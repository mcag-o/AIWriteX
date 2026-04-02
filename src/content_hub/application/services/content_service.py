from __future__ import annotations

from content_hub.domain.content.entities import ContentArtifact, ContentDocument
from content_hub.infrastructure.storage.article_repository import FileArticleRepository


class ContentService:
    def __init__(self, repository: FileArticleRepository):
        self.repository = repository

    def create_document(self, title: str, body: str, content_format: str = "markdown") -> ContentArtifact:
        document = ContentDocument(title=title, body=body, content_format=content_format)
        path = self.repository.save(document)
        return ContentArtifact(document=document, artifact_path=path)

    def list_documents(self) -> list[ContentDocument]:
        return self.repository.list_documents()

    def read_document(self, path) -> ContentDocument:
        return self.repository.read(path)

    def update_document(self, path, body: str) -> ContentDocument:
        return self.repository.update(path, body)

    def delete_document(self, path) -> None:
        self.repository.delete(path)
