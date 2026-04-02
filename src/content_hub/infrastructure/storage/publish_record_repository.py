from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path


class FilePublishRecordRepository:
    def __init__(self, path: Path):
        self.path = path

    def append_record(
        self,
        article_title: str,
        platform: str,
        success: bool,
        account_info: dict,
        error: str | None,
    ) -> None:
        payload = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload.setdefault(article_title, []).append(
            {
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "success": success,
                "account_info": account_info,
                "error": error,
            }
        )
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_records(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))
