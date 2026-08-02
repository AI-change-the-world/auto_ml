# AutoML Server

`automl_server` 是平台的主业务 API 和编排服务。前端的大部分页面只直接访问它；它再把 MySQL、MinIO、RabbitMQ、Nacos 以及训练、部署、AI 能力、批量标注沙箱串成一条完整链路。

## 服务职责

- 数据集、样本、资产和预览链接管理
- 标注项目、标注记录和多种标注类型的保存
- 训练任务、部署任务、推理入口的统一编排
- AI Pipeline 模板、资源绑定和能力调用
- 批量标注工具包上传、任务切分、事件流、结果落库和重试

## 目录结构

```text
automl_server/
├── app/
│   ├── common/      # 通用响应、异常、常量
│   ├── config/      # settings、数据库、S3、Nacos
│   ├── db/          # SQLAlchemy 模型与会话
│   ├── modules/     # dataset / annotation / task / deploy / ai_pipeline 等业务模块
│   ├── mq/          # RabbitMQ publisher、consumer、handler
│   ├── scheduler/   # 定时任务
│   └── utils/       # S3、SSE、HTTP、标注工具函数
├── run.py
├── requirements.txt
└── Dockerfile
```

## 对外接口

- 健康检查：`/health`
- Swagger：`/swagger-ui`
- 主要业务分组：
  - `/dataset*`
  - `/annotation*`
  - `/task*`
  - `/deploy*`
  - `/inference*`
  - `/ai-pipeline*`

其中批量标注相关接口集中在：

- `/ai-pipeline/batch-scripts*`
- `/ai-pipeline/batch-runs*`

## 批量标注链路

`automl_server` 在批量标注中承担控制面职责，具体包括：

1. 上传脚本包时解析 ZIP 根目录的 `batch_script.json`，并持久化可选的 `README.md`
2. 创建任务时冻结脚本版本、入口、参数快照，并把样本切成多个 chunk 发送到 `pipeline.batch.execute`
3. 消费 `pipeline.batch.progress` 和 `pipeline.batch.result`，更新任务进度、事件时间线和样本状态
4. 保存成功样本的标注记录，并为结果预览生成原图 presigned URL
5. 提供继续执行、仅重试失败项、按原配置处理新增样本、删除已结束任务等能力

脚本 `secret` 参数会先在主服务数据库中加密保存，只在本次下发 MQ 消息时解密。加密密钥读取 Nacos 的 `ai-pipeline-batch.secret_key`。

## 依赖关系

- MySQL：主数据持久化
- MinIO：数据集、模型、标注和脚本 ZIP 存储
- RabbitMQ：训练、AI Pipeline RPC、批量标注和部署状态同步
- Nacos：统一运行配置
- `model_trainer`：训练插件服务
- `model_deploy`：部署与推理插件服务
- `ai_pipeline_runtime`：AI 能力运行时
- `ai_pipeline_sandbox`：批量标注脚本执行服务

## 实验训练数据快照

`POST /task/training-dataset-snapshot/preview` 是给
`training_code_runtime` 准备的只读预览接口。它复用现有的训练数据源
校验，输出 `training-dataset-source-manifest/v1`：数据集资产映射到
datasets bucket，已持久化标注记录映射到 annotations bucket。

该接口当前不会读取 S3 对象正文、创建训练任务、写入数据库或发布 MQ。
返回的 manifest 尚未固定对象哈希；后续由实验运行时的
`/v1/registrations/dataset-snapshots` 使用 OpenDAL 校验内容并登记为不可变
快照。它拒绝未声明字段及重复的“数据集 + 标注”来源，避免预览把同一
样本集重复交给未来运行时；旧的 `POST /task/train` 与 `model_trainer` 流程
完全不变。

只有在 Nacos 的 `AUTO_ML_CONFIG` 中显式配置 `training-code-runtime` 的
`enabled`、`base_url`、`timeout` 和可选 `token` 后，
`POST /task/training-dataset-snapshot/register` 才会调用实验运行时，读取对象
并返回固定 SHA-256 的快照引用。`token` 以 Bearer Token 传给运行时。登记
相同的对象版本是幂等的（`created=false`）；对象内容变化会生成新的快照。
登记本身仍不会创建任务、写主库、发布 MQ 或执行训练代码。

## 服务通信

- 训练：
  - 主服务通过 RabbitMQ 发布 `trainer.task.submit`
  - `model_trainer` 通过 RabbitMQ 回传 `task.status.update`、`task.log`、`model.registered`
  - 主服务通过 HTTP 调用 `model_trainer` 的 `/health` 和 `/tasks/{task_id}/cancel`
- 部署：
  - 主服务通过 HTTP 调用 `model_deploy` 的 `/deploy`、`/undeploy`、`/deployments`、`/deploy/{model_id}/health`
  - `model_deploy` 通过 RabbitMQ 回传 `model.deployed`、`model.undeployed`
- AI Pipeline Runtime：
  - 当前辅助标注和 pipeline 调用走 RabbitMQ RPC
- 批量标注：
  - 主服务通过 RabbitMQ 发布 `pipeline.batch.execute`
  - `ai_pipeline_sandbox` 通过 RabbitMQ 回传 `pipeline.batch.progress`、`pipeline.batch.result`

当前代码中虽然保留了 `service.heartbeat` 消息类型定义，但训练和部署服务没有实际启用单独的 MQ 心跳；页面显示的服务状态，当前来自主服务按需调用对应服务的 `/health`。

## 配置

主要配置入口：

- `app/config/settings.py`
- `app/config/rabbitmq_config.py`
- `app/config/s3_config.py`
- `app/config/nacos_config_center.py`

配置来源优先级：

1. Nacos `AUTO_ML_CONFIG`
2. 本地环境变量
3. 代码内默认值

批量标注相关重点配置：

- `rabbitmq.queues.pipeline_batch_*`
- `rabbitmq.routing_keys.pipeline_batch_*`
- `ai-pipeline-batch.secret_key`
- `local-s3-config`

## 本地运行

```bash
cd automl_server
pip install -r requirements.txt
python run.py
```

默认监听：

- Host：`0.0.0.0`
- Port：`45678`

本地直跑时可结合 `automl_server/.env.example` 和根目录 `.env.example` 提供环境变量。

## 相关文档

- [主服务架构说明](./ARCHITECTURE.md)
- [前端工作台 README](../frontend_v2/README.md)
- [批量标注沙箱 README](../ai_pipeline_sandbox/README.md)
