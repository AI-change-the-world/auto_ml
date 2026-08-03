# 内置训练与自定义训练脚本共存方案

## 已确认的边界

| 用户选择的内容 | 训练后端 | 是否进入 `model_trainer` |
| --- | --- | --- |
| 内置基础模型、数据集、标注集与现有 Ultralytics 参数 | `model_trainer` | 是 |
| 用户上传的训练脚本 ZIP、运行时模型 ZIP、数据集、标注集与脚本参数 | `model_training_runtime` | 否 |

训练脚本 ZIP 声明的是运行逻辑，不是旧训练器能够加载的“模型”。即使它
包含 Ultralytics 代码或 `.pt` 文件，也不得写入 `base_models`，不得出现在
旧训练弹窗的基础模型下拉框，也不得投递到现有 `trainer.task.queue`。

## 第一阶段：运行时包目录（已实现）

`automl_server` 新增独立的目录 API：

- `POST /training-runtime/code-packages/import`：将含 `training_package.json`
  的 ZIP 交给 runtime 校验、不可变存储和登记。
- `POST /training-runtime/model-packages/import`：将含
  `training_model_package.json` 的 ZIP 交给 runtime 处理初始化权重和可选
  可恢复检查点。
- `GET /training-runtime/code-packages` 与
  `GET /training-runtime/model-packages`：仅供未来的“自定义脚本训练”模式选择。

主服务将 runtime 返回的 digest、对象路径、框架、模型输入约束、参数
schema 和产物约束持久化到专用的 `training_runtime_code_package` 与
`training_runtime_model_package` 表中。它们不关联 `base_models`；导入不会
创建训练任务、发布 MQ 消息或执行脚本。

先执行 `mysql/migrations/20260803_add_training_runtime_catalog.sql`，并配置
`AUTO_ML_CONFIG.model-training-runtime` 的 `enabled`、`base_url` 和可选
`token`。目录导入会复用 runtime 的受控 ZIP 校验，而不在控制面解压或执行
用户代码。

## 后续实施顺序

1. 增加独立的“自定义脚本训练”入口（页面/表单），默认仍进入内置训练。
   该入口只展示运行时脚本包和运行时模型包；旧训练页不变化。
2. 新建 `training_backend=code_package` 的任务记录，持久化选择的包版本、
   digest、模型输入模式、数据集来源、资源申请和脚本参数快照。不要复用
   legacy `Task` 的 `config` 来隐式判断后端。
3. 创建任务时复用已有的数据源解析，调用
   `/task/training-dataset-snapshot/register` 得到不可变数据快照；根据脚本
   `model_input_contract` 校验模型的框架、格式、任务类型、类别与
   initialize/resume 模式。
4. 由专用生产 worker 消费独立 routing key，并构造
   `training-code-submit/v1`。worker 按 `execution_id` 幂等领取任务、限制
   并发/资源、支持取消与重试，并将事件、日志和最终状态回写主服务。
5. 验证并登记 runtime 产物为可部署模型；仅在产物适配现有部署协议时写入
   `AvailableModel`。这与输入的运行时模型包目录是两件事。

### 自定义训练提交的数据边界

自定义训练表单可以像内置训练一样让用户选择 `dataset_id` 与
`annotation_id`（或多个来源），但这些 ID 只提交给 `automl_server` 用于
权限校验、查询当前数据与创建平台任务记录。主服务必须将选择解析成数据集
和标注 bucket 的对象引用，再登记为带 SHA-256 与大小的不可变
`dataset_source_snapshot`。

最终投递给 runtime worker 的 `training-code-submit/v1` 不包含
`dataset_id` 或 `annotation_id`。它包含：平台 `task.task_id`、已登记脚本包
的 key/version/SHA-256 与 archive 引用、`dataset_source_snapshot` 的对象
引用、runtime ID、已校验的脚本参数和资源配置，以及可选的运行时模型产物
引用。用户脚本只能读取 worker 物化后的数据，不读取数据库，也不获得 S3
凭据。

## 当前限制

runtime 目前的 `/v1/executions/run` 是同步的实验验证接口，不能用于长时间
生产训练。目录登记已可用，但“自定义脚本训练”任务在专用异步 worker 和
完整生命周期实现之前不应开放创建。内置训练不需要迁移或停机。
