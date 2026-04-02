from pathlib import Path
import tempfile
import unittest

from content_hub.application.services.config_service import ConfigService
from content_hub.application.services.content_service import ContentService
from content_hub.application.services.publish_service import PublishService
from content_hub.application.services.template_service import TemplateService
from content_hub.application.services.workflow_service import WorkflowService
from content_hub.application.jobs.event_service import JobEventService
from content_hub.application.jobs.job_service import InMemoryJobRepository, JobRun
from content_hub.bootstrap.container import build_container
from content_hub.bootstrap.settings import HubSettings, LLMSettings, PublishSettings, RewriteSettings, StorageSettings, TemplateSettings, WeChatCredential, WorkflowSettings
from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.infrastructure.storage.job_repository import FileJobRepository
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository
from content_hub.runtime.nodes.generation import StaticGenerationNode
from content_hub.runtime.nodes.persist import PersistNode
from content_hub.runtime.nodes.publish import RecordPublishNode
from content_hub.runtime.nodes.registry import NodeRegistry
from content_hub.runtime.nodes.rewrite import SuffixRewriteNode


class ServiceTestCase(unittest.TestCase):
    def test_config_service_reads_legacy_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            config_dir = project_root / "src" / "ai_write_x" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "config.yaml").write_text(
                """
publish_platform: wechat
article_format: markdown
auto_publish: true
wechat:
  credentials:
    - appid: legacy-app
      appsecret: legacy-secret
      author: legacy-author
api:
  api_type: OpenRouter
  OpenRouter:
    model_index: 0
    key_index: 0
    model: [openrouter/legacy-model]
    api_key: [legacy-key]
    api_base: https://example.com/v1
    max_tokens: 4096
dimensional_creative:
  enabled: true
""".strip(),
                encoding="utf-8",
            )

            settings = ConfigService(project_root).load_legacy_settings()

            self.assertEqual(settings.llm.model, "openrouter/legacy-model")
            self.assertEqual(settings.publish.wechat_credentials[0].appid, "legacy-app")
            self.assertTrue(settings.rewrite.enabled)

    def test_template_content_and_publish_services_share_file_repositories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            template_root = tmp_path / "templates"
            article_root = tmp_path / "articles"
            record_file = tmp_path / "publish_records.json"
            (template_root / "Finance").mkdir(parents=True)
            (template_root / "Finance" / "weekly.html").write_text("<html>weekly</html>", encoding="utf-8")

            template_service = TemplateService(FileTemplateRepository(template_root))
            content_service = ContentService(FileArticleRepository(article_root))
            publish_service = PublishService(FilePublishRecordRepository(record_file))

            self.assertEqual(template_service.list_categories(), ["Finance"])
            self.assertEqual(template_service.list_templates("Finance")[0].name, "weekly")

            artifact = content_service.create_document(title="Weekly Note", body="# Weekly", content_format="markdown")
            self.assertTrue(artifact.artifact_path is not None)
            self.assertTrue(artifact.artifact_path.exists())

            result = publish_service.record_success(
                article_title="Weekly Note",
                platform="wechat",
                account_info={"appid": "demo-app"},
            )
            self.assertTrue(result.success)
            self.assertEqual(publish_service.list_records()["Weekly Note"][0]["platform"], "wechat")

    def test_content_service_lists_and_updates_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = ContentService(FileArticleRepository(Path(tmp_dir)))

            artifact = service.create_document(title="Insight", body="# Insight\n\nBody", content_format="markdown")
            documents = service.list_documents()

            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].title, "Insight")

            updated = service.update_document(artifact.artifact_path, "# Insight\n\nUpdated")
            self.assertIn("Updated", updated.body)

    def test_template_service_returns_template_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "templates"
            (root / "Tech").mkdir(parents=True)
            (root / "Tech" / "alpha.html").write_text("<html>alpha</html>", encoding="utf-8")
            service = TemplateService(FileTemplateRepository(root))

            self.assertEqual(service.read_template("Tech", "alpha"), "<html>alpha</html>")

    def test_template_service_supports_crud_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "templates"
            service = TemplateService(FileTemplateRepository(root))

            created = service.create_template("Tech", "alpha", "<html>alpha</html>")
            renamed = service.rename_template(created, "beta")
            copied = service.copy_template(renamed, "Finance", "gamma")
            moved = service.move_template(renamed, "Lifestyle")

            self.assertTrue(created.parent.exists())
            self.assertEqual(copied.parent.name, "Finance")
            self.assertEqual(moved.parent.name, "Lifestyle")

    def test_publish_service_can_filter_history_by_article_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = PublishService(FilePublishRecordRepository(Path(tmp_dir) / "publish_records.json"))
            service.record_success("Article A", "wechat", {"appid": "a"})
            service.record_success("Article B", "wechat", {"appid": "b"})

            history = service.get_history("Article A")

            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["account_info"]["appid"], "a")

    def test_workflow_service_builds_default_registry_and_executes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=True),
                rewrite=RewriteSettings(enabled=True),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[WeChatCredential(appid="a", appsecret="b", author="c")]),
            )

            registry = NodeRegistry()
            registry.register("generate", StaticGenerationNode())
            registry.register("rewrite", SuffixRewriteNode(" [styled]"))
            registry.register("persist", PersistNode(FileArticleRepository(settings.storage.article_dir)))
            registry.register("publish", RecordPublishNode(FilePublishRecordRepository(settings.storage.publish_record_file), "wechat"))

            service = WorkflowService(registry)
            result = service.run_default_workflow(settings=settings, payload={"topic": "服务化测试"})

            self.assertIn("styled", result.document.body)
            self.assertTrue(result.artifact_path is not None)
            self.assertEqual(result.publish_results[0].platform, "wechat")

    def test_job_event_service_appends_and_lists_job_events(self) -> None:
        repository = InMemoryJobRepository()
        service = JobEventService(repository)
        job = repository.save(JobRun(job_id="job-1", status="running"))

        service.record(job, status="running", message="workflow started")
        service.record(job, status="completed", message="workflow completed", detail="artifact ready")

        self.assertEqual([event.status for event in service.list_events("job-1")], ["running", "completed"])
        self.assertEqual(service.list_events("job-1")[-1].detail, "artifact ready")

    def test_build_container_exposes_job_event_service(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            config_dir = project_root / "src" / "ai_write_x" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "config.yaml").write_text(
                """
publish_platform: wechat
article_format: markdown
auto_publish: false
wechat:
  credentials: []
api:
  api_type: OpenRouter
  OpenRouter:
    model_index: 0
    key_index: 0
    model: [openrouter/test-model]
    api_key: [test-key]
dimensional_creative:
  enabled: false
""".strip(),
                encoding="utf-8",
            )

            container = build_container(project_root)

            self.assertIsInstance(container.job_event_service, JobEventService)
            self.assertIsInstance(container.job_service.job_repository, FileJobRepository)


if __name__ == "__main__":
    unittest.main()
