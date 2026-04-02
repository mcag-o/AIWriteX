from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMSettings:
    provider: str
    model: str
    api_key: str = ""
    api_base: str = ""
    max_tokens: int = 0


@dataclass
class WorkflowSettings:
    publish_platform: str
    article_format: str = "markdown"
    auto_publish: bool = False


@dataclass
class RewriteSettings:
    enabled: bool = False


@dataclass
class TemplateSettings:
    root_dir: Path


@dataclass
class StorageSettings:
    root_dir: Path

    @property
    def article_dir(self) -> Path:
        return self.root_dir / "articles"

    @property
    def publish_record_file(self) -> Path:
        return self.root_dir / "publish_records.json"


@dataclass
class WeChatCredential:
    appid: str
    appsecret: str
    author: str = ""


@dataclass
class PublishSettings:
    wechat_credentials: list[WeChatCredential] = field(default_factory=list)


@dataclass
class HubSettings:
    llm: LLMSettings
    workflow: WorkflowSettings
    rewrite: RewriteSettings
    template: TemplateSettings
    storage: StorageSettings
    publish: PublishSettings

    @classmethod
    def load(cls, path: Path) -> "HubSettings":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        llm_raw = raw.get("llm", {})
        workflow_raw = raw.get("workflow", {})
        rewrite_raw = raw.get("rewrite", {})
        template_raw = raw.get("template", {})
        storage_raw = raw.get("storage", {})
        publish_raw = raw.get("publish", {})
        credentials = [
            WeChatCredential(
                appid=item.get("appid", ""),
                appsecret=item.get("appsecret", ""),
                author=item.get("author", ""),
            )
            for item in publish_raw.get("wechat_credentials", [])
        ]
        return cls(
            llm=LLMSettings(
                provider=llm_raw.get("provider", ""),
                model=llm_raw.get("model", ""),
                api_key=llm_raw.get("api_key", ""),
                api_base=llm_raw.get("api_base", ""),
                max_tokens=int(llm_raw.get("max_tokens", 0) or 0),
            ),
            workflow=WorkflowSettings(
                publish_platform=workflow_raw.get("publish_platform", "wechat"),
                article_format=workflow_raw.get("article_format", "markdown"),
                auto_publish=bool(workflow_raw.get("auto_publish", False)),
            ),
            rewrite=RewriteSettings(enabled=bool(rewrite_raw.get("enabled", False))),
            template=TemplateSettings(root_dir=Path(template_raw.get("root_dir", "knowledge/templates"))),
            storage=StorageSettings(root_dir=Path(storage_raw.get("root_dir", "output"))),
            publish=PublishSettings(wechat_credentials=credentials),
        )

    @classmethod
    def from_legacy_config(cls, config_data: dict[str, Any], project_root: Path) -> "HubSettings":
        api_section = config_data.get("api", {})
        api_type = api_section.get("api_type", "OpenRouter")
        provider_config = api_section.get(api_type, {})
        model_index = provider_config.get("model_index", 0)
        key_index = provider_config.get("key_index", 0)
        models = provider_config.get("model", []) or [""]
        keys = provider_config.get("api_key", []) or [""]
        wechat_credentials = [
            WeChatCredential(
                appid=item.get("appid", ""),
                appsecret=item.get("appsecret", ""),
                author=item.get("author", ""),
            )
            for item in config_data.get("wechat", {}).get("credentials", [])
        ]
        return cls(
            llm=LLMSettings(
                provider=api_type,
                model=models[model_index] if model_index < len(models) else "",
                api_key=keys[key_index] if key_index < len(keys) else "",
                api_base=provider_config.get("api_base", ""),
                max_tokens=int(provider_config.get("max_tokens", 0) or 0),
            ),
            workflow=WorkflowSettings(
                publish_platform=config_data.get("publish_platform", "wechat"),
                article_format=config_data.get("article_format", "markdown"),
                auto_publish=bool(config_data.get("auto_publish", False)),
            ),
            rewrite=RewriteSettings(enabled=bool(config_data.get("dimensional_creative", {}).get("enabled", False))),
            template=TemplateSettings(root_dir=project_root / "knowledge" / "templates"),
            storage=StorageSettings(root_dir=project_root / "output"),
            publish=PublishSettings(wechat_credentials=wechat_credentials),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "api_key": self.llm.api_key,
                "api_base": self.llm.api_base,
                "max_tokens": self.llm.max_tokens,
            },
            "workflow": {
                "publish_platform": self.workflow.publish_platform,
                "article_format": self.workflow.article_format,
                "auto_publish": self.workflow.auto_publish,
            },
            "rewrite": {"enabled": self.rewrite.enabled},
            "template": {"root_dir": str(self.template.root_dir)},
            "storage": {"root_dir": str(self.storage.root_dir)},
            "publish": {
                "wechat_credentials": [
                    {
                        "appid": item.appid,
                        "appsecret": item.appsecret,
                        "author": item.author,
                    }
                    for item in self.publish.wechat_credentials
                ]
            },
        }
