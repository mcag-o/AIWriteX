from __future__ import annotations

from pathlib import Path

from content_hub.domain.content.entities import ContentDocument


class FileArticleRepository:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def save(self, document: ContentDocument) -> Path:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        safe_title = document.title.replace("|", "_").replace("/", "_")
        suffix = ".html" if document.content_format.lower() == "html" else ".md"
        path = self.root_dir / f"{safe_title}{suffix}"
        path.write_text(document.body, encoding="utf-8")
        return path

    def list_documents(self) -> list[ContentDocument]:
        if not self.root_dir.exists():
            return []
        documents = []
        for path in sorted(self.root_dir.glob("*")):
            if path.suffix.lower() not in {".md", ".html", ".txt"}:
                continue
            documents.append(self.read(path))
        return documents

    def read(self, path: Path) -> ContentDocument:
        content = path.read_text(encoding="utf-8")
        return ContentDocument(
            title=path.stem.replace("_", "|"),
            body=content,
            content_format=path.suffix.lstrip(".") or "markdown",
        )

    def update(self, path: Path, body: str) -> ContentDocument:
        path.write_text(body, encoding="utf-8")
        return self.read(path)

    def delete(self, path: Path) -> None:
        if path.exists():
            path.unlink()
