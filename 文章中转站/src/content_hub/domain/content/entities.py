from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ContentDocument:
    title: str
    body: str
    content_format: str = "markdown"
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentArtifact:
    document: ContentDocument
    artifact_path: Path | None = None
