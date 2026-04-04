from __future__ import annotations

from content_hub.domain.template.entities import TemplateAsset
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository


class TemplateService:
    def __init__(self, repository: FileTemplateRepository):
        self.repository = repository

    def list_categories(self) -> list[str]:
        return self.repository.list_categories()

    def list_templates(
        self,
        category: str,
        platform: str | None = None,
        tag: str | None = None,
        theme: str | None = None,
        style: str | None = None,
    ) -> list[TemplateAsset]:
        templates = self.repository.list_templates(category)
        if platform is not None:
            templates = [item for item in templates if item.metadata.get("platform") == platform]
        if tag is not None:
            templates = [item for item in templates if tag in item.metadata.get("tags", [])]
        if theme is not None:
            templates = [item for item in templates if item.metadata.get("theme") == theme]
        if style is not None:
            templates = [item for item in templates if item.metadata.get("style") == style]
        return templates

    def read_template(self, category: str, name: str) -> str:
        return self.repository.read_template(category, name)

    def create_template(self, category: str, name: str, content: str):
        return self.repository.create_template(category, name, content)

    def rename_template(self, path, new_name: str):
        return self.repository.rename_template(path, new_name)

    def copy_template(self, path, target_category: str, new_name: str):
        return self.repository.copy_template(path, target_category, new_name)

    def move_template(self, path, target_category: str):
        return self.repository.move_template(path, target_category)

    def delete_template(self, path) -> None:
        self.repository.delete_template(path)
