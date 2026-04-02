from __future__ import annotations

import json

from content_hub.application.publishers.base import Publisher
from content_hub.domain.content.entities import ContentDocument
from content_hub.domain.publish.models import PublishResult
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository


class PublishService:
    def __init__(self, repository: FilePublishRecordRepository, publishers: dict[str, Publisher] | None = None):
        self.repository = repository
        self.publishers = publishers or {}

    def publish_document(self, document: ContentDocument, platform: str, account_info: dict | None = None) -> PublishResult:
        publisher = self.publishers.get(platform)
        if publisher is None:
            return PublishResult(
                success=False,
                platform=platform,
                message=f"unsupported platform: {platform}",
                metadata={"error_code": "UNSUPPORTED_PLATFORM", "publisher": "missing"},
            )
        return publisher.publish(document, platform=platform, account_info=account_info)

    def record_success(self, article_title: str, platform: str, account_info: dict) -> PublishResult:
        self.repository.append_record(
            article_title=article_title,
            platform=platform,
            success=True,
            account_info=account_info,
            error=None,
        )
        return PublishResult(success=True, platform=platform, message="recorded")

    def list_records(self) -> dict:
        return self.repository.list_records()

    def get_history(self, article_title: str) -> list:
        return self.list_records().get(article_title, [])
