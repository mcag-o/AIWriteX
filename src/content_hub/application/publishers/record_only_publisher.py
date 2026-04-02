from __future__ import annotations

from content_hub.domain.content.entities import ContentDocument
from content_hub.domain.publish.models import PublishResult
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository


class RecordOnlyPublisher:
    def __init__(self, repository: FilePublishRecordRepository):
        self.repository = repository

    def publish(self, document: ContentDocument, platform: str, account_info: dict | None = None) -> PublishResult:
        payload = account_info or {"mode": "record-only"}
        self.repository.append_record(
            article_title=document.title,
            platform=platform,
            success=True,
            account_info=payload,
            error=None,
        )
        return PublishResult(
            success=True,
            platform=platform,
            message="recorded",
            metadata={"publisher": "record_only", "mode": payload.get("mode", "record-only")},
        )
