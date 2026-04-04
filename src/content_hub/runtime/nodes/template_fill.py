from __future__ import annotations

from content_hub.application.services.template_service import TemplateService
from content_hub.domain.content.entities import ContentDocument
from content_hub.runtime.nodes.base import WorkflowContext, WorkflowNode


class TemplateFillNode(WorkflowNode):
    def __init__(self, template_service: TemplateService):
        self.template_service = template_service

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        if context.document is None:
            raise ValueError("document is required before template fill")

        category = context.payload.get("template_category")
        name = context.payload.get("template_name")
        if not category or not name:
            return context

        template = self.template_service.read_template(str(category), str(name))
        body = template.replace("{{title}}", context.document.title).replace("{{body}}", context.document.body)
        context.document = ContentDocument(
            title=context.document.title,
            body=body,
            content_format="html",
            summary=context.document.summary,
            metadata={**context.document.metadata, "template_category": category, "template_name": name},
        )
        return context
