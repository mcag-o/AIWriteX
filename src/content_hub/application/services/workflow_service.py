from __future__ import annotations

from content_hub.bootstrap.settings import HubSettings
from content_hub.domain.workflow.models import WorkflowDefinition
from content_hub.runtime.engine.workflow_engine import WorkflowEngine
from content_hub.runtime.nodes.base import WorkflowContext
from content_hub.runtime.nodes.registry import NodeRegistry


class WorkflowService:
    def __init__(self, registry: NodeRegistry):
        self.engine = WorkflowEngine(registry)

    def build_default_workflow(self, settings: HubSettings) -> WorkflowDefinition:
        nodes = ["generate"]
        if settings.workflow.article_format.lower() == "html":
            nodes.append("design")
        if settings.rewrite.enabled:
            nodes.append("creative")
        nodes.append("persist")
        if settings.workflow.auto_publish:
            nodes.append("publish")
        return WorkflowDefinition(name="default", nodes=nodes)

    def run_default_workflow(self, settings: HubSettings, payload: dict) -> WorkflowContext:
        workflow = self.build_default_workflow(settings)
        context = WorkflowContext(settings=settings, payload=payload)
        return self.engine.execute(workflow, context)
