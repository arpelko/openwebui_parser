from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ParsedSections:
    yhteenveto: str = ""
    koodi: str = ""
    kb: str = ""


@dataclass
class ChatChunk:
    title: str
    safe_title: str
    chunk_index: int
    total_chunks: int
    content: str


@dataclass
class ProcessMetadata:
    source_file: str
    title: str
    safe_title: str
    chunk_index: int
    total_chunks: int
    model: str
    chunk_length_chars: int
    raw_response_path: Optional[str] = None