from pathlib import Path
import json
import tempfile
import unittest

from content_hub.application.jobs.job_service import JobEvent, JobRun
from content_hub.infrastructure.storage.job_event_repository import FileJobEventRepository
from content_hub.infrastructure.storage.job_repository import FileJobRepository
from content_hub.domain.content.entities import ContentDocument
from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository


class RepositoryTestCase(unittest.TestCase):
    def test_template_repository_lists_and_reads_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_root = Path(tmp_dir) / "templates"
            category = template_root / "Tech"
            category.mkdir(parents=True)
            template_path = category / "t1.html"
            template_path.write_text("<html><body>Hello</body></html>", encoding="utf-8")

            repository = FileTemplateRepository(template_root)

            self.assertEqual(repository.list_categories(), ["Tech"])
            templates = repository.list_templates("Tech")
            self.assertEqual(len(templates), 1)
            self.assertEqual(templates[0].name, "t1")
            self.assertIn("Hello", repository.read_template("Tech", "t1"))

    def test_template_repository_supports_crud_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FileTemplateRepository(Path(tmp_dir) / "templates")

            created = repository.create_template("Tech", "alpha", "<html>alpha</html>")
            self.assertTrue(created.exists())

            renamed = repository.rename_template(created, "beta")
            self.assertTrue(renamed.exists())
            self.assertEqual(renamed.stem, "beta")

            copied = repository.copy_template(renamed, "Finance", "gamma")
            self.assertTrue(copied.exists())
            self.assertEqual(copied.parent.name, "Finance")

            moved = repository.move_template(renamed, "Lifestyle")
            self.assertTrue(moved.exists())
            self.assertEqual(moved.parent.name, "Lifestyle")

            repository.delete_template(moved)
            self.assertFalse(moved.exists())

    def test_article_repository_persists_markdown_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FileArticleRepository(Path(tmp_dir))
            document = ContentDocument(title="Demo Title", body="# Demo\n\nBody", content_format="markdown")

            saved_path = repository.save(document)

            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.suffix, ".md")
            self.assertIn("Demo", saved_path.read_text(encoding="utf-8"))

    def test_article_repository_lists_reads_updates_and_deletes_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FileArticleRepository(Path(tmp_dir))
            path = repository.save(
                ContentDocument(title="Weekly Report", body="# Weekly\n\nOriginal", content_format="markdown")
            )

            documents = repository.list_documents()

            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].title, "Weekly Report")
            self.assertIn("Original", repository.read(path).body)

            repository.update(path, "# Weekly\n\nUpdated")
            self.assertIn("Updated", repository.read(path).body)

            repository.delete(path)
            self.assertEqual(repository.list_documents(), [])

    def test_publish_record_repository_appends_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            records_path = Path(tmp_dir) / "publish_records.json"
            repository = FilePublishRecordRepository(records_path)

            repository.append_record(
                article_title="Demo Title",
                platform="wechat",
                success=True,
                account_info={"appid": "demo-app"},
                error=None,
            )

            payload = json.loads(records_path.read_text(encoding="utf-8"))
            self.assertIn("Demo Title", payload)
            self.assertEqual(payload["Demo Title"][0]["platform"], "wechat")
            self.assertEqual(repository.list_records()["Demo Title"][0]["platform"], "wechat")

    def test_file_job_repository_persists_job_status_events_and_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FileJobRepository(Path(tmp_dir) / "jobs.json")
            artifact_path = Path(tmp_dir) / "output" / "article.md"
            job = JobRun(
                job_id="job-1",
                status="completed",
                error="",
                artifact_path=artifact_path,
                events=[
                    JobEvent(job_id="job-1", status="running", message="workflow started"),
                    JobEvent(job_id="job-1", status="completed", message="workflow completed", detail="saved"),
                ],
            )

            repository.save(job)
            restored = repository.get("job-1")

            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, "completed")
            self.assertEqual(restored.artifact_path, artifact_path)
            self.assertEqual([event.status for event in restored.events], ["running", "completed"])
            self.assertEqual(restored.events[-1].detail, "saved")

    def test_file_job_repository_lists_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FileJobRepository(Path(tmp_dir) / "jobs.json")
            repository.save(JobRun(job_id="job-1", status="running"))
            repository.save(JobRun(job_id="job-2", status="completed"))

            jobs = repository.list_jobs()

            self.assertEqual([job.job_id for job in jobs], ["job-1", "job-2"])

    def test_file_job_event_repository_persists_and_lists_events_by_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FileJobEventRepository(Path(tmp_dir) / "job_events.json")

            repository.append(
                JobEvent(job_id="job-1", status="running", message="workflow started")
            )
            repository.append(
                JobEvent(job_id="job-1", status="completed", message="workflow completed", detail="saved")
            )
            repository.append(
                JobEvent(job_id="job-2", status="failed", message="workflow failed", detail="boom")
            )

            events = repository.list_by_job("job-1")

            self.assertEqual([event.status for event in events], ["running", "completed"])
            self.assertEqual(events[-1].detail, "saved")


if __name__ == "__main__":
    unittest.main()
