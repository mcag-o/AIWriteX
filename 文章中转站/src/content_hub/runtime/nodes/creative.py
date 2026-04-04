from __future__ import annotations

from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class CreativeEnhancementNode(WorkflowNode):
    def _get_intensity_description(self, intensity: float) -> str:
        if intensity < 0.8:
            return "保守"
        if intensity < 1.0:
            return "适中"
        if intensity < 1.2:
            return "激进"
        return "非常激进"

    def _calculate_compatibility(self, dimensions: list[dict]) -> float:
        categories = [item.get("category") for item in dimensions]
        incompatible_pairs = [
            ("style", "format"),
            ("time", "scene"),
            ("personality", "tone"),
            ("structure", "rhythm"),
        ]
        conflicts = 0
        for left, right in incompatible_pairs:
            if left in categories and right in categories:
                conflicts += 1
        return max(0.0, 1.0 - conflicts * 0.3)

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before creative enhancement")

        creative_style = context.payload.get("creative_style", "default")
        creative_intensity = float(context.payload.get("creative_intensity", 1.0))
        selected_dimensions = context.payload.get("creative_dimensions", [])
        compatibility_score = self._calculate_compatibility(selected_dimensions)
        context.document.body = (
            f"{context.document.body}\n\n## 创意增强\n\n"
            f"内容已完成创意变换，当前风格：{creative_style}。"
        )
        context.document.metadata["transformation_type"] = "dimensional_creative"
        context.document.metadata["creative_style"] = str(creative_style)
        context.document.metadata["creative_intensity"] = creative_intensity
        context.document.metadata["creative_intensity_description"] = self._get_intensity_description(
            creative_intensity
        )
        context.document.metadata["selected_dimensions"] = selected_dimensions
        context.document.metadata["compatibility_score"] = compatibility_score
        return context
