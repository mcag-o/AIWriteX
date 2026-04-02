from __future__ import annotations

from content_hub.domain.publish.models import PublishResult
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class RecordPublishNode(WorkflowNode):
    def __init__(self, repository: FilePublishRecordRepository, platform: str):
        self.repository = repository
        self.platform = platform

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before publish")
        self.repository.append_record(
            article_title=context.document.title,
            platform=self.platform,
            success=True,
            account_info={"mode": "record-only"},
            error=None,
        )
        context.publish_results.append(
            PublishResult(success=True, platform=self.platform, message="recorded")
        )
        return context
