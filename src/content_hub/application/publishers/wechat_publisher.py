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
        if not self.credentials:
            return PublishResult(
                success=False,
                platform=platform,
                message="未找到有效的微信公众号凭据",
                metadata={
                    "publisher": "wechat",
                    "channel": "wechat",
                    "credential_count": 0,
                    "success_count": 0,
                    "partial_success": False,
                    "error_code": "MISSING_CREDENTIALS",
                    "account_results": [],
                },
            )

        selected_credentials = self.credentials
        account_results = []
        for credential in selected_credentials:
            account_payload = account_info or {
                "mode": "wechat-placeholder",
                "channel": "wechat",
                "appid": credential.appid,
                "author": credential.author,
            }
            self.repository.append_record(
                article_title=document.title,
                platform=platform,
                success=True,
                account_info=account_payload,
                error=None,
            )
            account_results.append(
                {
                    "appid": credential.appid,
                    "author": credential.author,
                    "success": True,
                    "message": "wechat recorded",
                }
            )
        return PublishResult(
            success=True,
            platform=platform,
            message=f"wechat recorded for {len(account_results)} account(s)",
            metadata={
                "publisher": "wechat",
                "channel": "wechat",
                "mode": (account_info or {}).get("mode", "wechat-placeholder"),
                "appid": account_results[0]["appid"] if account_results else "",
                "author": account_results[0]["author"] if account_results else "",
                "credential_count": len(account_results),
                "success_count": len([item for item in account_results if item["success"]]),
                "partial_success": False,
                "error_code": None,
                "account_results": account_results,
            },
        )
