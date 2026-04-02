# 文章中转站

这是从 `AIWriteX` 中抽取出来的服务化内容中站骨架。

当前已包含：
- 配置中枢
- 内容仓储
- 模板仓储
- 模板资产库
- 发布记录仓储
- 节点化工作流运行时
- 作业服务
- FastAPI 服务入口

目录结构：
- `文章中转站/src/content_hub/`
- `文章中转站/knowledge/templates/`
- `文章中转站/tests/content_hub/`
- `文章中转站/pyproject.toml`
- `文章中转站/requirements.txt`
- `文章中转站/main.py`

启动方式：

```bash
PYTHONPATH=src uvicorn content_hub.interfaces.api.main:app --reload
```

当前版本是抽取后的第一阶段服务化结果，可作为后续继续二开的主目录。
