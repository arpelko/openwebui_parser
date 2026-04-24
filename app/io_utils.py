import glob
import json
import os
import shutil
from datetime import datetime
from typing import Any, List


def ensure_directories(base_output_dir: str, input_dir: str, processed_dir: str, failed_dir: str) -> dict:
    output_dirs = {
        "yhteenveto": os.path.join(base_output_dir, "1_Yhteenvedot"),
        "koodi": os.path.join(base_output_dir, "2_Koodit"),
        "kb": os.path.join(base_output_dir, "3_Knowledge_Base"),
        "meta": os.path.join(base_output_dir, "4_Metadata"),
        "virheet": os.path.join(base_output_dir, "5_Virheet"),
        "raw": os.path.join(base_output_dir, "6_RawResponses"),
    }

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(failed_dir, exist_ok=True)

    for path in output_dirs.values():
        os.makedirs(path, exist_ok=True)

    return output_dirs


def list_json_files(input_dir: str) -> List[str]:
    return glob.glob(os.path.join(input_dir, "*.json"))


def load_json_file(filepath: str) -> Any:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def move_file_to_directory(filepath: str, target_dir: str) -> str:
    os.makedirs(target_dir, exist_ok=True)

    filename = os.path.basename(filepath)
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = os.path.join(target_dir, f"{base}_{timestamp}{ext}")

    shutil.move(filepath, target_path)
    return target_path