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

    def test_extracted_project_contains_independent_runtime_files(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        article_hub_dir = project_root / "文章中转站"

        self.assertTrue((article_hub_dir / "src" / "content_hub" / "interfaces" / "api" / "main.py").exists())
        self.assertTrue((article_hub_dir / "tests" / "content_hub" / "test_api_structure.py").exists())
        self.assertTrue((article_hub_dir / "requirements.txt").exists())
        self.assertTrue((article_hub_dir / "pyproject.toml").exists())
        self.assertTrue((article_hub_dir / "README.md").exists())

    def test_root_main_entry_is_removed_in_favor_of_extracted_runtime(self) -> None:
        project_root = Path(__file__).resolve().parents[2]

        self.assertFalse((project_root / "main.py").exists())

    def test_legacy_web_api_modules_are_removed(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        legacy_api_dir = project_root / "src" / "ai_write_x" / "web" / "api"

        self.assertFalse(legacy_api_dir.exists())
        self.assertFalse((legacy_api_dir / "articles.py").exists())
        self.assertFalse((legacy_api_dir / "config.py").exists())
        self.assertFalse((legacy_api_dir / "generate.py").exists())
        self.assertFalse((legacy_api_dir / "templates.py").exists())

    def test_legacy_web_package_is_reduced_to_bridge_entry_only(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        legacy_web_dir = project_root / "src" / "ai_write_x" / "web"
        web_app = (legacy_web_dir / "app.py").read_text(encoding="utf-8")

        self.assertTrue((legacy_web_dir / "app.py").exists())
        self.assertFalse((legacy_web_dir / "__init__.py").exists())
        self.assertIn("from content_hub.interfaces.compat.legacy_web_app import app", web_app)

    def test_docs_no_longer_recommend_root_main_entry(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        readme = (project_root / "README.md").read_text(encoding="utf-8")
        agents = (project_root / "AGENTS.md").read_text(encoding="utf-8")

        self.assertNotIn("python .\\main.py", readme)
        self.assertNotIn("python3 main.py", agents)

    def test_legacy_crew_main_is_only_a_compatibility_shim(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        crew_main = (project_root / "src" / "ai_write_x" / "crew_main.py").read_text(encoding="utf-8")

        self.assertIn("from content_hub.interfaces.compat.legacy_runner import run_legacy_workflow", crew_main)
        self.assertNotIn("build_container", crew_main)

    def test_legacy_unified_workflow_is_only_a_compatibility_shim(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        unified_workflow = (project_root / "src" / "ai_write_x" / "core" / "unified_workflow.py").read_text(encoding="utf-8")

        self.assertIn("from content_hub.interfaces.compat.legacy_workflow import UnifiedContentWorkflow", unified_workflow)
        self.assertNotIn("DimensionalCreativeEngine", unified_workflow)

    def test_legacy_system_init_is_only_a_compatibility_shim(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        system_init = (project_root / "src" / "ai_write_x" / "core" / "system_init.py").read_text(encoding="utf-8")

        self.assertIn("from content_hub.interfaces.compat.legacy_system_init import", system_init)
        self.assertNotIn("WeChatAdapter", system_init)

    def test_legacy_platform_adapters_is_only_a_compatibility_shim(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        platform_adapters = (project_root / "src" / "ai_write_x" / "adapters" / "platform_adapters.py").read_text(encoding="utf-8")

        self.assertIn("from content_hub.interfaces.compat.legacy_platforms import", platform_adapters)
        self.assertNotIn("pub2wx", platform_adapters)

    def test_legacy_wx_publisher_is_only_a_compatibility_shim(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        wx_publisher = (project_root / "src" / "ai_write_x" / "tools" / "wx_publisher.py").read_text(encoding="utf-8")

        self.assertIn("from content_hub.interfaces.compat.legacy_wx_publisher import", wx_publisher)
        self.assertNotIn("BeautifulSoup", wx_publisher)

    def test_remaining_ai_write_x_surface_is_limited_to_known_compat_layers(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        ai_write_x_root = project_root / "src" / "ai_write_x"
        expected = {
            "crew_main.py",
            "version.py",
            "__init__.py",
            "web/app.py",
            "core/unified_workflow.py",
            "core/system_init.py",
            "adapters/platform_adapters.py",
            "tools/wx_publisher.py",
            "core/__init__.py",
            "adapters/__init__.py",
            "tools/__init__.py",
            "utils/__init__.py",
            "config/__init__.py",
        }

        actual = {
            str(path.relative_to(ai_write_x_root))
            for path in ai_write_x_root.rglob("*.py")
            if "__pycache__" not in path.parts
        }

        self.assertTrue(expected.issubset(actual))


if __name__ == "__main__":
    unittest.main()
