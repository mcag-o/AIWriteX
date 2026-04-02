from __future__ import annotations

from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class SuffixRewriteNode(WorkflowNode):
    def __init__(self, suffix: str):
        self.suffix = suffix

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is not None:
            context.document.body = f"{context.document.body}{self.suffix}"
        return context
