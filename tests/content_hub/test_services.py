from pathlib import Path
import tempfile
import unittest

from content_hub.application.services.config_service import ConfigService
from content_hub.application.services.content_service import ContentService
from content_hub.application.services.publish_service import PublishService
from content_hub.application.services.template_service import TemplateService
from content_hub.application.services.workflow_service import WorkflowService
from content_hub.application.publishers.record_only_publisher import RecordOnlyPublisher
from content_hub.application.publishers.wechat_publisher import WeChatPublisher
from content_hub.application.jobs.event_service import JobEventService
from content_hub.application.jobs.job_service import InMemoryJobRepository, JobRun, JobService
from content_hub.bootstrap.container import build_container
from content_hub.bootstrap.settings import HubSettings, LLMSettings, PublishSettings, RewriteSettings, StorageSettings, TemplateSettings, WeChatCredential, WorkflowSettings
from content_hub.domain.content.entities import ContentDocument
from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.infrastructure.storage.job_event_repository import FileJobEventRepository
from content_hub.infrastructure.storage.job_repository import FileJobRepository
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository
from content_hub.runtime.engine.workflow_engine import WorkflowEngine
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

    def test_content_service_returns_document_detail_with_publish_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            article_repository = FileArticleRepository(tmp_path / "articles")
            publish_repository = FilePublishRecordRepository(tmp_path / "publish_records.json")
            publish_service = PublishService(
                publish_repository,
                {"wechat": RecordOnlyPublisher(publish_repository)},
            )
            service = ContentService(article_repository, publish_service)

            artifact = service.create_document(title="Detail Article", body="# Detail", content_format="markdown")
            publish_service.record_success("Detail Article", "wechat", {"appid": "demo-app"})

            detail = service.get_document_detail(artifact.artifact_path)

            self.assertEqual(detail["document"].title, "Detail Article")
            self.assertEqual(detail["artifact_path"], artifact.artifact_path)
            self.assertEqual(detail["publish_history"][0]["platform"], "wechat")

    def test_content_service_returns_document_list_view_with_publish_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            article_repository = FileArticleRepository(tmp_path / "articles")
            publish_repository = FilePublishRecordRepository(tmp_path / "publish_records.json")
            publish_service = PublishService(
                publish_repository,
                {"wechat": RecordOnlyPublisher(publish_repository)},
            )
            service = ContentService(article_repository, publish_service)

            artifact = service.create_document(title="List Article", body="# List", content_format="markdown")
            publish_service.record_success("List Article", "wechat", {"appid": "demo-app"})

            listing = service.list_document_views()

            self.assertEqual(listing[0]["title"], "List Article")
            self.assertEqual(listing[0]["artifact_path"], artifact.artifact_path)
            self.assertEqual(listing[0]["publish_count"], 1)
            self.assertTrue(listing[0]["published"])
            self.assertEqual(listing[0]["last_publish_platform"], "wechat")
            self.assertIsNotNone(listing[0]["last_published_at"])

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

    def test_publish_service_publishes_document_through_unified_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FilePublishRecordRepository(Path(tmp_dir) / "publish_records.json")
            service = PublishService(repository, {"wechat": RecordOnlyPublisher(repository)})
            document = ContentDocument(title="Article A", body="# Demo", content_format="markdown")

            result = service.publish_document(document, platform="wechat")

            self.assertTrue(result.success)
            self.assertEqual(result.platform, "wechat")
            self.assertEqual(result.message, "recorded")
            self.assertEqual(result.metadata["publisher"], "record_only")
            self.assertEqual(service.get_history("Article A")[0]["platform"], "wechat")

    def test_publish_service_returns_structured_failure_for_unsupported_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FilePublishRecordRepository(Path(tmp_dir) / "publish_records.json")
            service = PublishService(repository, {"wechat": RecordOnlyPublisher(repository)})
            document = ContentDocument(title="Article A", body="# Demo", content_format="markdown")

            result = service.publish_document(document, platform="xiaohongshu")

            self.assertFalse(result.success)
            self.assertEqual(result.platform, "xiaohongshu")
            self.assertEqual(result.metadata["error_code"], "UNSUPPORTED_PLATFORM")

    def test_wechat_publisher_returns_structured_publish_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FilePublishRecordRepository(Path(tmp_dir) / "publish_records.json")
            publisher = WeChatPublisher(
                repository,
                [WeChatCredential(appid="wx-app", appsecret="wx-secret", author="Tester")],
            )
            document = ContentDocument(title="Article A", body="# Demo", content_format="markdown")

            result = publisher.publish(document, platform="wechat")

            self.assertTrue(result.success)
            self.assertEqual(result.platform, "wechat")
            self.assertEqual(result.metadata["channel"], "wechat")
            self.assertEqual(result.metadata["publisher"], "wechat")
            self.assertEqual(result.metadata["appid"], "wx-app")
            self.assertEqual(result.metadata["author"], "Tester")
            self.assertEqual(repository.list_records()["Article A"][0]["platform"], "wechat")

    def test_wechat_publisher_uses_first_configured_credential_as_account_info(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repository = FilePublishRecordRepository(Path(tmp_dir) / "publish_records.json")
            publisher = WeChatPublisher(
                repository,
                [
                    WeChatCredential(appid="wx-first", appsecret="secret-1", author="Author A"),
                    WeChatCredential(appid="wx-second", appsecret="secret-2", author="Author B"),
                ],
            )
            document = ContentDocument(title="Article B", body="# Demo", content_format="markdown")

            publisher.publish(document, platform="wechat")

            record = repository.list_records()["Article B"][0]
            self.assertEqual(record["account_info"]["appid"], "wx-first")
            self.assertEqual(record["account_info"]["author"], "Author A")

    def test_build_container_exposes_wechat_publisher(self) -> None:
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

            self.assertIsInstance(container.publish_service.publishers["wechat"], WeChatPublisher)

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
            registry.register(
                "publish",
                RecordPublishNode(
                    PublishService(
                        FilePublishRecordRepository(settings.storage.publish_record_file),
                        {"wechat": RecordOnlyPublisher(FilePublishRecordRepository(settings.storage.publish_record_file))},
                    ),
                    "wechat",
                ),
            )

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

    def test_job_event_service_can_use_dedicated_event_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            job_repository = InMemoryJobRepository()
            event_repository = FileJobEventRepository(Path(tmp_dir) / "job_events.json")
            service = JobEventService(job_repository, event_repository)
            job = job_repository.save(JobRun(job_id="job-1", status="running"))

            service.record(job, status="running", message="workflow started")
            service.record(job, status="completed", message="workflow completed", detail="artifact ready")

            self.assertEqual([event.status for event in service.list_events("job-1")], ["running", "completed"])
            self.assertEqual(event_repository.list_by_job("job-1")[-1].detail, "artifact ready")

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

    def test_job_service_lists_jobs_from_repository(self) -> None:
        repository = InMemoryJobRepository()
        repository.save(JobRun(job_id="job-1", status="running"))
        repository.save(JobRun(job_id="job-2", status="completed"))
        service = JobService(engine=WorkflowEngine(NodeRegistry()), job_repository=repository)

        jobs = service.list_jobs()

        self.assertEqual([job.job_id for job in jobs], ["job-1", "job-2"])


if __name__ == "__main__":
    unittest.main()
