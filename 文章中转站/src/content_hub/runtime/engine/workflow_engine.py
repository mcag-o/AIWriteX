from __future__ import annotations

from content_hub.domain.workflow.models import WorkflowDefinition
from content_hub.runtime.nodes.base import WorkflowContext
from content_hub.runtime.nodes.registry import NodeRegistry


class WorkflowEngine:
    def __init__(self, registry: NodeRegistry):
        self.registry = registry

    def execute(self, workflow: WorkflowDefinition, context: WorkflowContext) -> WorkflowContext:
        for node_name in workflow.nodes:
            node = self.registry.get(node_name)
            context = node.execute(context)
        return context
