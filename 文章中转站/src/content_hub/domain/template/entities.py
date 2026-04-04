from dataclasses import dataclass, field


@dataclass
class TemplateAsset:
    category: str
    name: str
    path: str
    metadata: dict = field(default_factory=dict)
