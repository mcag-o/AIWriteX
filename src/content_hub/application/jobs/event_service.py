from __future__ import annotations

from content_hub.application.jobs.job_service import JobEvent
from content_hub.application.jobs.job_service import JobRepository
from content_hub.application.jobs.job_service import JobRun


class JobEventService:
    def __init__(self, job_repository: JobRepository):
        self.job_repository = job_repository

    def record(self, job: JobRun, status: str, message: str, detail: str = "") -> JobEvent:
        event = JobEvent(job_id=job.job_id, status=status, message=message, detail=detail)
        job.events.append(event)
        self.job_repository.save(job)
        return event

    def list_events(self, job_id: str) -> list[JobEvent]:
        job = self.job_repository.get(job_id)
        if job is None:
            return []
        return list(job.events)
