#!/usr/bin/env python

from pathlib import Path

from content_hub.bootstrap.container import build_container


def run(inputs):
    project_root = Path(__file__).resolve().parents[2]
    container = build_container(project_root)
    result = container.workflow_service.run_default_workflow(container.settings, inputs)
    return {
        "success": True,
        "document": {
            "title": result.document.title if result.document else "",
            "body": result.document.body if result.document else "",
        },
        "artifact_path": str(result.artifact_path) if result.artifact_path else None,
        "publish_results": [item.message for item in result.publish_results],
    }


def ai_write_x_run(config_data=None):
    inputs = config_data or {"topic": "AIWriteX 内容中站任务"}
    return True, run(inputs)


def ai_write_x_main(config_data=None):
    return ai_write_x_run(config_data=config_data)


if __name__ == "__main__":
    ai_write_x_main()
