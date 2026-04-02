from __future__ import annotations

from content_hub.application.services.publish_service import PublishService
from content_hub.domain.publish.models import PublishResult
from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class RecordPublishNode(WorkflowNode):
    def __init__(self, publish_service: PublishService, platform: str):
        self.publish_service = publish_service
        self.platform = platform

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before publish")
        context.publish_results.append(
            self.publish_service.publish_document(
                context.document,
                platform=self.platform,
                account_info={"mode": "record-only"},
            )
        )
        return context
