from __future__ import annotations

from pathlib import Path

from content_hub.bootstrap.container import build_container


def run_legacy_workflow(inputs: dict | None = None) -> dict:
    project_root = Path(__file__).resolve().parents[4]
    container = build_container(project_root)
    payload = inputs or {"topic": "AIWriteX 内容中站任务"}
    result = container.workflow_service.run_default_workflow(container.settings, payload)
    return {
        "success": True,
        "document": {
            "title": result.document.title if result.document else "",
            "body": result.document.body if result.document else "",
        },
        "artifact_path": str(result.artifact_path) if result.artifact_path else None,
        "publish_results": [item.message for item in result.publish_results],
    }
