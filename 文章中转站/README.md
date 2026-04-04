# 文章中转站

`文章中转站/` 是从原始 `AIWriteX` 仓库中抽取出来的 service-first 内容中站运行时，也是当前推荐的主开发目录。

这份 README 不是一个简单的启动说明，而是把以下三类信息整合到了一起：

- 项目来源与迁移背景
- 当前架构、能力边界与完成态判断
- 后续继续开发时需要保留的上下文

如果你后续主要依赖 `文章中转站/` 继续开发，可以把这份文档视为覆盖整个项目的总说明。

---

## 1. 项目定位

原始 `AIWriteX` 是一个以桌面软件为中心的内容生成系统，历史上同时包含：

- 桌面壳与 GUI
- 本地 Web 服务
- 内容生成工作流
- 模板系统
- 平台发布能力
- 配置与工具体系

本次重构的目标不是继续维护桌面应用，而是把其中真正有业务价值的能力抽出来，形成一个可 API 化、可任务化、可继续演进的“内容中站”运行时。

因此，`文章中转站/` 的定位是：

- 新的主运行时
- 未来主开发目录
- 可独立交付的内容中台骨架
- 原始 `AIWriteX` 中高价值业务能力的承接者

简而言之：

> 原项目更像“桌面产品 + 本地服务”，现在的 `文章中转站/` 更像“可独立运行的 service-first 内容中站”。

---

## 2. 当前完成态

到当前阶段，主体提取工作已经基本完成。

这意味着：

- 新运行时已经能够独立承载主路径能力
- 原始仓库中的关键 legacy 核心已大多被 shim 化或降级为兼容层
- 后续工作应以增强 `文章中转站/` 能力为主，而不是继续把 legacy 目录当主开发区

对完成度的直观判断可以这样理解：

- 主体提取完成度：约 `99%+`
- 如果只从“可继续开发的新主项目”角度看：可以视为已完成
- 剩余问题主要是：
  - 少量 compatibility surface 的保留策略
  - 少量 frozen legacy supporting module 的后续清理或继续增强
  - 新 runtime 的质量增强，而不是结构性迁移缺失

因此，当前最合理的开发策略是：

- 以 `文章中转站/` 为主继续开发
- 把原始 `src/ai_write_x/` 视为历史兼容层与参考资料

---

## 3. 当前已包含的核心能力

### 3.1 配置中枢

当前中站已包含 service-first 配置模型与容器装配能力，能够承载：

- LLM 配置
- 工作流配置
- 模板配置
- 存储配置
- 发布配置
- 创意改写配置

虽然还没有完全 1:1 迁移原始巨大 `Config` 的所有复杂字段，但已经具备主运行时需要的配置骨架。

### 3.2 工作流主链路

当前工作流主线已经具备：

- `generate`
- `creative`
- `design`
- `template_fill`
- `persist`
- `publish`

也就是说，新的运行时已经不是只有“生成一段文本”的骨架，而是具备了完整内容流水线的第一版运行能力。

### 3.3 Jobs 子系统

当前作业系统已经具备：

- 创建作业
- 查询作业
- 列出作业
- 取消作业
- 查询作业事件
- 文件化 job repository
- 文件化 event store

因此它已经不只是一个内存中的临时执行器，而是具备基本管理面的服务子系统。

### 3.4 Publish 子系统

当前发布子系统已经具备：

- `PublishService`
- publisher protocol
- `RecordOnlyPublisher`
- `WeChatPublisher`
- 结构化 `PublishResult`
- 微信多账号汇总语义
- 失败语义与错误码

虽然仍不是对旧微信发布实现的 1:1 深度迁移，但已经开始具备真实平台发布器的核心结果模型。

### 3.5 Content 子系统

当前内容域已经具备：

- 内容 CRUD
- 内容详情聚合
- 内容列表视图
- 已发布/未发布过滤
- 发布历史聚合
- 资产级字段：
  - `publish_count`
  - `published`
  - `last_publish_platform`
  - `last_published_at`

因此它已经不是“只会读写文件”，而是开始具备内容资产管理能力。

### 3.6 Template 子系统

当前模板域已经具备：

- 模板分类
- 模板 CRUD
- 模板元数据索引
- 元数据字段：
  - `platform`
  - `tags`
  - `theme`
  - `style`
- API 级筛选

这使得模板库从“目录里的 HTML 文件集合”变成了可查询、可管理的模板资产层。

### 3.7 Ingestion 子系统

当前平台接收层已经有三条最小输入通道：

- `POST /ingestion/reference-urls`
- `POST /ingestion/raw-content`
- `POST /ingestion/hot-topics`

并且已经具备：

- 统一记录模型
- `source_type`
- `status`
- `created_at`
- `payload`
- `GET /ingestion`

这意味着平台接收层已经从“占位 API”进入“可管理输入边界”的阶段。

### 3.8 Platform 目录能力

当前已经从 legacy `platform_adapters.py` 中抽出了平台能力目录层，能够表达：

- 平台 key
- 显示名
- 是否支持 HTML
- 是否支持模板
- 是否支持发布
- 默认内容格式
- 账号类型

这部分将支撑后续内容、模板、发布和 UI/API 的平台能力展示与策略决策。

---

## 4. 当前目录结构

`文章中转站/` 当前应视为一个独立项目，核心目录如下：

- `文章中转站/src/content_hub/`
  - 主运行时代码
- `文章中转站/tests/content_hub/`
  - 当前 extracted runtime 的测试
- `文章中转站/knowledge/templates/`
  - 模板资产库
- `文章中转站/main.py`
  - 独立启动入口
- `文章中转站/requirements.txt`
  - 依赖清单
- `文章中转站/pyproject.toml`
  - 项目元数据

当前建议把这个目录理解成“新的主项目根”，而不是原仓库里的一个附属示例目录。

---

## 5. 如何运行

### 5.1 安装依赖

```bash
python3 -m pip install -r "文章中转站/requirements.txt"
```

建议 Python 版本：

- `>=3.10,<3.13`

### 5.2 运行 API

在仓库根目录执行：

```bash
PYTHONPATH="文章中转站/src" uvicorn content_hub.interfaces.api.main:app --reload
```

### 5.3 运行独立入口

```bash
python3 "文章中转站/main.py"
```

### 5.4 运行测试

```bash
PYTHONPATH="文章中转站/src" python3 -m unittest discover -s "文章中转站/tests/content_hub" -p "test_*.py"
```

---

## 6. 当前架构理解方式

推荐把 `文章中转站/` 理解成下面几层：

1. **bootstrap**
   - 容器装配
   - settings
   - 运行时依赖注入

2. **domain**
   - 内容实体
   - 模板实体
   - 发布结果模型
   - 工作流定义

3. **application/services**
   - `ConfigService`
   - `ContentService`
   - `TemplateService`
   - `PublishService`
   - `WorkflowService`
   - `IngestionService`
   - `PlatformService`

4. **application/jobs**
   - 作业模型
   - 作业服务
   - 事件服务

5. **runtime/nodes**
   - `generate`
   - `creative`
   - `design`
   - `template_fill`
   - `persist`
   - `publish`

6. **infrastructure/storage**
   - 内容仓储
   - 模板仓储
   - 发布记录仓储
   - job/event 仓储
   - ingestion 仓储

7. **interfaces/api**
   - FastAPI 入口与路由

8. **interfaces/compat**
   - 承接 legacy 入口和旧核心的兼容层

---

## 7. 原始仓库剩余内容与当前关系

如果你仍然在原始 monorepo 中工作，那么需要知道：

### 7.1 已经被降为 compatibility surface 的 legacy 文件

- `src/ai_write_x/crew_main.py`
- `src/ai_write_x/web/app.py`
- `src/ai_write_x/core/unified_workflow.py`
- `src/ai_write_x/core/system_init.py`
- `src/ai_write_x/adapters/platform_adapters.py`
- `src/ai_write_x/tools/wx_publisher.py`

这些文件已经不再是主实现，只是兼容旧入口或旧导入路径。

### 7.2 仍然保留的 shared utility / config

这些模块还存在于原始 `src/ai_write_x/` 中，但更像共享支撑或历史工具，不应再被视为主业务入口：

- `src/ai_write_x/config/`
- `src/ai_write_x/utils/`
- `src/ai_write_x/tools/custom_tool.py`
- `src/ai_write_x/tools/search_template.py`
- `src/ai_write_x/tools/hotnews.py`
- `src/ai_write_x/core/tool_registry.py`
- `src/ai_write_x/core/base_framework.py`
- `src/ai_write_x/core/agent_factory.py`
- `src/ai_write_x/core/content_generation.py`
- `src/ai_write_x/core/monitoring.py`

### 7.3 冻结的 legacy supporting module

- `src/ai_write_x/creative/dimensional_engine.py`

当前判断：

- 该模块最有价值的一层能力已经迁入新 runtime
- 剩余部分不再阻塞主体提取完成
- 它可以作为历史参考继续保留，但不应成为后续主开发的依赖中心

---

## 8. 如果只带走 `文章中转站/`，还缺什么

如果你打算把 `文章中转站/` 拿出原仓库独立开发，建议你除了这个目录本身，还把以下知识一起保留下来：

- 当前这份 `README.md`
- 原始迁移计划中的目标边界、架构原则和风险判断
- 原始仓库里形成的 agent/维护说明

也就是说，`文章中转站/` 已经足以作为新的主开发目录，但为了保留迁移知识，你需要让这份 README 自身足够完整。

这也是为什么这份文档要覆盖整个项目，而不只是写启动命令。

---

## 9. 后续开发建议

现在更推荐的工作方式是：

- 把 `文章中转站/` 当主项目继续开发
- 不再把“继续提取 legacy”作为默认目标
- 把原仓库中其余内容视为：
  - 兼容层
  - 历史参考
  - 共享工具来源

### 9.1 推荐继续做的事情

如果你后续还要增强系统，优先建议：

1. 强化 `WeChatPublisher`
   - 更细的错误码
   - 更真实的发布状态语义
   - 封面、草稿、轮询等进一步抽象

2. 强化 `creative / design / template_fill`
   - 更接近旧系统复杂行为
   - 但继续保持新架构边界清晰

3. 强化 ingestion
   - 去重
   - 状态流转
   - job 化处理

4. 逐步减少对原始 `src/ai_write_x/` shared utility 的依赖
   - 让 `文章中转站/` 真正自足

### 9.2 不推荐继续默认做的事情

- 不要继续把 `src/ai_write_x/` 当主开发目录
- 不要再往 legacy compat surface 里新增业务逻辑
- 不要为了“看起来没有 legacy”而机械搬运所有剩余文件

---

## 10. 当前完成度判断

当前可以这样理解项目状态：

- 主体提取：**已完成**
- 新主运行时：**已形成**
- legacy 核心：**已大多 shim 化**
- 剩余 legacy：**已分类为 compat / shared utility / frozen module**

因此从工程判断上说：

> `文章中转站/` 已经足以承载后续主开发，原项目的主体提取任务已经完成。

后面如果还继续做，属于：

- 收尾清理
- 新架构能力增强

而不再属于“主提取工作尚未完成”。

---

## 11. 一句话总结

`文章中转站/` 不是一个“从大项目里临时裁出来的示例目录”，而是当前已经基本成型的 service-first 内容中站主运行时。

如果你接下来要继续做自己的版本，建议：

- 直接以 `文章中转站/` 为主项目开发
- 把原仓库其余部分视为兼容层与历史参考
- 把后续工作重心放在新能力增强，而不是继续大规模 legacy 提取
