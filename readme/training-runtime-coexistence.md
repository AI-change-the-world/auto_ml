# 内置训练与自定义训练脚本共存方案

## 当前实现

| 用户选择 | 训练后端 | 队列 | 能否部署推理 |
| --- | --- | --- | --- |
| 内置基础模型、数据集、标注集 | `model_trainer` | `trainer.task.queue` | 保持现有逻辑 |
| 上传的训练脚本 ZIP、可选模型 ZIP、平台数据集/标注集 | `model_training_runtime` | `training.code.execute` | 仅合规 ONNX |
| 上传的训练脚本 ZIP、脚本自行下载或生成数据 | `model_training_runtime` | `training.code.execute` | 仅合规 ONNX |

训练脚本 ZIP 是运行逻辑，不是旧训练器的基础模型。因此它不进入 `base_models`，
也不会出现在内置训练的模型选择中。运行时模型 ZIP 是自定义脚本的可选输入，
同样不交给 `model_trainer`。

自定义脚本产生的检查点也不会出现在内置训练的“历史继续训练”候选中；它只能由
兼容的自定义脚本作为初始化模型或恢复检查点再次选择。

## 用户操作

在“模型管理”的外部页签导入：

- **训练脚本包**：根目录包含 `training_package.json` 和 `train.py`，声明
  运行时、支持任务、参数、输入模式和输出产物。
- **初始化模型包**：根目录包含 `training_model_package.json`，提供自定义
  脚本可选的初始化权重或可恢复检查点。

在训练任务弹窗选择“自定义脚本训练”后：

- `platform_dataset`：提交数据集 ID 与标注集 ID 给主服务。主服务解析、校验
  并冻结为对象存储快照；脚本不获取数据库 ID 或 S3 凭据。
- `script_managed`：不提交数据集或标注集 ID，只提交类别、模态和脚本参数；
  脚本自行获取数据。例如提供的 PyTorch 猫狗示例会下载 CIFAR-10。

运行时只接受 `cpu` 和 `cuda`。脚本包声明的 `runtime.id` 必须出现在 Nacos
`execution.runtime_ids` 白名单中，主服务和 worker 都会在执行前校验。

主服务创建 `Task` 与 `training_runtime_execution`，冻结
`training-code-submit/v1` 后投递专用队列。runtime worker 执行
`train(context, report)`，回写日志、运行状态和终态结果；验证后的产物会先持久化，
再清理单次工作目录。

## 推理边界

成功脚本包只能将声明为 `deployable: true` 的 ONNX 模型登记为 `AvailableModel`。
当前只接受与现有分类或检测推理模板兼容的任务类型。`.pt` 权重和训练检查点可以
作为后续自定义训练输入，但不能直接进入部署列表。

## 启用条件

自定义训练默认关闭。Nacos 中需同时设置：

```yaml
model-training-runtime:
  enabled: true
  base_url: http://model-training-runtime:8012
  allow_script_managed_data: false
  execution:
    enabled: true
    runtime_ids:
      - ultralytics-8.3.0-pytorch-2.5-cu124
      - pytorch-2.5-cu124
```

`script_managed` 还要求 `allow_script_managed_data: true`。该开关只控制平台
入口与 worker 校验，不等同于网络隔离：需要下载数据的脚本必须通过容器/网络策略
显式允许所需出站地址；普通平台数据集训练应保持无出站访问。

## 当前限制

- 用户脚本在 runtime 容器的受限子进程中执行，带超时、输出、进程、内存和文件
  限制，但这不是多租户安全边界。生产环境应进一步使用隔离容器或 Job，并配置
  CPU/GPU 配额和 egress allowlist。
- 自定义训练尚未提供取消协议；运行中的自定义任务不能删除，避免错误调用旧
  `model_trainer` 的取消接口。
- worker 使用 `prefetch=1` 串行消费；多并发和 GPU 调度应在引入 Job 调度器时
  明确实现。
