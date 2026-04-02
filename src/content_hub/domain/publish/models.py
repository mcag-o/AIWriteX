from dataclasses import dataclass, field
from typing import Any


@dataclass
class PublishResult:
    success: bool
    platform: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
