from pathlib import Path
import unittest


class ApiStructureTestCase(unittest.TestCase):
    def test_api_main_exposes_expected_routes_in_source(self) -> None:
        api_main = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "api" / "main.py"
        source = api_main.read_text(encoding="utf-8")

        self.assertIn('@app.get("/health")', source)
        self.assertIn('@app.get("/config")', source)
        self.assertIn('@app.patch("/config")', source)
        self.assertIn('@app.get("/templates/categories")', source)
        self.assertIn('@app.get("/templates")', source)
        self.assertIn('async def templates(', source)
        self.assertIn('platform: str | None = None', source)
        self.assertIn('tag: str | None = None', source)
        self.assertIn('theme: str | None = None', source)
        self.assertIn('style: str | None = None', source)
        self.assertIn('@app.post("/templates")', source)
        self.assertIn('@app.put("/templates/rename")', source)
        self.assertIn('@app.post("/templates/copy")', source)
        self.assertIn('@app.put("/templates/move")', source)
        self.assertIn('@app.delete("/templates")', source)
        self.assertIn('@app.get("/content")', source)
        self.assertIn('@app.get("/content/detail")', source)
        self.assertIn('async def content_list(title: str | None = None, published: bool | None = None)', source)
        self.assertIn('@app.post("/content")', source)
        self.assertIn('@app.get("/content/read")', source)
        self.assertIn('@app.put("/content")', source)
        self.assertIn('@app.delete("/content")', source)
        self.assertIn('@app.get("/platforms")', source)
        self.assertIn('@app.get("/publish/records")', source)
        self.assertIn('@app.get("/jobs")', source)
        self.assertIn('@app.post("/jobs")', source)
        self.assertIn('@app.get("/jobs/{job_id}")', source)
        self.assertIn('@app.post("/jobs/{job_id}/cancel")', source)
        self.assertIn('@app.get("/jobs/{job_id}/events")', source)
        self.assertIn('@app.post("/ingestion/reference-urls")', source)
        self.assertIn('@app.post("/ingestion/raw-content")', source)
        self.assertIn('@app.post("/ingestion/hot-topics")', source)
        self.assertIn('@app.get("/ingestion")', source)
        self.assertIn('@app.post("/workflows/execute")', source)

    def test_compat_module_exposes_legacy_run_bridge(self) -> None:
        compat_module = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "compat" / "legacy_runner.py"
        source = compat_module.read_text(encoding="utf-8")

        self.assertIn("def run_legacy_workflow", source)

    def test_compat_module_exposes_legacy_workflow_shim(self) -> None:
        compat_module = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "compat" / "legacy_workflow.py"
        source = compat_module.read_text(encoding="utf-8")

        self.assertIn("class UnifiedContentWorkflow", source)

    def test_compat_module_exposes_legacy_system_init_shim(self) -> None:
        compat_module = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "compat" / "legacy_system_init.py"
        source = compat_module.read_text(encoding="utf-8")

        self.assertIn("def setup_aiwritex", source)
        self.assertIn("def get_platform_adapter", source)

    def test_compat_module_exposes_legacy_platform_shim(self) -> None:
        compat_module = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "compat" / "legacy_platforms.py"
        source = compat_module.read_text(encoding="utf-8")

        self.assertIn("class PlatformType", source)
        self.assertIn("class WeChatAdapter", source)

    def test_compat_module_exposes_legacy_wx_publisher_shim(self) -> None:
        compat_module = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "compat" / "legacy_wx_publisher.py"
        source = compat_module.read_text(encoding="utf-8")

        self.assertIn("def pub2wx", source)

    def test_compat_module_exposes_legacy_web_app_shim(self) -> None:
        compat_module = Path(__file__).resolve().parents[2] / "src" / "content_hub" / "interfaces" / "compat" / "legacy_web_app.py"
        source = compat_module.read_text(encoding="utf-8")

        self.assertIn("from content_hub.interfaces.api.main import app", source)


if __name__ == "__main__":
    unittest.main()
