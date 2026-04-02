from __future__ import annotations

from content_hub.bootstrap.settings import WeChatCredential
from content_hub.domain.content.entities import ContentDocument
from content_hub.domain.publish.models import PublishResult
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository


class WeChatPublisher:
    def __init__(self, repository: FilePublishRecordRepository, credentials: list[WeChatCredential]):
        self.repository = repository
        self.credentials = credentials

    def publish(self, document: ContentDocument, platform: str, account_info: dict | None = None) -> PublishResult:
        selected = self.credentials[0] if self.credentials else None
        account_payload = account_info or {
            "mode": "wechat-placeholder",
            "channel": "wechat",
            "appid": selected.appid if selected else "",
            "author": selected.author if selected else "",
        }
        self.repository.append_record(
            article_title=document.title,
            platform=platform,
            success=True,
            account_info=account_payload,
            error=None,
        )
        return PublishResult(
            success=True,
            platform=platform,
            message="wechat recorded",
            metadata={
                "publisher": "wechat",
                "channel": "wechat",
                "mode": account_payload.get("mode", "wechat-placeholder"),
                "appid": account_payload.get("appid", ""),
                "author": account_payload.get("author", ""),
            },
        )
