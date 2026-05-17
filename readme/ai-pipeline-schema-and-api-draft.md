# AI Pipeline 数据库与接口草案

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-05-17 | Codex | 基于 `readme/ai-pipeline-design.md` 补充 `ai_pipeline` 首期数据库表结构、接口草案、优先级与实施步骤 |

## 1. 文档目标

本文档承接 [ai-pipeline-design.md](/C:/Users/xiaoshuyui/github_repo/auto_ml/readme/ai-pipeline-design.md)，把 `ai_pipeline` 的设计进一步收敛到：

- 可落 SQL 的表结构草案
- 可落 REST 的接口草案
- 主服务与 `ai_pipeline` 的职责分工
- 首期实施优先级与步骤

本文档不是最终 DDL，而是用于确定方向、字段边界和改造顺序的工程草案。

## 2. 首期总体结论

首期推荐采用以下方案：

- `ai_pipeline` 与 `automl_server` 共用同一个 MySQL 库 `auto_ml`
- `ai_pipeline` 独立维护自己的数据库连接池，不与主服务共用 engine/session
- 新增 `ai_pipeline_*` 前缀表，不新建独立库
- pipeline 模板、版本、binding、run、artifact 全部落数据库
- Nacos 只保留基础设施与运行时配置，不再保存业务 pipeline 模板

## 3. 数据库设计原则

### 3.1 命名风格

沿用当前项目约定：

- 表名小写下划线
- 逻辑删除字段统一使用 `is_deleted`
- 统一保留 `id / created_at / updated_at / is_deleted`
- 结构化扩展数据优先先落 `TEXT` JSON，而不是过早拆成很多表

### 3.2 为什么首期大量使用 JSON TEXT

当前项目已有明显风格：

- `dataset.scenario_config`
- `sample_item.payload`
- `available_model.class_names`
- `task.config`

都使用 `TEXT` 存 JSON。

对 `ai_pipeline` 来说，这个选择首期是合理的，因为：

- 模板 DSL 迭代会比较快
- 动态表单 schema 变化也会比较快
- 运行输入、产物 metadata、资源绑定都天然是半结构化数据

因此建议：

- 关键检索字段拆列
- 大块 DSL、schema、binding 继续走 JSON TEXT

### 3.3 检索字段与 JSON 的边界

应该拆列的字段：

- `template_key`
- `scene_type`
- `status`
- `binding_type`
- `binding_target_id`
- `run_id`
- `trigger_mode`
- `artifact_type`

可以留在 JSON 的字段：

- `definition_json`
- `form_schema_json`
- `resource_bindings_json`
- `input_payload_json`
- `output_payload_json`
- `metadata_json`

## 4. 表结构草案

## 4.1 `ai_pipeline_template`

用途：

- 模板主记录
- 稳定业务标识
- 当前发布版本引用

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `template_key` | VARCHAR(128) | 模板稳定标识，唯一 |
| `name` | VARCHAR(255) | 模板名称 |
| `description` | TEXT | 模板描述 |
| `scene_type` | VARCHAR(64) | 场景类型，如 `assist_annotation` / `video_annotation` |
| `input_kind` | VARCHAR(64) | 主输入类型，如 `image` / `video` / `text` |
| `output_kind` | VARCHAR(64) | 主输出类型，如 `annotation_bbox` |
| `status` | VARCHAR(32) | `draft / published / disabled` |
| `latest_version` | INT | 最新版本号 |
| `published_version` | INT | 当前发布版本号，可空 |
| `is_builtin` | TINYINT(1) | 是否系统内置模板 |
| `created_by` | VARCHAR(64) | 创建人 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `uk_ai_pipeline_template_key(template_key)`
- `idx_ai_pipeline_template_scene_type(scene_type)`
- `idx_ai_pipeline_template_status(status)`

说明：

- `template_key` 不能随着重命名变化
- `name` 可以用于展示层修改

## 4.2 `ai_pipeline_template_version`

用途：

- 模板版本快照
- DSL 与表单 schema 的实际存储位置

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `template_id` | BIGINT | 关联模板 |
| `version` | INT | 版本号 |
| `definition_json` | LONGTEXT | pipeline DSL JSON |
| `form_schema_json` | LONGTEXT | 前端配置表单 schema JSON |
| `change_note` | VARCHAR(512) | 变更说明 |
| `is_published` | TINYINT(1) | 是否已发布 |
| `created_by` | VARCHAR(64) | 创建人 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `uk_ai_pipeline_template_version(template_id, version)`
- `idx_ai_pipeline_template_version_published(template_id, is_published)`

说明：

- `definition_json` 建议包含：
  - `steps`
  - `data_inputs`
  - `runtime_inputs`
  - `resource_slots`
  - `output_schema`
- `form_schema_json` 可以是对 `definition_json` 的前端友好投影，也可以直接冗余存储，首期更推荐冗余，减少前端解析复杂度

## 4.3 `ai_pipeline_binding`

用途：

- 业务对象与模板的绑定关系
- 项目级默认 prompt / 资源默认绑定的挂载点

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `binding_type` | VARCHAR(64) | 绑定对象类型，如 `annotation_project` |
| `binding_target_id` | BIGINT | 绑定对象 ID |
| `template_id` | BIGINT | 模板 ID |
| `template_version` | INT | 绑定版本 |
| `name` | VARCHAR(255) | 绑定名称，可用于项目内区分 |
| `description` | TEXT | 绑定说明 |
| `is_default` | TINYINT(1) | 是否默认绑定 |
| `runtime_input_defaults_json` | LONGTEXT | 项目级默认运行参数 |
| `resource_bindings_json` | LONGTEXT | 项目级资源绑定 |
| `created_by` | VARCHAR(64) | 创建人 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `idx_ai_pipeline_binding_target(binding_type, binding_target_id)`
- `idx_ai_pipeline_binding_template(template_id, template_version)`
- `idx_ai_pipeline_binding_default(binding_type, binding_target_id, is_default)`

说明：

- 这里是未来替代 `annotation.assist_pipeline` 的核心表
- `runtime_input_defaults_json` 是“项目默认 prompt / 默认阈值”等的推荐位置

## 4.4 `ai_pipeline_run`

用途：

- 一次执行实例

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `run_id` | VARCHAR(64) | 外部可见运行 ID，唯一 |
| `template_id` | BIGINT | 模板 ID |
| `template_version` | INT | 模板版本 |
| `binding_id` | BIGINT | 绑定 ID，可空 |
| `source_type` | VARCHAR(64) | 触发来源，如 `annotation_project` |
| `source_id` | BIGINT | 来源对象 ID |
| `trigger_mode` | VARCHAR(32) | `sync / async` |
| `execution_mode` | VARCHAR(32) | `interactive / batch / video` |
| `status` | VARCHAR(32) | `pending / queued / running / succeeded / failed / canceled` |
| `progress` | INT | 0-100 |
| `data_inputs_json` | LONGTEXT | 本次数据输入 |
| `runtime_inputs_json` | LONGTEXT | 本次运行参数 |
| `resource_bindings_json` | LONGTEXT | 本次最终资源绑定快照 |
| `result_summary_json` | LONGTEXT | 最终结果摘要 |
| `error_message` | TEXT | 错误信息 |
| `started_at` | DATETIME | 开始时间 |
| `finished_at` | DATETIME | 结束时间 |
| `created_by` | VARCHAR(64) | 触发人 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `uk_ai_pipeline_run_run_id(run_id)`
- `idx_ai_pipeline_run_status(status)`
- `idx_ai_pipeline_run_source(source_type, source_id)`
- `idx_ai_pipeline_run_binding(binding_id)`
- `idx_ai_pipeline_run_created_at(created_at)`

说明：

- `resource_bindings_json` 建议保存执行时快照，避免模板和绑定后续变化影响审计

## 4.5 `ai_pipeline_run_step`

用途：

- 每一步的执行状态
- 调试和问题排查

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `run_id` | BIGINT | 关联 `ai_pipeline_run.id` |
| `step_key` | VARCHAR(128) | 步骤 key |
| `step_name` | VARCHAR(255) | 步骤名称 |
| `step_type` | VARCHAR(64) | `builtin / resource / transform / control` |
| `executor` | VARCHAR(128) | 执行器名称 |
| `status` | VARCHAR(32) | 步骤状态 |
| `attempt_count` | INT | 尝试次数 |
| `input_ref_json` | LONGTEXT | 输入引用 |
| `output_ref_json` | LONGTEXT | 输出引用 |
| `error_message` | TEXT | 错误信息 |
| `started_at` | DATETIME | 开始时间 |
| `finished_at` | DATETIME | 结束时间 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `idx_ai_pipeline_run_step_run_id(run_id)`
- `idx_ai_pipeline_run_step_status(run_id, status)`
- `idx_ai_pipeline_run_step_key(run_id, step_key)`

## 4.6 `ai_pipeline_artifact`

用途：

- 中间产物和最终产物索引

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `run_id` | BIGINT | run ID |
| `run_step_id` | BIGINT | 步骤 ID，可空 |
| `artifact_key` | VARCHAR(128) | 产物 key |
| `artifact_type` | VARCHAR(64) | `image / video_chunk / annotation_json / preview_image / report` |
| `storage_type` | VARCHAR(32) | `minio / s3 / local_ref` |
| `bucket_name` | VARCHAR(128) | bucket 名称 |
| `object_key` | VARCHAR(512) | 对象路径 |
| `content_type` | VARCHAR(128) | 内容类型 |
| `size_bytes` | BIGINT | 大小 |
| `metadata_json` | LONGTEXT | 扩展元数据 |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `idx_ai_pipeline_artifact_run_id(run_id)`
- `idx_ai_pipeline_artifact_run_step_id(run_step_id)`
- `idx_ai_pipeline_artifact_type(artifact_type)`

## 4.7 `ai_pipeline_event_log`

用途：

- 记录运行期事件流
- 首期可以只做轻量事件日志，不需要复杂 tracing 系统

建议字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | BIGINT PK | 主键 |
| `run_id` | BIGINT | run ID |
| `event_type` | VARCHAR(64) | `queued / step_started / step_finished / progress / failed` |
| `event_payload` | LONGTEXT | 事件内容 JSON |
| `created_at` | DATETIME | 创建时间 |
| `updated_at` | DATETIME | 更新时间 |
| `is_deleted` | TINYINT(1) | 逻辑删除 |

建议索引：

- `idx_ai_pipeline_event_log_run_id(run_id, created_at)`

说明：

- 这个表对视频与长任务很重要
- 首期先做简单落库即可，不必先上外部日志系统

## 5. 对现有表的增量改造建议

## 5.1 `annotation`

当前已有：

- `prompt`
- `assist_pipeline`

建议首期增量新增：

| 字段 | 类型 | 说明 |
|------|------|------|
| `default_ai_pipeline_binding_id` | BIGINT | 默认绑定关系 ID，可空 |

为什么不建议直接删除 `assist_pipeline`：

- 当前前端和业务链路已经在用
- 首期应该保持兼容

推荐策略：

- 新链路优先使用 `default_ai_pipeline_binding_id`
- 旧字段保留只读兼容

## 5.2 是否需要单独的资源表

首期不强求新增统一资源总表。

原因：

- ONNX 模型资源已经可以复用 `available_model`
- provider 资源当前仍然更适合走 Nacos 配置

首期建议：

- `onnx_model` 资源从 `available_model` 映射
- `multimodal_provider` 先走运行时 provider registry

等资源类型稳定后，再决定是否抽象统一 `resource_catalog` 表。

## 6. 接口草案

## 6.1 主服务 `automl_server` 负责的接口

主服务更适合承担“管理面”和“业务入口”。

### 6.1.1 模板管理

- `GET /ai-pipeline/templates`
- `GET /ai-pipeline/templates/{templateKey}`
- `POST /ai-pipeline/templates`
- `POST /ai-pipeline/templates/{templateKey}/versions`
- `POST /ai-pipeline/templates/{templateKey}/publish`
- `POST /ai-pipeline/templates/{templateKey}/disable`

### 6.1.2 Binding 管理

- `GET /ai-pipeline/bindings`
- `POST /ai-pipeline/bindings`
- `PUT /ai-pipeline/bindings/{bindingId}`
- `DELETE /ai-pipeline/bindings/{bindingId}`

### 6.1.3 针对 annotation project 的绑定接口

- `GET /annotation/{annotationId}/ai-pipelines`
- `POST /annotation/{annotationId}/ai-pipelines/bindings`
- `PUT /annotation/{annotationId}/ai-pipelines/default-binding`

### 6.1.4 运行入口

- `POST /annotation/{annotationId}/ai-pipelines/run-sync`
- `POST /annotation/{annotationId}/ai-pipelines/runs`
- `GET /annotation/{annotationId}/ai-pipelines/runs`

说明：

- `run-sync` 主要给单图交互式辅助标注
- `runs` 主要给视频或长任务

## 6.2 `ai_pipeline` 服务负责的接口

`ai_pipeline` 更适合承担“执行面接口”。

### 6.2.1 模板查询

- `GET /v1/pipeline-templates`
- `GET /v1/pipeline-templates/{templateKey}`
- `GET /v1/pipeline-templates/{templateKey}/form-schema`

### 6.2.2 执行接口

- `POST /v1/pipeline-runs/sync`
- `POST /v1/pipeline-runs`
- `GET /v1/pipeline-runs/{runId}`
- `GET /v1/pipeline-runs/{runId}/steps`
- `GET /v1/pipeline-runs/{runId}/artifacts`
- `POST /v1/pipeline-runs/{runId}/cancel`

### 6.2.3 资源辅助查询

- `GET /v1/resources`

说明：

- 首期这个接口可以只返回当前模板所需资源的过滤后列表
- 也可以继续由 `automl_server` 聚合后再下发给前端

## 6.3 `form-schema` 返回草案

```json
{
  "template_key": "onnx_bbox_assist",
  "name": "ONNX BBox 辅助标注",
  "scene_type": "assist_annotation",
  "data_inputs": [
    {
      "key": "primary_image",
      "label": "输入图片",
      "value_type": "image",
      "required": true,
      "widget": "image-asset-picker"
    }
  ],
  "runtime_inputs": [
    {
      "key": "user_prompt",
      "label": "提示词",
      "value_type": "string",
      "required": false,
      "widget": "textarea",
      "default_value": ""
    },
    {
      "key": "score_threshold",
      "label": "置信度阈值",
      "value_type": "number",
      "required": false,
      "widget": "number",
      "default_value": 0.25
    }
  ],
  "resource_slots": [
    {
      "key": "detector_model",
      "label": "检测模型",
      "value_type": "resource_ref",
      "required": true,
      "widget": "resource-select",
      "widget_props": {
        "resource_type": "onnx_model",
        "task_kind": "detection_bbox",
        "deployed_only": true
      }
    }
  ]
}
```

## 6.4 同步执行请求草案

```json
{
  "template_key": "onnx_bbox_assist",
  "template_version": 3,
  "binding_id": 12,
  "data_inputs": {
    "primary_image": {
      "sample_item_id": 1001,
      "asset_id": 8801
    }
  },
  "runtime_inputs": {
    "user_prompt": "请重点识别安全帽和安全背心",
    "score_threshold": 0.3
  },
  "resource_bindings": {
    "detector_model": {
      "resource_id": "model:88"
    }
  },
  "context": {
    "annotation_id": 12,
    "dataset_id": 22
  }
}
```

## 6.5 异步执行响应草案

```json
{
  "run_id": "run_20260517_xxx",
  "status": "queued",
  "trigger_mode": "async"
}
```

## 7. 首期实施优先级

## 7.1 P0：必须先完成

这些是架构转向的基础，不先做后面都会返工。

### P0-1 建立数据库模型

范围：

- `ai_pipeline_template`
- `ai_pipeline_template_version`
- `ai_pipeline_binding`
- `ai_pipeline_run`
- `ai_pipeline_run_step`
- `ai_pipeline_artifact`
- `ai_pipeline_event_log`
- `annotation.default_ai_pipeline_binding_id`

原因：

- 没有这些表，就仍然只能靠 Nacos 和字符串字段拼装

### P0-2 Pipeline 模板从 Nacos 迁到数据库

范围：

- 编写一次性导入脚本
- `ai_pipeline` 启动优先查数据库
- 数据库为空时短暂兼容回退 Nacos

原因：

- 这是后续前后端 schema 驱动和 binding 的前提

### P0-3 定义动态输入 schema

范围：

- 明确 `data_inputs / runtime_inputs / resource_slots`
- 明确 `prompt` 走 `runtime_inputs`
- 明确 `form_schema_json` 存储模型

原因：

- 不先定义清楚，前端后端会很快陷入特判

## 7.2 P1：首期可用闭环

### P1-1 单图同步执行

范围：

- `POST /v1/pipeline-runs/sync`
- 先支撑 annotation 场景单图调用

原因：

- 能较快替换当前同步 MQ RPC 的核心交互链路

### P1-2 ONNX 模型资源槽位

范围：

- 资源选择过滤 `available_model`
- binding 支持默认模型选择
- 执行器支持调用 ONNX 推理资源

原因：

- 这是你当前最直接的业务需求

### P1-3 前端 schema 驱动表单首版

范围：

- `textarea`
- `number`
- `resource-select`
- `image-asset-picker`

原因：

- 足够覆盖“提示词 + 模型选择 + 图片输入”首期闭环

## 7.3 P2：为视频和长任务铺路

### P2-1 异步 run 与事件流

范围：

- `POST /v1/pipeline-runs`
- `GET /v1/pipeline-runs/{runId}`
- MQ 事件状态更新

### P2-2 artifact 引用体系

范围：

- 统一视频分片、帧结果、结果文件的存储引用

### P2-3 视频输入 schema

范围：

- `video-asset-picker`
- 采样参数
- 帧处理策略

## 7.4 P3：后续增强

- 多模态 `content_items`
- 可视化模板管理
- 模板版本对比
- 统一资源目录
- 更通用的控制节点和 batch node

## 8. 推荐实施步骤

## Step 1：先落库，不急着改前端

建议先做：

- SQL migration 草案
- ORM model 草案
- 模板导入脚本

输出结果：

- 数据库里能看到模板、版本和 binding 表

## Step 2：先让 `ai_pipeline` 从数据库读模板

建议先做：

- 模板查询 service
- 模板版本解析
- 兼容 Nacos 回退

输出结果：

- 即使前端不改，服务内部也已经从数据库驱动

## Step 3：打通单图同步执行

建议先做：

- `run-sync` 接口
- ONNX 资源执行器
- annotation 侧调用入口

输出结果：

- 当前辅助标注单图场景可以跑起来

## Step 4：前端改成 schema 驱动

建议先做最小组件集：

- `textarea`
- `number`
- `resource-select`
- `image-asset-picker`

输出结果：

- 可以按模板动态渲染“提示词 + 模型选择 + 图片输入”

## Step 5：再做异步 run

建议后做：

- run 状态表更新
- 事件日志
- MQ 状态通知

输出结果：

- 为视频和批处理铺路

## 9. 不建议的实施方式

以下做法首期不推荐：

### 9.1 先上可视化编排器

原因：

- 当前真正缺的是模板、binding、run、schema，不是拖拽 UI

### 9.2 先拆独立数据库

原因：

- 当前还不到那个复杂度
- 会增加迁移与运维负担

### 9.3 继续把 pipeline 主数据放在 Nacos

原因：

- 后续所有 binding、版本、表单、审计都会继续受限

### 9.4 让前端按 pipeline 名称写专属表单

原因：

- 扩展性会很差
- 很快就会堆很多业务分支

## 10. 关键决策摘要

### 10.1 数据库

- 同库分表
- 独立连接池
- 不新建独立库

### 10.2 模板存储

- 模板与版本进数据库
- Nacos 退出业务模板存储角色

### 10.3 动态输入

- `prompt` 进入 `runtime_inputs`
- 不继续简单塞到 `params`

### 10.4 前后端协作

- 后端返回 `form-schema`
- 前端按字段类型和 widget 渲染

### 10.5 实施顺序

- 先表结构
- 再模板迁移
- 再单图同步闭环
- 再前端 schema 驱动
- 最后补异步 run 和视频能力

## 11. 下一步建议

下一步最合适的动作是：

1. 先把这份草案收敛成一版确认后的表结构
2. 基于确认结果输出 `mysql/migrations` SQL 草案
3. 同时列出 `automl_server` 和未来 `ai_pipeline` 目录下的文件改造清单

也就是先锁数据库与接口边界，再开始代码实施。
