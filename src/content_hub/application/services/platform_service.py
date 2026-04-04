from __future__ import annotations


class PlatformService:
    def list_platforms(self) -> list[dict]:
        return [
            {
                "key": "wechat",
                "display_name": "微信公众号",
                "supports_html": True,
                "supports_template": True,
                "supports_publish": True,
                "default_content_format": "html",
                "account_type": "wechat_official",
            },
            {
                "key": "xiaohongshu",
                "display_name": "小红书",
                "supports_html": False,
                "supports_template": False,
                "supports_publish": False,
                "default_content_format": "markdown",
                "account_type": "xiaohongshu",
            },
            {
                "key": "douyin",
                "display_name": "抖音",
                "supports_html": False,
                "supports_template": False,
                "supports_publish": False,
                "default_content_format": "markdown",
                "account_type": "douyin",
            },
        ]
