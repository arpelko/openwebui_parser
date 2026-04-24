from typing import Any, Dict, List
from app.models import Message
from app.utils import normalize_content, is_probable_base64_junk


def extract_messages(item: Dict[str, Any]) -> List[Message]:
    candidates = []

    if isinstance(item.get("messages"), list):
        candidates = item["messages"]
    elif isinstance(item.get("chat"), dict) and isinstance(item["chat"].get("messages"), list):
        candidates = item["chat"]["messages"]

    result: List[Message] = []

    for msg in candidates:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue

        content = normalize_content(msg.get("content"))
        if not content:
            continue

        if is_probable_base64_junk(content):
            continue

        result.append(Message(role=role, content=content))

    return result