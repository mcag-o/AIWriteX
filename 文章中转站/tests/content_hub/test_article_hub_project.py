from pathlib import Path
import tempfile
import unittest


class ArticleHubProjectTestCase(unittest.TestCase):
    def test_extracted_project_tree_exists_under_article_hub_directory(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        article_hub_dir = project_root / "文章中转站"

        self.assertTrue(article_hub_dir.exists())
        self.assertTrue((article_hub_dir / "src").exists())
        self.assertTrue((article_hub_dir / "tests").exists())
        self.assertTrue((article_hub_dir / "pyproject.toml").exists())

    def test_extracted_project_includes_template_assets_and_boot_entry(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        article_hub_dir = project_root / "文章中转站"

        self.assertTrue((article_hub_dir / "knowledge" / "templates").exists())
        self.assertTrue((article_hub_dir / "main.py").exists())

    def test_legacy_web_api_modules_are_removed(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        legacy_api_dir = project_root / "src" / "ai_write_x" / "web" / "api"

        self.assertFalse((legacy_api_dir / "articles.py").exists())
        self.assertFalse((legacy_api_dir / "config.py").exists())
        self.assertFalse((legacy_api_dir / "generate.py").exists())
        self.assertFalse((legacy_api_dir / "templates.py").exists())


if __name__ == "__main__":
    unittest.main()
