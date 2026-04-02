from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Protocol
from uuid import uuid4

from content_hub.bootstrap.settings import HubSettings
from content_hub.domain.workflow.models import WorkflowDefinition
from content_hub.runtime.engine.workflow_engine import WorkflowEngine
from content_hub.runtime.nodes.base import WorkflowContext


@dataclass
class JobRun:
    job_id: str
    status: str
    result: WorkflowContext | None = None
    error: str | None = None
    artifact_path: Path | None = None
    events: list["JobEvent"] = field(default_factory=list)


@dataclass
class JobEvent:
    job_id: str
    status: str
    message: str
    detail: str = ""


class InMemoryJobRepository:
    def __init__(self):
        self._jobs: Dict[str, JobRun] = {}

    def save(self, job: JobRun) -> JobRun:
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobRun | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[JobRun]:
        return [self._jobs[key] for key in sorted(self._jobs)]


class JobRepository(Protocol):
    def save(self, job: JobRun) -> JobRun: ...

    def get(self, job_id: str) -> JobRun | None: ...

    def list_jobs(self) -> list[JobRun]: ...


class JobService:
    def __init__(self, engine: WorkflowEngine, job_repository: JobRepository, event_service=None):
        self.engine = engine
        self.job_repository = job_repository
        self.event_service = event_service

    def create_job_run(self) -> JobRun:
        job = JobRun(job_id=str(uuid4()), status="running")
        self._record_event(job, status="running", message="workflow started")
        return job

    def run_workflow(
        self,
        workflow: WorkflowDefinition,
        settings: HubSettings,
        payload: dict,
    ) -> JobRun:
        job = self.create_job_run()
        self.job_repository.save(job)
        try:
            context = WorkflowContext(settings=settings, payload=payload)
            result = self.engine.execute(workflow, context)
            job.status = "completed"
            job.result = result
            job.artifact_path = result.artifact_path
            self._record_event(job, status="completed", message="workflow completed")
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            detail = exc.args[0] if len(exc.args) == 1 and isinstance(exc.args[0], str) else str(exc)
            self._record_event(job, status="failed", message="workflow failed", detail=detail)
        return self.job_repository.save(job)

    def cancel_job(self, job_id: str) -> JobRun:
        job = self.job_repository.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.status = "cancelled"
        self._record_event(job, status="cancelled", message="workflow cancelled")
        return self.job_repository.save(job)

    def list_jobs(self) -> list[JobRun]:
        return self.job_repository.list_jobs()

    def _record_event(self, job: JobRun, status: str, message: str, detail: str = "") -> None:
        if self.event_service is not None:
            self.event_service.record(job, status=status, message=message, detail=detail)
            return
        job.events.append(JobEvent(job_id=job.job_id, status=status, message=message, detail=detail))
