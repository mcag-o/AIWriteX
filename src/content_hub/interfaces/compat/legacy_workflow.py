from __future__ import annotations

from pathlib import Path
from typing import Any

from content_hub.bootstrap.container import build_container


class UnifiedContentWorkflow:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[4]
        self.container = build_container(self.project_root)
        self.platform_adapters: dict[str, dict[str, Any]] = {
            item["key"]: item for item in self.container.platform_service.list_platforms()
        }

    def execute(self, topic: str, **kwargs) -> dict[str, Any]:
        payload = {"topic": topic, **kwargs}
        result = self.container.workflow_service.run_default_workflow(self.container.settings, payload)
        return {
            "base_content": result.document.body if result.document else "",
            "final_content": result.document.body if result.document else "",
            "formatted_content": result.document.body if result.document else "",
            "save_result": {
                "success": result.artifact_path is not None,
                "path": str(result.artifact_path) if result.artifact_path else None,
            },
            "publish_result": {
                "success": all(item.success for item in result.publish_results) if result.publish_results else False,
                "message": ", ".join(item.message for item in result.publish_results) if result.publish_results else "",
            }
            if result.publish_results
            else None,
            "success": True,
        }

    def register_platform_adapter(self, name: str, adapter: Any) -> None:
        self.platform_adapters[name] = {"key": name, "adapter": adapter}
