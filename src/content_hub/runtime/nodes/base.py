from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from content_hub.bootstrap.settings import HubSettings
from content_hub.domain.content.entities import ContentDocument
from content_hub.domain.publish.models import PublishResult


@dataclass
class WorkflowContext:
    settings: HubSettings
    payload: dict[str, Any] = field(default_factory=dict)
    document: ContentDocument | None = None
    artifact_path: Path | None = None
    publish_results: list[PublishResult] = field(default_factory=list)


class WorkflowNode:
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        raise NotImplementedError
