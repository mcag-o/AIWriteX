from __future__ import annotations

from typing import Protocol

from content_hub.domain.content.entities import ContentDocument
from content_hub.domain.publish.models import PublishResult


class Publisher(Protocol):
    def publish(self, document: ContentDocument, platform: str, account_info: dict | None = None) -> PublishResult: ...
