from __future__ import annotations

from content_hub.application.jobs.job_service import JobEvent
from content_hub.application.jobs.job_service import JobRepository
from content_hub.application.jobs.job_service import JobRun


class JobEventService:
    def __init__(self, job_repository: JobRepository, event_repository=None):
        self.job_repository = job_repository
        self.event_repository = event_repository

    def record(self, job: JobRun, status: str, message: str, detail: str = "") -> JobEvent:
        event = JobEvent(job_id=job.job_id, status=status, message=message, detail=detail)
        job.events.append(event)
        self.job_repository.save(job)
        if self.event_repository is not None:
            self.event_repository.append(event)
        return event

    def list_events(self, job_id: str) -> list[JobEvent]:
        if self.event_repository is not None:
            return self.event_repository.list_by_job(job_id)
        job = self.job_repository.get(job_id)
        if job is None:
            return []
        return list(job.events)
