from __future__ import annotations

import json
from pathlib import Path

from content_hub.application.jobs.job_service import JobEvent


class FileJobEventRepository:
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file

    def append(self, event: JobEvent) -> JobEvent:
        payload = self._load_all()
        payload.append(
            {
                "job_id": event.job_id,
                "status": event.status,
                "message": event.message,
                "detail": event.detail,
            }
        )
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.storage_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return event

    def list_by_job(self, job_id: str) -> list[JobEvent]:
        return [
            JobEvent(
                job_id=item["job_id"],
                status=item["status"],
                message=item["message"],
                detail=item.get("detail", ""),
            )
            for item in self._load_all()
            if item.get("job_id") == job_id
        ]

    def _load_all(self) -> list[dict]:
        if not self.storage_file.exists():
            return []
        return json.loads(self.storage_file.read_text(encoding="utf-8"))
