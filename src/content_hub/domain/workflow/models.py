from dataclasses import dataclass, field


@dataclass
class WorkflowDefinition:
    name: str
    nodes: list[str] = field(default_factory=list)
