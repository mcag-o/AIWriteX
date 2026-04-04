from pathlib import Path
import tempfile
import unittest

from content_hub.application.jobs.job_service import InMemoryJobRepository, JobService
from content_hub.application.publishers.record_only_publisher import RecordOnlyPublisher
from content_hub.application.services.publish_service import PublishService
from content_hub.application.services.template_service import TemplateService
from content_hub.application.services.workflow_service import WorkflowService
from content_hub.bootstrap.settings import HubSettings, LLMSettings, PublishSettings, RewriteSettings, StorageSettings, TemplateSettings, WeChatCredential, WorkflowSettings
from content_hub.domain.content.entities import ContentDocument
from content_hub.domain.workflow.models import WorkflowDefinition
from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository
from content_hub.runtime.engine.workflow_engine import WorkflowEngine
from content_hub.runtime.nodes.base import WorkflowContext
from content_hub.runtime.nodes.creative import CreativeEnhancementNode
from content_hub.runtime.nodes.generation import StaticGenerationNode
from content_hub.runtime.nodes.persist import PersistNode
from content_hub.runtime.nodes.publish import RecordPublishNode
from content_hub.runtime.nodes.registry import NodeRegistry
from content_hub.runtime.nodes.rewrite import SuffixRewriteNode
from content_hub.runtime.nodes.design import SimpleDesignNode
from content_hub.runtime.nodes.template_fill import TemplateFillNode


class WorkflowEngineTestCase(unittest.TestCase):
    def test_creative_node_enhances_document_and_marks_metadata(self) -> None:
        settings = HubSettings(
            llm=LLMSettings(provider="stub", model="stub-model"),
            workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
            rewrite=RewriteSettings(enabled=True),
            template=TemplateSettings(root_dir=Path("/tmp/templates")),
            storage=StorageSettings(root_dir=Path("/tmp/storage")),
            publish=PublishSettings(wechat_credentials=[]),
        )
        context = WorkflowContext(
            settings=settings,
            payload={"topic": "创意流程"},
            document=ContentDocument(title="创意流程", body="# 创意流程\n\n原始内容", content_format="markdown"),
        )

        result = CreativeEnhancementNode().execute(context)

        self.assertIn("创意增强", result.document.body)
        self.assertEqual(result.document.metadata["transformation_type"], "dimensional_creative")

    def test_creative_node_reads_style_from_payload_and_records_metadata(self) -> None:
        settings = HubSettings(
            llm=LLMSettings(provider="stub", model="stub-model"),
            workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
            rewrite=RewriteSettings(enabled=True),
            template=TemplateSettings(root_dir=Path("/tmp/templates")),
            storage=StorageSettings(root_dir=Path("/tmp/storage")),
            publish=PublishSettings(wechat_credentials=[]),
        )
        context = WorkflowContext(
            settings=settings,
            payload={"topic": "创意流程", "creative_style": "storytelling"},
            document=ContentDocument(title="创意流程", body="# 创意流程\n\n原始内容", content_format="markdown"),
        )

        result = CreativeEnhancementNode().execute(context)

        self.assertEqual(result.document.metadata["creative_style"], "storytelling")
        self.assertIn("storytelling", result.document.body)

    def test_creative_node_records_selected_dimensions_and_compatibility(self) -> None:
        settings = HubSettings(
            llm=LLMSettings(provider="stub", model="stub-model"),
            workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
            rewrite=RewriteSettings(enabled=True),
            template=TemplateSettings(root_dir=Path("/tmp/templates")),
            storage=StorageSettings(root_dir=Path("/tmp/storage")),
            publish=PublishSettings(wechat_credentials=[]),
        )
        context = WorkflowContext(
            settings=settings,
            payload={
                "topic": "创意流程",
                "creative_style": "storytelling",
                "creative_intensity": 1.1,
                "creative_dimensions": [
                    {"category": "style", "value": "叙事化", "description": "增强故事感"},
                    {"category": "tone", "value": "温暖", "description": "增强亲和力"},
                ],
            },
            document=ContentDocument(title="创意流程", body="# 创意流程\n\n原始内容", content_format="markdown"),
        )

        result = CreativeEnhancementNode().execute(context)

        self.assertEqual(result.document.metadata["creative_intensity"], 1.1)
        self.assertEqual(result.document.metadata["creative_intensity_description"], "激进")
        self.assertEqual(len(result.document.metadata["selected_dimensions"]), 2)
        self.assertEqual(result.document.metadata["selected_dimensions"][0]["category"], "style")
        self.assertEqual(result.document.metadata["compatibility_score"], 1.0)

    def test_creative_node_marks_incompatible_dimension_combinations(self) -> None:
        settings = HubSettings(
            llm=LLMSettings(provider="stub", model="stub-model"),
            workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
            rewrite=RewriteSettings(enabled=True),
            template=TemplateSettings(root_dir=Path("/tmp/templates")),
            storage=StorageSettings(root_dir=Path("/tmp/storage")),
            publish=PublishSettings(wechat_credentials=[]),
        )
        context = WorkflowContext(
            settings=settings,
            payload={
                "topic": "创意流程",
                "creative_dimensions": [
                    {"category": "style", "value": "叙事化", "description": "增强故事感"},
                    {"category": "format", "value": "清单体", "description": "增强结构感"},
                ],
            },
            document=ContentDocument(title="创意流程", body="# 创意流程\n\n原始内容", content_format="markdown"),
        )

        result = CreativeEnhancementNode().execute(context)

        self.assertLess(result.document.metadata["compatibility_score"], 1.0)

    def test_default_workflow_uses_creative_node_when_rewrite_enabled(self) -> None:
        settings = HubSettings(
            llm=LLMSettings(provider="stub", model="stub-model"),
            workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
            rewrite=RewriteSettings(enabled=True),
            template=TemplateSettings(root_dir=Path("/tmp/templates")),
            storage=StorageSettings(root_dir=Path("/tmp/storage")),
            publish=PublishSettings(wechat_credentials=[]),
        )

        workflow = WorkflowService(NodeRegistry()).build_default_workflow(settings)

        self.assertIn("creative", workflow.nodes)
        self.assertNotIn("rewrite", workflow.nodes)
    def test_html_workflow_can_use_design_node_without_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="html", auto_publish=False),
                rewrite=RewriteSettings(enabled=False),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[]),
            )

            registry = NodeRegistry()
            registry.register("generate", StaticGenerationNode())
            registry.register("design", SimpleDesignNode())
            registry.register("persist", PersistNode(FileArticleRepository(settings.storage.article_dir)))

            workflow = WorkflowDefinition(name="html-design", nodes=["generate", "design", "persist"])
            context = WorkflowContext(settings=settings, payload={"topic": "设计流程"})

            result = WorkflowEngine(registry).execute(workflow, context)

            self.assertEqual(result.document.content_format, "html")
            self.assertIn("<html>", result.document.body)
            self.assertIn("设计流程", result.document.body)
            self.assertTrue(result.artifact_path is not None)
            self.assertEqual(result.artifact_path.suffix, ".html")
    def test_html_workflow_can_fill_template_before_persist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="html", auto_publish=False),
                rewrite=RewriteSettings(enabled=False),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[]),
            )
            settings.template.root_dir.mkdir(parents=True, exist_ok=True)
            (settings.template.root_dir / "Tech").mkdir(parents=True, exist_ok=True)
            (settings.template.root_dir / "Tech" / "demo.html").write_text(
                "<html><body><h1>{{title}}</h1><article>{{body}}</article></body></html>",
                encoding="utf-8",
            )

            registry = NodeRegistry()
            registry.register("generate", StaticGenerationNode())
            registry.register(
                "template",
                TemplateFillNode(TemplateService(FileTemplateRepository(settings.template.root_dir))),
            )
            registry.register("persist", PersistNode(FileArticleRepository(settings.storage.article_dir)))

            workflow = WorkflowDefinition(name="html-template", nodes=["generate", "template", "persist"])
            context = WorkflowContext(
                settings=settings,
                payload={"topic": "模板流程", "template_category": "Tech", "template_name": "demo"},
            )

            result = WorkflowEngine(registry).execute(workflow, context)

            self.assertEqual(result.document.content_format, "html")
            self.assertIn("<html>", result.document.body)
            self.assertIn("模板流程", result.document.body)
            self.assertTrue(result.artifact_path is not None)
            self.assertEqual(result.artifact_path.suffix, ".html")
    def test_publish_node_delegates_to_publish_service(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            publish_repository = FilePublishRecordRepository(tmp_path / "publish_records.json")
            publish_service = PublishService(publish_repository, {"wechat": RecordOnlyPublisher(publish_repository)})
            node = RecordPublishNode(publish_service, "wechat")
            context = WorkflowContext(
                settings=HubSettings(
                    llm=LLMSettings(provider="stub", model="stub-model"),
                    workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=True),
                    rewrite=RewriteSettings(enabled=False),
                    template=TemplateSettings(root_dir=tmp_path / "templates"),
                    storage=StorageSettings(root_dir=tmp_path / "storage"),
                    publish=PublishSettings(wechat_credentials=[]),
                ),
                payload={"topic": "发布委托"},
                document=ContentDocument(title="Publish Title", body="# Publish", content_format="markdown"),
            )

            result = node.execute(context)

            self.assertEqual(len(result.publish_results), 1)
            self.assertTrue(result.publish_results[0].success)
            self.assertEqual(publish_service.get_history("Publish Title")[0]["platform"], "wechat")
    def test_executes_registered_nodes_and_persists_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=True),
                rewrite=RewriteSettings(enabled=True),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(
                    wechat_credentials=[WeChatCredential(appid="demo-app", appsecret="demo-secret", author="demo-author")]
                ),
            )
            settings.template.root_dir.mkdir(parents=True, exist_ok=True)
            registry = NodeRegistry()
            article_repository = FileArticleRepository(settings.storage.article_dir)
            publish_repository = FilePublishRecordRepository(settings.storage.publish_record_file)
            publish_service = PublishService(publish_repository, {"wechat": RecordOnlyPublisher(publish_repository)})
            template_repository = FileTemplateRepository(settings.template.root_dir)
            engine = WorkflowEngine(registry)

            registry.register("generate", StaticGenerationNode())
            registry.register("rewrite", SuffixRewriteNode(" -- rewritten"))
            registry.register("persist", PersistNode(article_repository))
            registry.register("publish", RecordPublishNode(publish_service, settings.workflow.publish_platform))

            workflow = WorkflowDefinition(
                name="demo",
                nodes=["generate", "rewrite", "persist", "publish"],
            )
            context = WorkflowContext(
                settings=settings,
                payload={"topic": "测试话题", "template_repository": template_repository},
            )

            result = engine.execute(workflow, context)

            self.assertIn("rewritten", result.document.body)
            self.assertTrue(result.artifact_path is not None)
            self.assertTrue(result.artifact_path.exists())
            self.assertEqual(len(result.publish_results), 1)
            self.assertTrue(result.publish_results[0].success)

    def test_job_service_runs_workflow_and_tracks_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
                rewrite=RewriteSettings(enabled=False),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[]),
            )
            registry = NodeRegistry()
            registry.register("generate", StaticGenerationNode())
            registry.register("persist", PersistNode(FileArticleRepository(settings.storage.article_dir)))
            engine = WorkflowEngine(registry)
            jobs = JobService(engine=engine, job_repository=InMemoryJobRepository())
            workflow = WorkflowDefinition(name="job-demo", nodes=["generate", "persist"])

            job = jobs.run_workflow(workflow=workflow, settings=settings, payload={"topic": "中站任务"})

            self.assertEqual(job.status, "completed")
            self.assertIsNotNone(job.result)
            self.assertIsNotNone(job.result.artifact_path)

    def test_job_service_records_job_events_for_successful_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
                rewrite=RewriteSettings(enabled=True),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[]),
            )
            registry = NodeRegistry()
            registry.register("generate", StaticGenerationNode())
            registry.register("rewrite", SuffixRewriteNode(" [evented]"))
            registry.register("persist", PersistNode(FileArticleRepository(settings.storage.article_dir)))
            engine = WorkflowEngine(registry)
            jobs = JobService(engine=engine, job_repository=InMemoryJobRepository())
            workflow = WorkflowDefinition(name="job-events", nodes=["generate", "rewrite", "persist"])

            job = jobs.run_workflow(workflow=workflow, settings=settings, payload={"topic": "事件测试"})

            self.assertEqual(job.status, "completed")
            self.assertEqual([event.status for event in job.events], ["running", "completed"])
            self.assertEqual(job.events[0].message, "workflow started")
            self.assertEqual(job.events[1].message, "workflow completed")

    def test_job_service_records_failure_event_when_workflow_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
                rewrite=RewriteSettings(enabled=False),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[]),
            )
            jobs = JobService(engine=WorkflowEngine(NodeRegistry()), job_repository=InMemoryJobRepository())
            workflow = WorkflowDefinition(name="job-events-fail", nodes=["missing-node"])

            job = jobs.run_workflow(workflow=workflow, settings=settings, payload={"topic": "失败事件"})

            self.assertEqual(job.status, "failed")
            self.assertEqual([event.status for event in job.events], ["running", "failed"])
            self.assertEqual(job.events[-1].message, "workflow failed")
            self.assertEqual(job.events[-1].detail, "missing-node")

    def test_job_service_can_cancel_existing_job_and_append_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = HubSettings(
                llm=LLMSettings(provider="stub", model="stub-model"),
                workflow=WorkflowSettings(publish_platform="wechat", article_format="markdown", auto_publish=False),
                rewrite=RewriteSettings(enabled=False),
                template=TemplateSettings(root_dir=tmp_path / "templates"),
                storage=StorageSettings(root_dir=tmp_path / "storage"),
                publish=PublishSettings(wechat_credentials=[]),
            )
            jobs = JobService(engine=WorkflowEngine(NodeRegistry()), job_repository=InMemoryJobRepository())
            existing = jobs.job_repository.save(jobs.create_job_run())

            cancelled = jobs.cancel_job(existing.job_id)

            self.assertEqual(cancelled.status, "cancelled")
            self.assertEqual(cancelled.events[-1].status, "cancelled")
            self.assertEqual(cancelled.events[-1].message, "workflow cancelled")

    def test_job_service_cancel_missing_job_raises_key_error(self) -> None:
        jobs = JobService(engine=WorkflowEngine(NodeRegistry()), job_repository=InMemoryJobRepository())

        with self.assertRaises(KeyError):
            jobs.cancel_job("missing-job")


if __name__ == "__main__":
    unittest.main()
