import os
from app.io_utils import write_json, write_text
from app.models import ParsedSections, ProcessMetadata


class ResultWriter:
    def __init__(self, output_dirs: dict):
        self.output_dirs = output_dirs

    def write_error(self, filename: str, content: str) -> None:
        path = os.path.join(self.output_dirs["virheet"], filename)
        write_text(path, content)

    def write_raw_response(self, safe_title: str, chunk_suffix: str, content: str) -> str:
        path = os.path.join(self.output_dirs["raw"], f"{safe_title}{chunk_suffix}_raw.md")
        write_text(path, content)
        return path

    def write_sections(
        self,
        safe_title: str,
        chunk_suffix: str,
        sections: ParsedSections,
    ) -> None:
        if sections.yhteenveto:
            write_text(
                os.path.join(self.output_dirs["yhteenveto"], f"{safe_title}{chunk_suffix}_Yhteenveto.md"),
                f"# Yhteenveto: {safe_title}\n\n{sections.yhteenveto}",
            )

        if sections.koodi and "Ei koodia" not in sections.koodi and len(sections.koodi) > 20:
            write_text(
                os.path.join(self.output_dirs["koodi"], f"{safe_title}{chunk_suffix}_Koodit.md"),
                f"# Koodit: {safe_title}\n\n{sections.koodi}",
            )

        if sections.kb and "Ei KB-materiaalia" not in sections.kb and len(sections.kb) > 20:
            write_text(
                os.path.join(self.output_dirs["kb"], f"{safe_title}{chunk_suffix}_KB.md"),
                f"# KB: {safe_title}\n\n{sections.kb}",
            )

    def write_metadata(self, safe_title: str, chunk_suffix: str, metadata: ProcessMetadata) -> None:
        path = os.path.join(self.output_dirs["meta"], f"{safe_title}{chunk_suffix}_meta.json")
        write_json(path, metadata.__dict__)