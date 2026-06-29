from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class RetryQueue:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def enqueue(self, operation: str, payload: dict[str, Any], error: str) -> None:
        items = self.items()
        items.append(
            {
                "operation": operation,
                "payload": payload,
                "error": error,
                "attempts": 0,
                "created_at": time.time(),
            }
        )
        self.path.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")

    def items(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return list(payload)

    def clear(self) -> None:
        self.path.write_text("[]\n", encoding="utf-8")
