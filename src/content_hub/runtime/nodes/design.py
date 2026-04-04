from __future__ import annotations

from content_hub.domain.content.entities import ContentDocument
from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class SimpleDesignNode(WorkflowNode):
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before design formatting")

        body = (
            "<html><body>"
            f"<h1>{context.document.title}</h1>"
            f"<article>{context.document.body}</article>"
            "</body></html>"
        )
        context.document = ContentDocument(
            title=context.document.title,
            body=body,
            content_format="html",
            summary=context.document.summary,
            metadata={**context.document.metadata, "design_mode": "simple_html"},
        )
        return context
