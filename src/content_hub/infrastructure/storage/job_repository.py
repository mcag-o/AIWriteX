from __future__ import annotations

import json
from pathlib import Path

from content_hub.application.jobs.job_service import JobEvent
from content_hub.application.jobs.job_service import JobRun


class FileJobRepository:
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file

    def save(self, job: JobRun) -> JobRun:
        payload = self._load_all()
        payload[job.job_id] = self._serialize_job(job)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.storage_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return job

    def get(self, job_id: str) -> JobRun | None:
        payload = self._load_all()
        raw = payload.get(job_id)
        if raw is None:
            return None
        return self._deserialize_job(raw)

    def _load_all(self) -> dict:
        if not self.storage_file.exists():
            return {}
        return json.loads(self.storage_file.read_text(encoding="utf-8"))

    def _serialize_job(self, job: JobRun) -> dict:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "error": job.error,
            "artifact_path": str(job.artifact_path) if job.artifact_path is not None else None,
            "events": [
                {
                    "job_id": event.job_id,
                    "status": event.status,
                    "message": event.message,
                    "detail": event.detail,
                }
                for event in job.events
            ],
        }

    def _deserialize_job(self, raw: dict) -> JobRun:
        artifact_path = raw.get("artifact_path")
        return JobRun(
            job_id=raw["job_id"],
            status=raw["status"],
            error=raw.get("error") or "",
            artifact_path=Path(artifact_path) if artifact_path else None,
            events=[
                JobEvent(
                    job_id=item["job_id"],
                    status=item["status"],
                    message=item["message"],
                    detail=item.get("detail", ""),
                )
                for item in raw.get("events", [])
            ],
        )
