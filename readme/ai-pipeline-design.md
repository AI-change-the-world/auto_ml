# AI Pipeline 服务重构设计文档

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-05-17 | Codex | 基于现有 `auto_augment_pipeline + automl_server + model_deploy + RabbitMQ + Nacos` 结构整理 `ai_pipeline` 首期重构方案 |

## 1. 背景

当前 `auto_augment_pipeline` 已经不只是“图像增强”服务。

它现在实际承载的是：

- AI 辅助标注能力执行
- 多模态 provider 调用
- 轻量 pipeline 编排
- `automl_server` 的辅助标注能力目录
- 图像标注结果的生成与提取

但它的设计仍然保留了明显的首版痕迹：

- 服务命名偏窄，仍然叫 `auto_augment_pipeline`
- 输入模型强绑定图像标注场景
- pipeline 配置放在 Nacos 中，属于“把业务模板放进配置中心”
- `automl_server` 对它的调用是同步 MQ RPC，图片还能工作，视频场景会变得不自然
- pipeline 元数据和项目绑定关系没有进入数据库，缺少真实的业务管理面

因此，本次重构目标不是简单重命名，而是把这个子服务升级成真正的平台级 AI 执行层：`ai_pipeline`。

## 2. 重构目标

本文档定义 `auto_augment_pipeline -> ai_pipeline` 的首期重构方案。

目标：

- 把服务职责从“自动增强/辅助标注”升级为“AI pipeline 执行引擎”
- 让图片、批量图片、视频等不同输入类型都能接入同一执行框架
- 把 pipeline 模板、资源绑定、运行记录纳入数据库管理
- 把同步 MQ RPC 调用模式升级为“短任务同步、长任务异步”的双通道
- 明确 `Nacos` 与数据库的边界

首期明确不做：

- 不先做 Dify 式可视化拖拽编排器
- 不先做任意 DAG 与复杂分支调度
- 不一次性把所有 AI 能力全部资源化
- 不强行把所有跨服务调用都改成一种协议

## 3. 当前问题总结

### 3.1 服务职责命名与现实不一致

`auto_augment_pipeline` 当前已经承担：

- 多模态图像理解
- 标注草稿生成
- 白框叠加图解析
- pipeline 串联执行

这已经不是“augment”语义。

继续沿用原命名会导致两个问题：

- 服务边界误导，后续接视频/音频时会更别扭
- 业务上会天然把它当成“辅助标注子模块”，而不是平台级执行层

### 3.2 输入模型过于场景化

当前 `TaskPayload` 主要围绕：

- `image`
- `overlay_image`
- `classes`
- `prompt`

这使得现有 pipeline 更像“图像标注特化 DSL”，不适合自然扩展为：

- 视频帧采样
- 长任务处理
- 批量执行
- 中间产物引用

### 3.3 Pipeline 放在 Nacos 不合理

当前 Nacos 中保存了：

- provider 配置
- pipeline 模板

这在首版阶段可行，但继续扩展会有明显问题：

- pipeline 本质是业务模板，不是基础设施配置
- 无法做模板版本、状态、创建人、更新时间、项目绑定
- 无法做数据库级过滤、查询、分页、审计
- 不能稳定承载后续“项目默认 pipeline”“资源绑定”“视频 pipeline”这类业务能力

### 3.4 同步 MQ RPC 不适合视频与长任务

当前 `automl_server -> auto_augment_pipeline` 关键链路采用同步 MQ request-reply。

这个方案对单张图片辅助标注还能接受，但对视频和长任务存在天然问题：

- 调用链路阻塞
- 无进度状态
- 无中间产物引用
- 无取消、重试、恢复机制
- 消息体不适合承载大对象与长时间任务

核心问题不是“用了 MQ”，而是“把 MQ 当同步 RPC”。

## 4. 新服务定位

推荐将该子服务重构为：

- 服务名：`ai_pipeline`
- 角色：平台 AI 执行层

它只负责四类事情：

1. 管理并执行 pipeline 模板
2. 调用平台内外 AI 资源
3. 记录运行状态、日志、产物
4. 对上提供统一的同步/异步执行接口

它不负责：

- 原始业务实体管理，例如数据集、标注项目、任务、模型 CRUD
- 模型训练或模型部署本身
- 复杂前端编排器

## 5. 服务边界

### 5.1 `automl_server`

负责：

- 平台业务入口
- 标注项目、数据集、任务、模型管理
- pipeline 模板管理 API
- 项目默认 pipeline 与资源绑定关系
- 运行任务的业务侧入口

不负责：

- 具体 pipeline 节点执行
- 长任务内部调度
- AI provider 直接调用细节

### 5.2 `ai_pipeline`

负责：

- pipeline 模板加载与校验
- pipeline run 创建、执行、状态推进
- 节点执行器
- 资源调用适配
- 中间产物和结果产物引用管理

### 5.3 `model_deploy`

继续负责：

- ONNX 模型部署
- 推理运行时管理
- 推理健康检查

### 5.4 资源边界

平台上的 ONNX 模型、大模型 provider、OCR 服务、视频处理器，都统一视为“资源”。

但首期不要求所有资源都实现成独立服务。首期可以先将：

- `onnx_model`
- `multimodal_provider`

作为两类标准资源引入。

## 6. 数据库设计原则

你提的两个问题需要分开回答：

### 6.1 是否与主服务共用数据库连接

不建议。

这里的“共用数据库连接”如果指：

- 与 `automl_server` 共用同一个进程里的 SQLAlchemy engine / session factory

答案是明确不建议。

原因：

- `ai_pipeline` 是独立微服务，生命周期独立
- 长任务、异步 worker、批量执行会有完全不同的连接使用模式
- 共享连接池会让服务边界混乱
- 部署、排查、容量规划都更麻烦

推荐做法：

- `ai_pipeline` 独立进程
- 独立维护自己的 DB engine / session factory
- 通过相同的数据库配置连接到同一个 MySQL 实例

也就是：

- 不共连接池
- 可以共 MySQL 实例

### 6.2 是否初始化另一个库

首期不建议。

推荐方案是：

- 与 `automl_server` 共用同一个 MySQL 库 `auto_ml`
- 新增一组独立表，统一使用 `ai_pipeline_` 前缀

理由：

- pipeline 模板、绑定关系、运行记录与主业务强相关
- 需要频繁和 `annotation / dataset / available_model` 做关联
- 现有项目已经采用“单库多模块表”风格
- 先拆独立库会增加事务边界、初始化复杂度和运维成本

只有在下面情况明显出现时，再考虑独立库：

- `ai_pipeline` 运行量明显高于主业务
- 需要单独做库级扩缩容
- 大量运行日志/产物索引带来明显写压力
- 后续准备把它独立成平台通用 AI 工作流服务

因此首期建议：

- 共用 `auto_ml`
- 独立表前缀
- 独立服务连接池

## 7. 为什么 pipeline 要从 Nacos 迁到数据库

结论：要迁，而且应尽快迁。

### 7.1 Nacos 适合什么

Nacos 适合：

- 服务地址
- 超时配置
- 默认 provider 名称
- MQ / S3 / MySQL 等基础设施配置
- 少量基础运行参数

### 7.2 Pipeline 模板属于什么

pipeline 模板属于业务元数据，不属于基础设施配置。

它天然需要：

- CRUD
- 分页
- 状态管理
- 版本管理
- 审计
- 绑定关系
- 前端可见

这些都不是 Nacos 的强项。

### 7.3 继续放 Nacos 的问题

继续把 pipeline 放在 Nacos 中，后续会遇到：

- 模板修改无法精确审计
- 项目级默认模板不好管理
- 难以做版本发布与回滚
- 无法优雅支持“草稿/已发布/停用”
- 视频 pipeline 需要更多结构化元数据时会越来越别扭

### 7.4 推荐边界

推荐边界如下：

- Nacos：基础设施配置、默认运行配置
- Database：pipeline 模板、绑定、运行记录、产物元数据

## 8. 数据模型建议

首期建议新增以下表，全部放在 `auto_ml` 库中。

### 8.1 `ai_pipeline_template`

用途：

- 存储 pipeline 模板主记录

关键字段建议：

- `id`
- `template_key`
- `name`
- `description`
- `scene_type`
- `input_kind`
- `output_kind`
- `status`
- `version`
- `is_builtin`
- `created_by`
- `created_at`
- `updated_at`

说明：

- `template_key` 作为稳定业务标识
- `scene_type` 用于区分 `assist_annotation / image_process / video_annotation`
- `status` 建议值：`draft / published / disabled`

### 8.2 `ai_pipeline_template_version`

用途：

- 存储模板具体内容与版本快照

关键字段建议：

- `id`
- `template_id`
- `version`
- `definition_json`
- `change_note`
- `created_by`
- `created_at`

说明：

- 模板发布后不直接覆盖旧定义
- `definition_json` 存放 pipeline DSL，同时包含 `input_schema / runtime_input_schema / ui_schema / resource_slots`

### 8.3 `ai_pipeline_binding`

用途：

- 存储业务对象与 pipeline 的绑定关系

关键字段建议：

- `id`
- `binding_type`
- `binding_target_id`
- `template_id`
- `template_version`
- `resource_bindings_json`
- `is_default`
- `created_at`
- `updated_at`

说明：

- `binding_type` 例如：`annotation_project`
- `binding_target_id` 例如当前 annotation project id
- `resource_bindings_json` 用于记录资源槽位与具体资源映射

### 8.4 `ai_pipeline_run`

用途：

- 记录一次 pipeline 运行实例

关键字段建议：

- `id`
- `run_id`
- `template_id`
- `template_version`
- `source_type`
- `source_id`
- `trigger_mode`
- `status`
- `progress`
- `input_ref_json`
- `result_ref_json`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`
- `updated_at`

说明：

- `trigger_mode` 区分 `sync / async`
- `source_type` 例如 `annotation_project / predict_task / manual`

### 8.5 `ai_pipeline_run_step`

用途：

- 记录每个步骤的执行状态

关键字段建议：

- `id`
- `run_id`
- `step_key`
- `step_type`
- `status`
- `started_at`
- `finished_at`
- `input_ref_json`
- `output_ref_json`
- `error_message`

### 8.6 `ai_pipeline_artifact`

用途：

- 记录中间产物和最终产物引用

关键字段建议：

- `id`
- `run_id`
- `step_key`
- `artifact_type`
- `storage_type`
- `bucket_name`
- `object_key`
- `content_type`
- `metadata_json`
- `created_at`

说明：

- 图片、视频分段、标注结果、可视化预览都走 artifact 引用
- 不在 MQ / DB 中直接塞大对象内容

## 9. Pipeline 模板 DSL 调整建议

当前 DSL 可以保留一部分思想，但需要去掉过强的业务耦合。

### 9.1 可以保留的部分

- `steps`
- `params`
- `context_mapping`
- `input_key`
- `output_key`

### 9.2 需要新增的部分

- `input_schema`
- `output_schema`
- `resource_slots`
- `execution_mode`
- `step_type`
- `retry_policy`

### 9.3 需要移出模板执行层的部分

以下字段不建议继续作为执行层主字段：

- `supported_annotation_types`
- `supported_shapes`

这些应转移为业务层可见的场景元数据，由 `automl_server` 来决定哪些模板对哪个标注项目可用。

### 9.4 推荐模板结构

```json
{
  "template_key": "onnx_bbox_assist",
  "scene_type": "assist_annotation",
  "input_schema": {
    "kind": "image"
  },
  "output_schema": {
    "kind": "annotation_bbox"
  },
  "resource_slots": {
    "detector_model": {
      "resource_type": "onnx_model",
      "task_kind": "detection_bbox",
      "required": true
    }
  },
  "steps": [
    {
      "key": "detect",
      "step_type": "resource",
      "resource_ref": "detector_model",
      "executor": "invoke_model_resource",
      "input_key": "input",
      "output_key": "detections"
    }
  ]
}
```

### 9.5 动态输入、运行参数、资源绑定要分层

你提到的 `prompt` 动态化是对的，但不建议简单把所有动态内容都继续塞进现在的 `params`。

推荐把一次 pipeline 执行请求拆成三层：

1. `data_inputs`
2. `runtime_inputs`
3. `resource_bindings`

含义如下：

- `data_inputs`
  - 代表数据本身，例如图片、视频、文本、overlay 图、样本引用
- `runtime_inputs`
  - 代表这次执行的可变业务输入，例如 `prompt`、类别列表、阈值、是否启用某个开关
- `resource_bindings`
  - 代表资源槽位绑定，例如当前使用哪个 ONNX 模型、哪个多模态 provider

这里最关键的边界是：

- `step.params`
  - 用来放模板内部稳定参数
- `runtime_inputs`
  - 用来放用户、项目、运行时可变参数

因此建议：

- `prompt` 默认作为 `runtime_inputs` 字段，而不是硬编码在模板里
- 只有极少量稳定 system prompt 或 executor 内部默认值，才保留在模板定义中

这样做的好处：

- 同一个 pipeline 模板可以适配不同项目和不同 prompt 风格
- 后续可以支持“项目默认 prompt + 运行时覆盖”
- 前后端都能围绕 schema 做统一渲染和校验

### 9.6 推荐的输入 schema 结构

为了支撑不同 pipeline 的动态配置，模板版本中的 `definition_json` 需要包含一组明确的字段定义，而不是只放执行步骤。

推荐结构：

```json
{
  "template_key": "multimodal_assist_with_detector",
  "scene_type": "assist_annotation",
  "data_inputs": [
    {
      "key": "primary_image",
      "label": "输入图片",
      "value_type": "image",
      "required": true,
      "source_type": "asset_ref"
    },
    {
      "key": "reference_image",
      "label": "参考图片",
      "value_type": "image",
      "required": false,
      "source_type": "asset_ref"
    }
  ],
  "runtime_inputs": [
    {
      "key": "user_prompt",
      "label": "提示词",
      "value_type": "string",
      "required": false,
      "default_value": "",
      "multiline": true
    },
    {
      "key": "target_classes",
      "label": "目标类别",
      "value_type": "string_array",
      "required": false
    },
    {
      "key": "score_threshold",
      "label": "置信度阈值",
      "value_type": "number",
      "required": false,
      "default_value": 0.25
    }
  ],
  "resource_slots": {
    "detector_model": {
      "resource_type": "onnx_model",
      "task_kind": "detection_bbox",
      "required": true
    },
    "vision_provider": {
      "resource_type": "multimodal_provider",
      "required": false
    }
  }
}
```

这套结构里：

- 图片、视频、文本等“原始输入”走 `data_inputs`
- `prompt`、阈值、开关、类别等“动态业务参数”走 `runtime_inputs`
- 模型、provider、OCR 等走 `resource_slots`

这样就不会把“数据输入”和“表单配置”混成一团。

### 9.7 Prompt 的推荐设计

`prompt` 不建议只作为一个裸字符串字段。

推荐支持三种层级：

1. 模板默认值
2. 项目级默认值
3. 运行时覆盖值

优先级建议：

- `runtime override > project binding default > template default`

这样一个标注项目可以给某条 pipeline 预设一段 prompt，但当前用户在执行时仍然可以临时调整。

对于 prompt 字段，建议额外支持这些属性：

- `placeholder`
- `multiline`
- `max_length`
- `supports_variables`
- `variable_definitions`

例如：

```json
{
  "key": "user_prompt",
  "label": "提示词",
  "value_type": "string",
  "multiline": true,
  "supports_variables": true,
  "variable_definitions": [
    "annotation_classes",
    "dataset_name",
    "sample_item_key"
  ]
}
```

这样后续可以支持：

- 在 prompt 中引用项目类别
- 在 prompt 中引用样本上下文
- 在项目级模板里做一定程度的复用

但首期不建议上复杂表达式引擎，变量替换保持简单、白名单化即可。

### 9.8 前后端联动必须走 schema 驱动

如果后续每种 pipeline 都单独写一套页面组件，前后端会很快变成：

- 后端写模板
- 前端再手写一套专属配置页面
- 新增一种 pipeline 又写一套 `if/else`

这条路不可持续。

推荐方案：

- 后端返回模板详情时，带回完整的 `data_inputs / runtime_inputs / resource_slots / ui_schema`
- 前端维护一个“字段渲染器注册表”，按 schema 渲染表单

也就是：

- pipeline 是动态的
- 表单也是动态的
- 前端不按 pipeline 名称写分支，而按字段类型和 widget 类型渲染

### 9.9 推荐的前端字段组件模型

首期建议前端只实现一组有限但通用的组件：

- `text`
- `textarea`
- `number`
- `switch`
- `select`
- `multi-select`
- `resource-select`
- `image-asset-picker`
- `video-asset-picker`
- `json-editor`

字段 schema 建议至少包含：

- `key`
- `label`
- `value_type`
- `required`
- `default_value`
- `description`
- `widget`
- `widget_props`

例如 ONNX 模型绑定字段可以这样返回：

```json
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
```

这样前端就能知道：

- 这是下拉组件
- 数据源不是写死的，而是资源列表接口
- 需要过滤成 `onnx_model + detection_bbox + 已部署`

### 9.10 多模态输入组件要抽象成内容项，而不是只做“图片 + prompt”

你提到“设计多模态的可能需要支撑图文”，这个判断也成立。

因此不建议把多模态 pipeline 的输入永远写死成：

- 一张图片
- 一个 prompt

更合理的抽象是：

- 一个或多个 `content items`

例如：

```json
{
  "key": "multimodal_context",
  "label": "多模态输入",
  "value_type": "content_items",
  "required": true,
  "widget": "multimodal-composer",
  "widget_props": {
    "allowed_item_types": ["text", "image"],
    "max_items": 4
  }
}
```

这样后续同一个执行框架就能支持：

- 单图 + 文本提示
- 多图对比
- 图 + 文 + 参考图
- 视频封面图 + 文本说明

首期前端如果不想一下做太重，可以先收敛成：

- `primary_image`
- `reference_image`
- `user_prompt`

但后端 schema 建议按“可扩展为 content items”的方向建模，不要把模型锁死。

### 9.11 后端接口建议

为了支撑 schema 驱动前端，建议新增一个模板表单描述接口：

- `GET /v1/pipeline-templates/{template_key}/form-schema`

返回内容建议包含：

- 模板基础信息
- `data_inputs`
- `runtime_inputs`
- `resource_slots`
- `ui_schema`
- 默认值
- 允许的资源过滤条件

而真正执行时的请求结构建议收敛为：

```json
{
  "template_key": "multimodal_assist_with_detector",
  "data_inputs": {
    "primary_image": {
      "asset_id": 123,
      "sample_item_id": 456
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
  }
}
```

这样就把：

- 数据
- 动态参数
- 资源选择

三个来源彻底拆开了。

## 10. 运行模式设计

### 10.1 短任务同步模式

适用场景：

- 单张图片辅助标注
- 小型图像理解
- 响应时间要求较高的交互式操作

推荐链路：

- `automl_server` 通过 HTTP 调用 `ai_pipeline`
- `ai_pipeline` 同步执行
- 返回最终结果

为什么这里不用 MQ：

- HTTP 更直接
- 超时、错误、调用链更清晰
- 与现有前端交互模型更一致

### 10.2 长任务异步模式

适用场景：

- 视频标注 pipeline
- 大批量图像处理
- 多步骤耗时 pipeline

推荐链路：

1. `automl_server` 创建 run 请求
2. `ai_pipeline` 持久化 `run`
3. 投递内部异步任务
4. worker 执行 pipeline
5. 通过 MQ 发送状态事件
6. 结果写入 MinIO 和数据库

MQ 在这里适合做：

- 任务派发
- 状态事件
- 进度广播
- 失败通知

不适合做：

- 长时间同步等待的 request-reply

## 11. 视频场景为什么必须改调用模型

视频 pipeline 至少会涉及：

- 视频解码
- 帧采样
- 帧级推理
- 时序聚合
- 结果导出

这意味着：

- 输入文件更大
- 执行时间更长
- 中间产物更多
- 更需要进度与恢复

如果继续沿用当前同步 MQ RPC 模式，会直接遇到：

- 超时管理困难
- 回调队列长时间占用
- 任务中断后无法恢复
- 前端无法观察处理中间态

因此视频场景应天然走：

- `run_id`
- `artifact ref`
- `async execution`

而不是继续走“调用后等待完整返回”。

## 12. 配置设计建议

### 12.1 保留在 Nacos 的内容

- MySQL / RabbitMQ / MinIO 基础配置
- `ai_pipeline` 服务地址
- provider 基础配置
- 默认超时、重试等运行参数

### 12.2 迁移到数据库的内容

- pipeline 模板
- pipeline 模板版本
- 业务绑定关系
- 资源绑定关系
- run 记录
- step 记录
- artifact 元数据

### 12.3 不建议继续放在 Nacos 的内容

- 具体业务 pipeline 列表
- 项目默认 pipeline
- pipeline 的资源绑定

## 13. 迁移方案

推荐采用三阶段迁移。

### Phase 1：数据库承接模板，但保持兼容

目标：

- 新增 `ai_pipeline_*` 表
- 写一个迁移脚本，把当前 Nacos 中的 pipeline 定义导入数据库
- `ai_pipeline` 启动时优先查数据库，数据库为空时再回退 Nacos

这样可以保证：

- 首期不阻塞当前功能
- 可以先验证数据库模板模型是否合理

### Phase 2：主服务切换到数据库模板管理

目标：

- `automl_server` 新增 pipeline 管理接口
- 标注项目从“只存 `assist_pipeline` 字符串”升级为“存 binding”
- 首页、标注页都改为从数据库模板读取

### Phase 3：移除 Nacos 中的 pipeline 业务定义

目标：

- Nacos 仅保留基础配置
- pipeline 业务模板完全数据库化

## 14. 与现有表的关系

首期不建议直接大改现有 `annotation` 表，只建议增量兼容。

### 14.1 当前字段保留

当前 `annotation.assist_pipeline` 可以先保留，作为兼容字段。

### 14.2 新增字段建议

后续建议新增：

- `annotation.assist_pipeline_binding_id`

或更通用一点：

- `annotation.default_ai_pipeline_binding_id`

首期兼容策略：

- 新建项目优先写新 binding
- 老字段继续可读
- 数据迁移完成后再考虑清理老字段

## 15. 对现有代码结构的建议

### 15.1 子服务目录

建议新目录直接叫：

- `ai_pipeline/`

而不是继续在 `auto_augment_pipeline/` 里叠加。

原因：

- 服务定位已经变化
- 后续视频能力加入后，旧命名会持续误导

### 15.2 主服务模块

建议在 `automl_server` 中新增专门模块：

- `app/modules/ai_pipeline/`

负责：

- 模板管理
- binding 管理
- run 查询
- 业务侧触发

### 15.3 运行接口建议

建议 `ai_pipeline` 对外暴露：

- `POST /v1/pipeline-runs/sync`
- `POST /v1/pipeline-runs`
- `GET /v1/pipeline-runs/{run_id}`
- `GET /v1/pipeline-templates`
- `GET /v1/pipeline-templates/{template_key}`

## 16. 首期推荐实现范围

首期建议严格收敛到下面这几个点：

1. 完成 `ai_pipeline` 命名与职责重构设计
2. 新增数据库表结构
3. 将 pipeline 模板从 Nacos 迁到数据库
4. 接入 ONNX 模型资源槽位
5. 保留单图同步执行
6. 为视频和批量任务预留异步 run 模型

首期不建议同时做：

- 可视化编排器
- 全量资源市场
- 任意 DAG 引擎
- 跨服务大规模重构

## 17. 关键结论

### 17.1 关于数据库

推荐结论：

- 不共用主服务的连接池
- 共用同一个 MySQL 实例与同一个 `auto_ml` 库
- 通过 `ai_pipeline_*` 独立表隔离

也就是：

- 独立服务连接
- 同库分表

这是当前项目阶段最稳的方案。

### 17.2 关于 Nacos

推荐结论：

- Nacos 保留为基础配置中心
- pipeline 模板和绑定关系迁移到数据库

也就是：

- `Nacos -> infra config`
- `Database -> business template metadata`

### 17.3 关于调用方式

推荐结论：

- 单图短任务：HTTP 同步
- 视频/批量长任务：异步 run + MQ 事件

不再继续把 MQ request-reply 作为主调用模型。

### 17.4 关于重构方向

推荐结论：

- `auto_augment_pipeline` 应升级为 `ai_pipeline`
- 首期先把“模板、绑定、运行态”做对
- 不急着先做大而全的工作流产品形态

这条路径和你当前项目现状最匹配，也最适合后续接入视频标注、模型资源化和更通用的 AI 工作流能力。
