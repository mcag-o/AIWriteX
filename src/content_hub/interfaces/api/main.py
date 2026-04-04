from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from content_hub.bootstrap.container import build_container


class CreateContentRequest(BaseModel):
    title: str
    body: str
    content_format: str = "markdown"


class UpdateContentRequest(BaseModel):
    path: str
    body: str


class ExecuteWorkflowRequest(BaseModel):
    topic: str


class CreateJobRequest(BaseModel):
    topic: str


class CreateTemplateRequest(BaseModel):
    category: str
    name: str
    content: str


class RenameTemplateRequest(BaseModel):
    path: str
    new_name: str


class CopyTemplateRequest(BaseModel):
    path: str
    target_category: str
    new_name: str


class MoveTemplateRequest(BaseModel):
    path: str
    target_category: str


class UpdateConfigRequest(BaseModel):
    llm: dict | None = None
    workflow: dict | None = None
    rewrite: dict | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="Content Hub API", version="0.1.0")
    project_root = Path(__file__).resolve().parents[4]
    container = build_container(project_root)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/config")
    async def get_config() -> dict:
        return {
            "llm": {
                "provider": container.settings.llm.provider,
                "model": container.settings.llm.model,
            },
            "workflow": {
                "publish_platform": container.settings.workflow.publish_platform,
                "article_format": container.settings.workflow.article_format,
                "auto_publish": container.settings.workflow.auto_publish,
            },
            "rewrite": {"enabled": container.settings.rewrite.enabled},
        }

    @app.patch("/config")
    async def update_config(request: UpdateConfigRequest) -> dict:
        if request.llm:
            container.settings.llm.provider = request.llm.get(
                "provider", container.settings.llm.provider
            )
            container.settings.llm.model = request.llm.get("model", container.settings.llm.model)
        if request.workflow:
            container.settings.workflow.publish_platform = request.workflow.get(
                "publish_platform", container.settings.workflow.publish_platform
            )
            container.settings.workflow.article_format = request.workflow.get(
                "article_format", container.settings.workflow.article_format
            )
            container.settings.workflow.auto_publish = request.workflow.get(
                "auto_publish", container.settings.workflow.auto_publish
            )
        if request.rewrite:
            container.settings.rewrite.enabled = request.rewrite.get(
                "enabled", container.settings.rewrite.enabled
            )
        config_path = project_root / "文章中转站" / "config.generated.yaml"
        container.config_service.save_hub_settings(container.settings, config_path)
        return {"saved_to": str(config_path)}

    @app.get("/templates/categories")
    async def template_categories() -> dict:
        return {"data": container.template_service.list_categories()}

    @app.get("/templates")
    async def templates(category: str) -> dict:
        return {
            "data": [item.__dict__ for item in container.template_service.list_templates(category)]
        }

    @app.post("/templates")
    async def create_template(request: CreateTemplateRequest) -> dict:
        path = container.template_service.create_template(request.category, request.name, request.content)
        return {"path": str(path)}

    @app.put("/templates/rename")
    async def rename_template(request: RenameTemplateRequest) -> dict:
        path = container.template_service.rename_template(Path(request.path), request.new_name)
        return {"path": str(path)}

    @app.post("/templates/copy")
    async def copy_template(request: CopyTemplateRequest) -> dict:
        path = container.template_service.copy_template(
            Path(request.path),
            request.target_category,
            request.new_name,
        )
        return {"path": str(path)}

    @app.put("/templates/move")
    async def move_template(request: MoveTemplateRequest) -> dict:
        path = container.template_service.move_template(Path(request.path), request.target_category)
        return {"path": str(path)}

    @app.delete("/templates")
    async def delete_template(path: str) -> dict:
        container.template_service.delete_template(Path(path))
        return {"deleted": True}

    @app.get("/content")
    async def content_list() -> dict:
        return {
            "data": [
                {
                    "title": item["title"],
                    "content_format": item["content_format"],
                    "artifact_path": str(item["artifact_path"]),
                    "publish_count": item["publish_count"],
                    "published": item["published"],
                    "last_publish_platform": item["last_publish_platform"],
                    "last_published_at": item["last_published_at"],
                }
                for item in container.content_service.list_document_views()
            ]
        }

    @app.get("/content/detail")
    async def content_detail(path: str) -> dict:
        detail = container.content_service.get_document_detail(Path(path))
        document = detail["document"]
        return {
            "title": document.title,
            "body": document.body,
            "content_format": document.content_format,
            "artifact_path": str(detail["artifact_path"]),
            "publish_history": detail["publish_history"],
        }

    @app.post("/content")
    async def create_content(request: CreateContentRequest) -> dict:
        artifact = container.content_service.create_document(
            title=request.title,
            body=request.body,
            content_format=request.content_format,
        )
        return {
            "title": artifact.document.title,
            "artifact_path": str(artifact.artifact_path) if artifact.artifact_path else None,
        }

    @app.get("/content/read")
    async def read_content(path: str) -> dict:
        detail = container.content_service.get_document_detail(Path(path))
        document = detail["document"]
        return {
            "title": document.title,
            "body": document.body,
            "content_format": document.content_format,
            "artifact_path": str(detail["artifact_path"]),
            "publish_history": detail["publish_history"],
        }

    @app.put("/content")
    async def update_content(request: UpdateContentRequest) -> dict:
        document = container.content_service.update_document(Path(request.path), request.body)
        return {"title": document.title, "body": document.body}

    @app.delete("/content")
    async def delete_content(path: str) -> dict:
        container.content_service.delete_document(Path(path))
        return {"deleted": True}

    @app.get("/publish/records")
    async def publish_records(article_title: str | None = None) -> dict:
        if article_title:
            return {"data": container.publish_service.get_history(article_title)}
        return {"data": container.publish_service.list_records()}

    @app.get("/jobs")
    async def list_jobs() -> dict:
        return {
            "data": [
                {
                    "job_id": job.job_id,
                    "status": job.status,
                    "artifact_path": str(job.artifact_path) if job.artifact_path is not None else None,
                }
                for job in container.job_service.list_jobs()
            ]
        }

    @app.post("/jobs")
    async def create_job(request: CreateJobRequest) -> dict:
        job = container.job_service.run_workflow(
            workflow=container.workflow_service.build_default_workflow(container.settings),
            settings=container.settings,
            payload={"topic": request.topic},
        )
        return {"job_id": job.job_id, "status": job.status}

    @app.get("/jobs/{job_id}")
    async def get_job(job_id: str) -> dict:
        job = container.job_service.job_repository.get(job_id)
        if job is None:
            return {"job_id": job_id, "status": "missing"}
        return {
            "job_id": job.job_id,
            "status": job.status,
            "artifact_path": str(job.artifact_path) if job.artifact_path is not None else None,
        }

    @app.post("/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str) -> dict:
        try:
            job = container.job_service.cancel_job(job_id)
        except KeyError:
            return {"job_id": job_id, "status": "missing"}
        return {"job_id": job.job_id, "status": job.status}

    @app.get("/jobs/{job_id}/events")
    async def get_job_events(job_id: str) -> dict:
        job = container.job_service.job_repository.get(job_id)
        if job is None:
            return {"job_id": job_id, "events": []}
        return {
            "job_id": job.job_id,
            "events": [
                {
                    "status": event.status,
                    "message": event.message,
                    "detail": event.detail,
                }
                for event in job.events
            ],
        }

    @app.post("/workflows/execute")
    async def execute_workflow(request: ExecuteWorkflowRequest) -> dict:
        result = container.workflow_service.run_default_workflow(
            settings=container.settings,
            payload={"topic": request.topic},
        )
        return {
            "title": result.document.title if result.document else "",
            "artifact_path": str(result.artifact_path) if result.artifact_path else None,
            "publish_results": [item.message for item in result.publish_results],
        }

    return app


app = create_app()
