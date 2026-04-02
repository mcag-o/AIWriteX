from __future__ import annotations

from content_hub.runtime.nodes.base import WorkflowNode


class NodeRegistry:
    def __init__(self):
        self._nodes: dict[str, WorkflowNode] = {}

    def register(self, name: str, node: WorkflowNode) -> None:
        self._nodes[name] = node

    def get(self, name: str) -> WorkflowNode:
        return self._nodes[name]
