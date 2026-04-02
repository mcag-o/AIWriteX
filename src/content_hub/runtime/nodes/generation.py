from __future__ import annotations

from content_hub.domain.content.entities import ContentDocument
from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class StaticGenerationNode(WorkflowNode):
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        topic = context.payload.get("topic", "无标题")
        context.document = ContentDocument(
            title=str(topic),
            body=f"# {topic}\n\n这是内容中站生成的基础内容。",
            content_format=context.settings.workflow.article_format,
            summary=str(topic),
            metadata={"generated_by": "StaticGenerationNode"},
        )
        return context
