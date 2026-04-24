from typing import List
from app.models import Message


def build_chat_text(messages: List[Message]) -> str:
    parts = []
    for msg in messages:
        role_fi = "Kysymys" if msg.role == "user" else "Vastaus"
        parts.append(f"**{role_fi}:**\n{msg.content}\n")
    return "\n".join(parts).strip()


def chunk_messages(messages: List[Message], chunk_size: int) -> List[str]:
    chunks: List[str] = []
    current_parts: List[str] = []
    current_length = 0

    for msg in messages:
        role_fi = "Kysymys" if msg.role == "user" else "Vastaus"
        part = f"**{role_fi}:**\n{msg.content}\n\n"

        if current_parts and current_length + len(part) > chunk_size:
            chunks.append("".join(current_parts).strip())
            current_parts = [part]
            current_length = len(part)
        else:
            current_parts.append(part)
            current_length += len(part)

    if current_parts:
        chunks.append("".join(current_parts).strip())

    return chunksfrom typing import List
from app.models import Message


def build_chat_text(messages: List[Message]) -> str:
    parts = []
    for msg in messages:
        role_fi = "Kysymys" if msg.role == "user" else "Vastaus"
        parts.append(f"**{role_fi}:**\n{msg.content}\n")
    return "\n".join(parts).strip()


def chunk_messages(messages: List[Message], chunk_size: int) -> List[str]:
    chunks: List[str] = []
    current_parts: List[str] = []
    current_length = 0

    for msg in messages:
        role_fi = "Kysymys" if msg.role == "user" else "Vastaus"
        part = f"**{role_fi}:**\n{msg.content}\n\n"

        if current_parts and current_length + len(part) > chunk_size:
            chunks.append("".join(current_parts).strip())
            current_parts = [part]
            current_length = len(part)
        else:
            current_parts.append(part)
            current_length += len(part)

    if current_parts:
        chunks.append("".join(current_parts).strip())

    return chunks