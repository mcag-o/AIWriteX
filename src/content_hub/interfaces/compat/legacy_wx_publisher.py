from __future__ import annotations


def pub2wx(
    title: str,
    digest: str,
    article: str,
    appid: str,
    appsecret: str,
    author: str,
    cover_path: str | None = None,
):
    message = (
        "微信发布兼容层已切换到 content_hub；当前保留为兼容 shim，"
        f"appid={appid or ''}, author={author or ''}"
    )
    return message, article, True
