# AI Pipeline 实施改造清单

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-05-17 | Codex | 基于当前仓库结构整理 `ai_pipeline` 首期改造文件清单与实施边界 |

## 1. 目标

本文档把 `ai_pipeline` 的首期改造拆到目录和文件粒度，便于逐步实施。

目标不是一次性全改完，而是明确：

- 哪些文件需要新增
- 哪些文件需要修改
- 哪些改动属于 P0 / P1 / P2

## 2. 改造范围总览

涉及目录：

- `mysql/migrations`
- `mysql/init`
- `automl_server/app/db/models`
- `automl_server/app/config`
- `automl_server/app/modules`
- `automl_server/app/main.py`
- 新服务目录 `ai_pipeline`（建议新增，不继续堆在 `auto_augment_pipeline` 下）

## 3. P0 改造清单

P0 目标：

- 建立数据库模型
- 主服务具备模板/binding 管理骨架
- 为后续模板迁移和执行链路打基础

### 3.1 `mysql/migrations`

新增：

- `mysql/migrations/20260517_ai_pipeline_schema_draft.sql`

后续需要补：

- 正式版 migration SQL

### 3.2 `mysql/init`

后续需要修改：

- `mysql/init/01_init_automl.sql`

目的：

- 将确认后的 `ai_pipeline_*` 表结构同步到初始化脚本

### 3.3 `automl_server/app/db/models`

建议新增：

- `automl_server/app/db/models/ai_pipeline.py`

内容：

- `AiPipelineTemplate`
- `AiPipelineTemplateVersion`
- `AiPipelineBinding`
- `AiPipelineRun`
- `AiPipelineRunStep`
- `AiPipelineArtifact`
- `AiPipelineEventLog`

需要修改：

- `automl_server/app/db/models/annotation.py`
  - 新增 `default_ai_pipeline_binding_id`
- `automl_server/app/db/models/__init__.py`
  - 导出新模型

### 3.4 `automl_server/app/config`

可能需要新增或修改：

- `automl_server/app/config/settings.py`

内容：

- 新增 `AiPipelineConfig`
- 替代或兼容 `AutoAugmentPipelineConfig`

建议策略：

- 首期先保留 `auto_augment_pipeline` 配置名兼容
- 内部逐步过渡到 `ai_pipeline`

### 3.5 `automl_server/app/modules`

建议新增模块目录：

- `automl_server/app/modules/ai_pipeline/`

建议文件：

- `__init__.py`
- `router.py`
- `service.py`
- `schemas.py`
- `crud.py`

P0 阶段先实现：

- 模板查询
- binding 查询与创建
- 结构化 schema 返回骨架

### 3.6 `automl_server/app/main.py`

需要修改：

- 注册 `ai_pipeline` 模块路由

### 3.7 `automl_server/app/modules/annotation`

需要修改：

- `schemas.py`
- `service.py`
- `router.py`

首期目的：

- 增加 annotation 与 `ai_pipeline binding` 的查询/设置入口
- 暂不强制替换所有旧 `assist_pipeline` 逻辑

## 4. P1 改造清单

P1 目标：

- 打通单图同步执行闭环
- 接入 ONNX 模型资源选择
- 让前端能基于 schema 渲染最小表单

### 4.1 `automl_server/app/modules/ai_pipeline`

继续补充：

- `run-sync` 相关接口
- annotation 项目触发入口
- binding 默认值与运行时覆盖合并逻辑

### 4.2 `automl_server/app/modules/deploy`

可能需要修改：

- `service.py`
- `schemas.py`

目的：

- 输出更适合 `resource-select` 的模型资源列表
- 支持按 `task_kind / deployed_only / runtime_template` 过滤

### 4.3 `frontend_v2`

首期会涉及但当前先不动代码，后续清单建议如下：

- `src/api/aiPipeline.ts`
- `src/types/aiPipeline.ts`
- annotation 页面相关组件

最小组件集：

- `textarea`
- `number`
- `resource-select`
- `image-asset-picker`

## 5. P2 改造清单

P2 目标：

- 异步 run
- artifact 管理
- 视频 pipeline 入口

### 5.1 新服务 `ai_pipeline`

建议新增目录：

- `ai_pipeline/`

建议结构：

```text
ai_pipeline/
├── app.py
├── config.py
├── db.py
├── models.py
├── template_service.py
├── run_service.py
├── artifact_service.py
├── executors/
├── resources/
├── workers/
└── mq/
```

首期不需要把所有能力都迁过去，但目录建议直接按最终定位搭好。

### 5.2 `automl_server/app/mq`

后续需要修改或新增：

- 新的 `ai_pipeline` 运行状态事件消息
- run 状态消费处理器

## 6. 建议的实施顺序

### Step 1

先做：

- `automl_server/app/db/models/ai_pipeline.py`
- `annotation.py` 增字段
- `models/__init__.py` 导出

### Step 2

再做：

- `automl_server/app/modules/ai_pipeline/`
  - `schemas.py`
  - `crud.py`
  - `service.py`
  - `router.py`

先只实现管理面骨架，不急着做执行器。

### Step 3

再做：

- `main.py` 路由接入
- `settings.py` 配置兼容

### Step 4

再做：

- 模板导入脚本
- 数据库模板查询优先逻辑

### Step 5

最后进入：

- 同步执行
- ONNX 资源绑定
- 前端 schema 表单

## 7. 当前就可以开始的第一批代码

如果现在开始优化框架，最稳的第一批代码工作是：

1. 新增 `automl_server/app/db/models/ai_pipeline.py`
2. 修改 `annotation.py` 增加 `default_ai_pipeline_binding_id`
3. 修改 `models/__init__.py`
4. 新增 `automl_server/app/modules/ai_pipeline/` 基础文件
5. 在 `main.py` 注册新路由

这批改动不会直接破坏现有业务链路，但会把新框架骨架先搭出来。
