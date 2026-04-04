from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from content_hub.application.jobs.event_service import JobEventService
from content_hub.application.jobs.job_service import InMemoryJobRepository, JobService
from content_hub.application.publishers.record_only_publisher import RecordOnlyPublisher
from content_hub.application.publishers.wechat_publisher import WeChatPublisher
from content_hub.application.services.config_service import ConfigService
from content_hub.application.services.content_service import ContentService
from content_hub.application.services.ingestion_service import IngestionService
from content_hub.application.services.platform_service import PlatformService
from content_hub.application.services.publish_service import PublishService
from content_hub.application.services.template_service import TemplateService
from content_hub.application.services.workflow_service import WorkflowService
from content_hub.bootstrap.settings import HubSettings
from content_hub.infrastructure.storage.article_repository import FileArticleRepository
from content_hub.infrastructure.storage.ingestion_repository import FileHotTopicIngestionRepository
from content_hub.infrastructure.storage.ingestion_repository import FileRawContentIngestionRepository
from content_hub.infrastructure.storage.ingestion_repository import FileReferenceIngestionRepository
from content_hub.infrastructure.storage.job_event_repository import FileJobEventRepository
from content_hub.infrastructure.storage.job_repository import FileJobRepository
from content_hub.infrastructure.storage.publish_record_repository import FilePublishRecordRepository
from content_hub.infrastructure.storage.template_repository import FileTemplateRepository
from content_hub.runtime.nodes.creative import CreativeEnhancementNode
from content_hub.runtime.nodes.design import SimpleDesignNode
from content_hub.runtime.nodes.generation import StaticGenerationNode
from content_hub.runtime.nodes.persist import PersistNode
from content_hub.runtime.nodes.publish import RecordPublishNode
from content_hub.runtime.nodes.registry import NodeRegistry
from content_hub.runtime.nodes.rewrite import SuffixRewriteNode
from content_hub.runtime.nodes.template_fill import TemplateFillNode


@dataclass
class ServiceContainer:
    settings: HubSettings
    config_service: ConfigService
    template_service: TemplateService
    content_service: ContentService
    ingestion_service: IngestionService
    platform_service: PlatformService
    publish_service: PublishService
    workflow_service: WorkflowService
    job_service: JobService
    job_event_service: JobEventService


def build_container(project_root: Path, settings: HubSettings | None = None) -> ServiceContainer:
    config_service = ConfigService(project_root)
    resolved_settings = settings or config_service.load_legacy_settings()

    template_repository = FileTemplateRepository(resolved_settings.template.root_dir)
    article_repository = FileArticleRepository(resolved_settings.storage.article_dir)
    ingestion_repository = FileReferenceIngestionRepository(resolved_settings.storage.root_dir / "reference_urls.json")
    raw_content_repository = FileRawContentIngestionRepository(resolved_settings.storage.root_dir / "raw_contents.json")
    hot_topic_repository = FileHotTopicIngestionRepository(resolved_settings.storage.root_dir / "hot_topics.json")
    publish_record_repository = FilePublishRecordRepository(resolved_settings.storage.publish_record_file)
    job_repository = FileJobRepository(resolved_settings.storage.root_dir / "jobs.json")
    job_event_repository = FileJobEventRepository(resolved_settings.storage.root_dir / "job_events.json")
    publish_service = PublishService(
        publish_record_repository,
        {
            "wechat": WeChatPublisher(
                publish_record_repository,
                resolved_settings.publish.wechat_credentials,
            ),
            "record-only": RecordOnlyPublisher(publish_record_repository),
        },
    )

    registry = NodeRegistry()
    registry.register("generate", StaticGenerationNode())
    registry.register("design", SimpleDesignNode())
    registry.register("creative", CreativeEnhancementNode())
    registry.register("rewrite", SuffixRewriteNode(" [rewritten-by-content-hub]"))
    registry.register("template", TemplateFillNode(TemplateService(template_repository)))
    registry.register("persist", PersistNode(article_repository))
    registry.register(
        "publish",
        RecordPublishNode(publish_service, resolved_settings.workflow.publish_platform),
    )

    workflow_service = WorkflowService(registry)
    job_event_service = JobEventService(job_repository, job_event_repository)
    job_service = JobService(workflow_service.engine, job_repository, job_event_service)

    return ServiceContainer(
        settings=resolved_settings,
        config_service=config_service,
        template_service=TemplateService(template_repository),
        content_service=ContentService(article_repository, publish_service),
        ingestion_service=IngestionService(
            ingestion_repository,
            raw_content_repository,
            hot_topic_repository,
        ),
        platform_service=PlatformService(),
        publish_service=publish_service,
        workflow_service=workflow_service,
        job_service=job_service,
        job_event_service=job_event_service,
    )
