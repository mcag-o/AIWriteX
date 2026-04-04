from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from content_hub.application.services.platform_service import PlatformService


class PlatformType(Enum):
    WECHAT = "wechat"
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    TOUTIAO = "toutiao"
    BAIJIAHAO = "baijiahao"
    ZHIHU = "zhihu"
    DOUBAN = "douban"

    @classmethod
    def _get_display_names(cls) -> dict[str, str]:
        return {
            "wechat": "微信公众号",
            "xiaohongshu": "小红书",
            "douyin": "抖音",
            "toutiao": "今日头条",
            "baijiahao": "百家号",
            "zhihu": "知乎",
            "douban": "豆瓣",
        }

    @classmethod
    def get_all_platforms(cls) -> list[str]:
        return [platform.value for platform in cls]

    @classmethod
    def get_display_name(cls, platform_value: str) -> str:
        return cls._get_display_names().get(platform_value, platform_value)

    @classmethod
    def get_platform_key(cls, display_name: str) -> str:
        for key, name in cls._get_display_names().items():
            if name == display_name:
                return key
        return "wechat"

    @classmethod
    def get_all_display_names(cls) -> list[str]:
        display_names = cls._get_display_names()
        return [display_names[p.value] for p in cls]

    @classmethod
    def is_valid_platform(cls, platform_name: str) -> bool:
        return platform_name in cls.get_all_platforms()


@dataclass
class PublishResult:
    success: bool
    message: str
    platform_id: str | None = None
    error_code: str | None = None


class PlatformAdapter:
    platform_key = "wechat"

    def __init__(self) -> None:
        self._platforms = {item["key"]: item for item in PlatformService().list_platforms()}

    def supports_html(self) -> bool:
        return bool(self._platforms.get(self.platform_key, {}).get("supports_html", False))

    def supports_template(self) -> bool:
        return bool(self._platforms.get(self.platform_key, {}).get("supports_template", False))

    def get_platform_name(self) -> str:
        return self.platform_key

    def format_content(self, content_result: Any, **kwargs) -> str:
        return getattr(content_result, "content", "") or getattr(content_result, "body", "")

    def publish_content(self, content_result: Any, **kwargs) -> PublishResult:
        return PublishResult(
            success=False,
            message=f"{self.platform_key} compatibility adapter is deprecated",
            platform_id=self.platform_key,
            error_code="DEPRECATED_COMPAT_SHIM",
        )

    def register_platform_adapter(self, name: str, adapter: Any) -> None:
        self._platforms[name] = {"key": name, "adapter": adapter}


class WeChatAdapter(PlatformAdapter):
    platform_key = "wechat"


class XiaohongshuAdapter(PlatformAdapter):
    platform_key = "xiaohongshu"


class DouyinAdapter(PlatformAdapter):
    platform_key = "douyin"


class ToutiaoAdapter(PlatformAdapter):
    platform_key = "toutiao"


class BaijiahaoAdapter(PlatformAdapter):
    platform_key = "baijiahao"


class ZhihuAdapter(PlatformAdapter):
    platform_key = "zhihu"


class DoubanAdapter(PlatformAdapter):
    platform_key = "douban"
