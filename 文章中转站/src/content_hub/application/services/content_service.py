from __future__ import annotations

from pathlib import Path

from content_hub.application.services.publish_service import PublishService
from content_hub.domain.content.entities import ContentArtifact, ContentDocument
from content_hub.infrastructure.storage.article_repository import FileArticleRepository


class ContentService:
    def __init__(self, repository: FileArticleRepository, publish_service: PublishService | None = None):
        self.repository = repository
        self.publish_service = publish_service

    def create_document(self, title: str, body: str, content_format: str = "markdown") -> ContentArtifact:
        document = ContentDocument(title=title, body=body, content_format=content_format)
        path = self.repository.save(document)
        return ContentArtifact(document=document, artifact_path=path)

    def list_documents(self) -> list[ContentDocument]:
        return self.repository.list_documents()

    def list_document_views(
        self,
        title_query: str | None = None,
        published: bool | None = None,
    ) -> list[dict]:
        views = []
        for path in sorted(self.repository.root_dir.glob("*")):
            if path.suffix.lower() not in {".md", ".html", ".txt"}:
                continue
            document = self.repository.read(path)
            publish_history = []
            if self.publish_service is not None:
                publish_history = self.publish_service.get_history(document.title)
            last_record = publish_history[-1] if publish_history else None
            view = {
                "title": document.title,
                "content_format": document.content_format,
                "artifact_path": path,
                "publish_count": len(publish_history),
                "published": bool(publish_history),
                "last_publish_platform": last_record.get("platform") if last_record else None,
                "last_published_at": last_record.get("timestamp") if last_record else None,
            }
            if title_query is not None and title_query.lower() not in document.title.lower():
                continue
            if published is not None and view["published"] is not published:
                continue
            views.append(view)
        return views

    def read_document(self, path) -> ContentDocument:
        return self.repository.read(path)

    def get_document_detail(self, path: Path) -> dict:
        document = self.repository.read(path)
        history = []
        if self.publish_service is not None:
            history = self.publish_service.get_history(document.title)
        return {
            "document": document,
            "artifact_path": path,
            "publish_history": history,
        }

    def update_document(self, path, body: str) -> ContentDocument:
        return self.repository.update(path, body)

    def delete_document(self, path) -> None:
        self.repository.delete(path)
