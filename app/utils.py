import re
from typing import Any


def clean_filename(title: str) -> str:
    title = title or "Nimetön_Keskustelu"
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title).strip().replace(" ", "_")
    return cleaned[:180] if cleaned else "Nimetön_Keskustelu"


def is_probable_base64_junk(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False

    if "data:image/" in text and ";base64," in text:
        return True

    if re.search(r"[A-Za-z0-9+/=]{1200,}", text):
        return True

    return False


def normalize_content(content: Any) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(part for part in parts if part).strip()

    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"].strip()
        if isinstance(content.get("content"), str):
            return content["content"].strip()

    return str(content).strip()