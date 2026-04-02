from __future__ import annotations

from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class PersistNode(WorkflowNode):
    def __init__(self, repository: FileArticleRepository):
        self.repository = repository

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before persist")
        context.artifact_path = self.repository.save(context.document)
        return context
