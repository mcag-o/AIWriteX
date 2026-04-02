from __future__ import annotations

import json

from content_hub.domain.publish.models import PublishResult
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository


class PublishService:
    def __init__(self, repository: FilePublishRecordRepository):
        self.repository = repository

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
