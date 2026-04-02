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
        self.assertIn('@app.post("/templates")', source)
        self.assertIn('@app.put("/templates/rename")', source)
        self.assertIn('@app.post("/templates/copy")', source)
        self.assertIn('@app.put("/templates/move")', source)
        self.assertIn('@app.delete("/templates")', source)
        self.assertIn('@app.get("/content")', source)
        self.assertIn('@app.post("/content")', source)
        self.assertIn('@app.get("/content/read")', source)
        self.assertIn('@app.put("/content")', source)
        self.assertIn('@app.delete("/content")', source)
        self.assertIn('@app.get("/publish/records")', source)
        self.assertIn('@app.get("/jobs")', source)
        self.assertIn('@app.post("/jobs")', source)
        self.assertIn('@app.get("/jobs/{job_id}")', source)
        self.assertIn('@app.post("/jobs/{job_id}/cancel")', source)
        self.assertIn('@app.get("/jobs/{job_id}/events")', source)
        self.assertIn('@app.post("/workflows/execute")', source)


if __name__ == "__main__":
    unittest.main()
