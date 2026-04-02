from dataclasses import dataclass


@dataclass
class TemplateAsset:
    category: str
    name: str
    path: str
