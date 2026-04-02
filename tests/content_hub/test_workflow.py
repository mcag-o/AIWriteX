from pathlib import Path
import tempfile
import unittest

from content_hub.application.jobs.job_service import InMemoryJobRepository, JobService
from content_hub.bootstrap.settings import HubSettings, LLMSettings, PublishSettings, RewriteSettings, StorageSettings, TemplateSettings, WeChatCredential, WorkflowSettings
from content_hub.domain.workflow.models import WorkflowDefinition
from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository
from content_hub.runtime.engine.workflow_engine import WorkflowEngine
from content_hub.runtime.nodes.base import WorkflowContext
from content_hub.runtime.nodes.generation import StaticGenerationNode
from content_hub.runtime.nodes.persist import PersistNode
from content_hub.runtime.nodes.publish import RecordPublishNode
from content_hub.runtime.nodes.registry import NodeRegistry
from content_hub.runtime.nodes.rewrite import SuffixRewriteNode


class WorkflowEngineTestCase(unittest.TestCase):
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
            template_repository = FileTemplateRepository(settings.template.root_dir)
            engine = WorkflowEngine(registry)

            registry.register("generate", StaticGenerationNode())
            registry.register("rewrite", SuffixRewriteNode(" -- rewritten"))
            registry.register("persist", PersistNode(article_repository))
            registry.register("publish", RecordPublishNode(publish_repository, settings.workflow.publish_platform))

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
