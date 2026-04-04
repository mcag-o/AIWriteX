from __future__ import annotations

from content_hub.infrastructure.storage.ingestion_repository import FileHotTopicIngestionRepository
from content_hub.infrastructure.storage.ingestion_repository import FileRawContentIngestionRepository
from content_hub.infrastructure.storage.ingestion_repository import FileReferenceIngestionRepository


class IngestionService:
    def __init__(
        self,
        reference_repository: FileReferenceIngestionRepository,
        raw_content_repository: FileRawContentIngestionRepository | None = None,
        hot_topic_repository: FileHotTopicIngestionRepository | None = None,
    ):
        self.reference_repository = reference_repository
        self.raw_content_repository = raw_content_repository
        self.hot_topic_repository = hot_topic_repository

    def submit_reference_urls(self, urls: list[str]) -> dict:
        self.reference_repository.add_urls(urls)
        return {"submitted": len(urls), "items": self.reference_repository.list_urls()[-len(urls):]}

    def submit_raw_content(self, items: list[dict]) -> dict:
        if self.raw_content_repository is None:
            raise ValueError("raw content repository is not configured")
        self.raw_content_repository.add_items(items)
        return {"submitted": len(items), "items": self.raw_content_repository.list_items()[-len(items):]}

    def submit_hot_topics(self, items: list[dict]) -> dict:
        if self.hot_topic_repository is None:
            raise ValueError("hot topic repository is not configured")
        self.hot_topic_repository.add_items(items)
        return {"submitted": len(items), "items": self.hot_topic_repository.list_items()[-len(items):]}

    def list_records(self) -> dict:
        return {
            "reference_urls": self.reference_repository.list_urls(),
            "raw_content": self.raw_content_repository.list_items() if self.raw_content_repository is not None else [],
            "hot_topics": self.hot_topic_repository.list_items() if self.hot_topic_repository is not None else [],
        }
