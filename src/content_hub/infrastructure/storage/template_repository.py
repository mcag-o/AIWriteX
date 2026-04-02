from __future__ import annotations

from pathlib import Path

from content_hub.domain.template.entities import TemplateAsset


class FileTemplateRepository:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def list_categories(self) -> list[str]:
        if not self.root_dir.exists():
            return []
        return sorted(item.name for item in self.root_dir.iterdir() if item.is_dir())

    def list_templates(self, category: str) -> list[TemplateAsset]:
        category_dir = self.root_dir / category
        if not category_dir.exists():
            return []
        return [
            TemplateAsset(category=category, name=file.stem, path=str(file))
            for file in sorted(category_dir.glob("*.html"))
        ]

    def read_template(self, category: str, name: str) -> str:
        return (self.root_dir / category / f"{name}.html").read_text(encoding="utf-8")

    def create_template(self, category: str, name: str, content: str) -> Path:
        category_dir = self.root_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        path = category_dir / f"{name}.html"
        path.write_text(content, encoding="utf-8")
        return path

    def rename_template(self, path: Path, new_name: str) -> Path:
        target = path.parent / f"{new_name}.html"
        path.rename(target)
        return target

    def copy_template(self, path: Path, target_category: str, new_name: str) -> Path:
        target_dir = self.root_dir / target_category
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{new_name}.html"
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return target

    def move_template(self, path: Path, target_category: str) -> Path:
        target_dir = self.root_dir / target_category
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / path.name
        path.rename(target)
        return target

    def delete_template(self, path: Path) -> None:
        if path.exists():
            path.unlink()
