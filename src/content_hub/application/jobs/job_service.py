from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
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


class InMemoryJobRepository:
    def __init__(self):
        self._jobs: Dict[str, JobRun] = {}

    def save(self, job: JobRun) -> JobRun:
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobRun | None:
        return self._jobs.get(job_id)


class JobService:
    def __init__(self, engine: WorkflowEngine, job_repository: InMemoryJobRepository):
        self.engine = engine
        self.job_repository = job_repository

    def run_workflow(
        self,
        workflow: WorkflowDefinition,
        settings: HubSettings,
        payload: dict,
    ) -> JobRun:
        job = JobRun(job_id=str(uuid4()), status="running")
        self.job_repository.save(job)
        try:
            context = WorkflowContext(settings=settings, payload=payload)
            result = self.engine.execute(workflow, context)
            job.status = "completed"
            job.result = result
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
        return self.job_repository.save(job)
