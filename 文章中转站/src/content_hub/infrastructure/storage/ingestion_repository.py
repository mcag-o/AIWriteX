from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class FileReferenceIngestionRepository:
    def __init__(self, path: Path):
        self.path = path

    def add_urls(self, urls: list[str]) -> None:
        payload = self.list_urls()
        payload.extend(
            [
                {
                    "source_type": "reference_url",
                    "status": "received",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {"url": url},
                }
                for url in urls
            ]
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_urls(self) -> list[str]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))


class FileRawContentIngestionRepository:
    def __init__(self, path: Path):
        self.path = path

    def add_items(self, items: list[dict]) -> None:
        payload = self.list_items()
        payload.extend(
            [
                {
                    "source_type": "raw_content",
                    "status": "received",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "payload": item,
                }
                for item in items
            ]
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_items(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))


class FileHotTopicIngestionRepository:
    def __init__(self, path: Path):
        self.path = path

    def add_items(self, items: list[dict]) -> None:
        payload = self.list_items()
        payload.extend(
            [
                {
                    "source_type": "hot_topic",
                    "status": "received",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "payload": item,
                }
                for item in items
            ]
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_items(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))
