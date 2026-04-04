from __future__ import annotations

from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class CreativeEnhancementNode(WorkflowNode):
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before creative enhancement")

        creative_style = context.payload.get("creative_style", "default")
        context.document.body = (
            f"{context.document.body}\n\n## 创意增强\n\n"
            f"内容已完成创意变换，当前风格：{creative_style}。"
        )
        context.document.metadata["transformation_type"] = "dimensional_creative"
        context.document.metadata["creative_style"] = str(creative_style)
        return context
