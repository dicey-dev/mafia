import json
from pathlib import Path


def load_personalities(path: str) -> list[dict[str, str]]:
    data = json.loads(Path(path).read_text())
    return data["personalities"]
