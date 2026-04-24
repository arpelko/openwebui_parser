import glob
import json
import logging
import os
from collections import defaultdict
from typing import Dict, List, Tuple

from app.io_utils import read_text, write_text, write_json


logger = logging.getLogger(__name__)


class Consolidator:
    def __init__(self, llm_client_stage2, output_dirs: dict):
        self.llm_client_stage2 = llm_client_stage2
        self.output_dirs = output_dirs

    def run(self) -> None:
        logger.info("Aloitetaan metadataan perustuva final-konsolidointi...")

        groups = self._load_metadata_groups()
        if not groups:
            logger.info("Ei metadataan perustuvia konsolidoitavia ryhmiä.")
            return

        self._consolidate_groups(groups, section_type="yhteenveto", target_dir=self.output_dirs["final_yhteenveto"])
        self._consolidate_groups(groups, section_type="koodi", target_dir=self.output_dirs["final_koodi"])
        self._consolidate_groups(groups, section_type="kb", target_dir=self.output_dirs["final_kb"])

        logger.info("Metadataan perustuva final-konsolidointi valmis.")

    def _load_metadata_groups(self) -> Dict[str, dict]:
        metadata_files = glob.glob(os.path.join(self.output_dirs["meta"], "*.json"))
        by_group = defaultdict(list)

        for path in metadata_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                if meta.get("type") == "final_consolidation":
                    continue

                group_key = self._build_group_key(meta)
                by_group[group_key].append(meta)

            except Exception:
                logger.exception("Metadatan luku epäonnistui: %s", path)

        grouped: Dict[str, dict] = {}
        for group_key, metas in by_group.items():
            metas_sorted = sorted(metas, key=lambda x: x.get("chunk_index", 0))
            first = metas_sorted[0]

            grouped[group_key] = {
                "group_key": group_key,
                "source_file": first.get("source_file"),
                "title": first.get("title"),
                "safe_title": first.get("safe_title"),
                "conversation_id": first.get("conversation_id"),
                "total_chunks": max((m.get("total_chunks", 0) for m in metas_sorted), default=len(metas_sorted)),
                "chunks": metas_sorted,
            }

        return grouped

    def _build_group_key(self, meta: dict) -> str:
        conversation_id = meta.get("conversation_id")
        if conversation_id:
            return f"conversation_id::{conversation_id}"

        source_file = meta.get("source_file", "unknown_source")
        safe_title = meta.get("safe_title", "unknown_title")
        return f"{source_file}::{safe_title}"

    def _consolidate_groups(self, groups: Dict[str, dict], section_type: str, target_dir: str) -> None:
        for group_key, group in groups.items():
            try:
                parts = self._collect_section_parts(group, section_type)
                if not parts:
                    logger.info("Ei osia konsolidoitavaksi: %s / %s", group["safe_title"], section_type)
                    continue

                logger.info(
                    "Konsolidoidaan %s: %s (%s osaa, group=%s)",
                    section_type,
                    group["safe_title"],
                    len(parts),
                    group_key,
                )

                if len(parts) == 1:
                    final_content = parts[0][1]
                else:
                    final_content = self.llm_client_stage2.call_stage2_consolidation(
                        base_title=group["title"] or group["safe_title"],
                        section_type=section_type,
                        parts=[content for _, content in parts],
                    )

                    if not final_content:
                        logger.warning(
                            "Stage2-konsolidointi epäonnistui, käytetään fallbackia: %s / %s",
                            group["safe_title"],
                            section_type,
                        )
                        final_content = self._fallback_merge(section_type, [content for _, content in parts])

                output_filename = f"{group['safe_title']}_FINAL_{self._type_suffix(section_type)}.md"
                output_path = os.path.join(target_dir, output_filename)
                write_text(output_path, final_content)

                self._write_final_metadata(group, section_type, output_path, parts)

            except Exception:
                logger.exception(
                    "Ryhmäkohtainen konsolidointi epäonnistui: %s / %s",
                    group_key,
                    section_type,
                )

    def _collect_section_parts(self, group: dict, section_type: str) -> List[Tuple[int, str]]:
        parts: List[Tuple[int, str]] = []
        suffix = self._type_suffix(section_type)

        for meta in sorted(group["chunks"], key=lambda x: x.get("chunk_index", 0)):
            safe_title = meta.get("safe_title", "unknown_title")
            chunk_index = meta.get("chunk_index", 0)
            total_chunks = meta.get("total_chunks", 1)

            chunk_suffix = f"_Osa{chunk_index}" if total_chunks > 1 else ""
            filename = f"{safe_title}{chunk_suffix}_{suffix}.md"

            source_dir = self._source_dir_for_type(section_type)
            path = os.path.join(source_dir, filename)

            if not os.path.exists(path):
                logger.warning("Osatiedostoa ei löytynyt: %s", path)
                continue

            content = read_text(path).strip()
            if not content:
                continue

            parts.append((chunk_index, content))

        return parts

    def _fallback_merge(self, section_type: str, parts: List[str]) -> str:
        header_map = {
            "yhteenveto": "# Lopullinen yhteenveto",
            "koodi": "# Lopullinen koodikooste",
            "kb": "# Lopullinen Knowledge Base -artikkeli",
        }
        header = header_map.get(section_type, "# Lopullinen sisältö")
        return header + "\n\n" + "\n\n---\n\n".join(parts)

    def _write_final_metadata(self, group: dict, section_type: str, output_path: str, parts: List[Tuple[int, str]]) -> None:
        final_meta = {
            "type": "final_consolidation",
            "section_type": section_type,
            "source_file": group.get("source_file"),
            "title": group.get("title"),
            "safe_title": group.get("safe_title"),
            "conversation_id": group.get("conversation_id"),
            "group_key": group.get("group_key"),
            "input_chunk_count": len(parts),
            "expected_total_chunks": group.get("total_chunks"),
            "model": self.llm_client_stage2.model,
            "stage": "stage2",
            "output_path": output_path,
            "input_chunks": [
                {"chunk_index": chunk_index, "chars": len(content)}
                for chunk_index, content in parts
            ],
        }

        meta_filename = f"{group['safe_title']}_FINAL_{section_type}_meta.json"
        meta_path = os.path.join(self.output_dirs["meta"], meta_filename)
        write_json(meta_path, final_meta)

    def _source_dir_for_type(self, section_type: str) -> str:
        mapping = {
            "yhteenveto": self.output_dirs["yhteenveto"],
            "koodi": self.output_dirs["koodi"],
            "kb": self.output_dirs["kb"],
        }
        return mapping[section_type]

    def _type_suffix(self, section_type: str) -> str:
        mapping = {
            "yhteenveto": "Yhteenveto",
            "koodi": "Koodit",
            "kb": "KB",
        }
        return mapping[section_type]