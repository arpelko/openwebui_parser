import logging
import os
from typing import Any

from app.chunker import build_chat_text, chunk_messages
from app.config import load_settings
from app.consolidator import Consolidator
from app.extractor import extract_messages
from app.io_utils import (
    ensure_directories,
    list_json_files,
    load_json_file,
    move_file_to_directory,
)
from app.llm_client import LLMClient
from app.logging_setup import setup_logging
from app.models import ProcessMetadata
from app.parser import parse_sections
from app.utils import clean_filename
from app.writer import ResultWriter


logger = logging.getLogger(__name__)


def _get_title(item: dict, fallback_index: int) -> str:
    return (
        item.get("title")
        or item.get("chat", {}).get("title")
        or f"Nimetön_Keskustelu_{fallback_index}"
    )


def _get_conversation_id(item: dict) -> str | None:
    return (
        item.get("id")
        or item.get("chat_id")
        or item.get("conversation_id")
        or item.get("chat", {}).get("id")
    )


def process_file(
    filepath: str,
    settings: Any,
    llm_client_stage1: LLMClient,
    writer: ResultWriter,
) -> bool:
    """
    Käsittelee yhden input JSON -tiedoston.

    Palauttaa:
    - True: tiedosto käsiteltiin ilman kriittisiä virheitä
    - False: tiedostossa oli virheitä tai LLM-kutsuja epäonnistui
    """
    logger.info("Käsitellään tiedosto: %s", os.path.basename(filepath))
    had_errors = False

    try:
        data = load_json_file(filepath)
    except Exception as e:
        logger.exception("Virhe luettaessa tiedostoa %s", filepath)
        writer.write_error(
            f"{clean_filename(os.path.basename(filepath))}_read_error.txt",
            str(e),
        )
        return False

    if not isinstance(data, list):
        data = [data]

    for idx_item, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            had_errors = True
            logger.warning(
                "Ohitetaan item %s tiedostossa %s, koska se ei ole dict",
                idx_item,
                os.path.basename(filepath),
            )
            continue

        title = _get_title(item, idx_item)
        safe_title = clean_filename(title)
        conversation_id = _get_conversation_id(item)

        messages = extract_messages(item)
        if not messages:
            logger.info("[%s] Ei käsiteltäviä viestejä", safe_title)
            continue

        chat_text = build_chat_text(messages)
        chunks = chunk_messages(messages, settings.chunk_size_chars)

        logger.info(
            "[%s] Pituus: %s merkkiä -> %s osaa",
            safe_title,
            len(chat_text),
            len(chunks),
        )

        for chunk_idx, chunk in enumerate(chunks, start=1):
            chunk_suffix = f"_Osa{chunk_idx}" if len(chunks) > 1 else ""

            raw_response = llm_client_stage1.call_stage1(
                text_chunk=chunk,
                title=title,
                chunk_idx=chunk_idx,
                total_chunks=len(chunks),
            )

            if not raw_response:
                had_errors = True
                writer.write_error(
                    f"{safe_title}{chunk_suffix}_llm_error.txt",
                    "LLM ei palauttanut sisältöä.",
                )
                continue

            raw_path = writer.write_raw_response(
                safe_title=safe_title,
                chunk_suffix=chunk_suffix,
                content=raw_response,
            )

            sections = parse_sections(raw_response)
            writer.write_sections(
                safe_title=safe_title,
                chunk_suffix=chunk_suffix,
                sections=sections,
            )

            metadata = ProcessMetadata(
                source_file=os.path.basename(filepath),
                title=title,
                safe_title=safe_title,
                chunk_index=chunk_idx,
                total_chunks=len(chunks),
                model=llm_client_stage1.model,
                chunk_length_chars=len(chunk),
                raw_response_path=raw_path,
                conversation_id=conversation_id,
                stage="stage1",
            )
            writer.write_metadata(safe_title, chunk_suffix, metadata)

    return not had_errors


def run() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    output_dirs = ensure_directories(
        settings.output_dir,
        settings.input_dir,
        settings.processed_dir,
        settings.failed_dir,
    )

    writer = ResultWriter(output_dirs)

    llm_client_stage1 = LLMClient(
        api_key=settings.litellm_api_key,
        api_base=settings.litellm_api_base,
        model=settings.llm_model_stage1,
        temperature=settings.llm_temperature_stage1,
        max_output_tokens=settings.llm_max_output_tokens_stage1,
    )

    llm_client_stage2 = LLMClient(
        api_key=settings.litellm_api_key,
        api_base=settings.litellm_api_base,
        model=settings.llm_model_stage2,
        temperature=settings.llm_temperature_stage2,
        max_output_tokens=settings.llm_max_output_tokens_stage2,
    )

    json_files = list_json_files(settings.input_dir)
    if not json_files:
        logger.warning("Ei .json tiedostoja kansiossa %s", settings.input_dir)
    else:
        logger.info("Aloitetaan Open WebUI viennin käsittely...")

        for filepath in json_files:
            success = process_file(
                filepath=filepath,
                settings=settings,
                llm_client_stage1=llm_client_stage1,
                writer=writer,
            )

            try:
                if success:
                    moved_to = move_file_to_directory(filepath, settings.processed_dir)
                    logger.info("Tiedosto siirretty processed-kansioon: %s", moved_to)
                else:
                    moved_to = move_file_to_directory(filepath, settings.failed_dir)
                    logger.warning("Tiedosto siirretty failed-kansioon: %s", moved_to)
            except Exception:
                logger.exception("Tiedoston siirto epäonnistui: %s", filepath)

    consolidator = Consolidator(
        llm_client_stage2=llm_client_stage2,
        output_dirs=output_dirs,
    )
    consolidator.run()

    logger.info("Kaikki tiedostot on käsitelty.")