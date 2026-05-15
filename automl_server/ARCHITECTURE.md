# AutoML 主服务 - Python 重构架构说明

## 1. 项目概述

将原有 Java Spring Boot 主服务迁移到 Python FastAPI 实现，保持与现有微服务（model_trainer、model_deploy）的兼容性。

### 1.1 技术栈

| 组件 | Java 原实现 | Python 新实现 |
|------|------------|---------------|
| Web框架 | Spring Boot 3.3 | FastAPI |
| ORM | MyBatis Plus | SQLAlchemy 2.0 |
| 数据库连接池 | HikariCP | SQLAlchemy AsyncIO |
| 配置中心 | Nacos | nacos-sdk-python |
| 对象存储 | OpenDAL | boto3 / aioboto3 |
| HTTP客户端 | OkHttp | httpx (async) |
| 消息队列 | - | pika (RabbitMQ) |
| SSE推送 | SseEmitter | sse-starlette |
| API文档 | Swagger | FastAPI Swagger |
| 日志 | Logback | loguru |

### 1.2 服务端口

- 主服务端口：45678
- 上下文路径：`/automl`

---

## 2. 模块架构

```
automl_server/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用入口
│   ├── config/                     # 配置层
│   │   ├── __init__.py
│   │   ├── settings.py             # 全局配置 (Nacos + 环境变量)
│   │   ├── database.py             # 数据库配置
│   │   ├── s3_config.py            # S3/MinIO 配置
│   │   └── rabbitmq_config.py      # RabbitMQ 配置
│   │
│   ├── common/                     # 通用组件
│   │   ├── __init__.py
│   │   ├── response.py             # 统一响应格式 Result
│   │   ├── pagination.py           # 分页请求/响应
│   │   ├── exceptions.py           # 自定义异常
│   │   └── constants.py            # 常量定义
│   │
│   ├── db/                         # 数据库层
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy Base
│   │   ├── session.py              # 数据库会话管理
│   │   └── models/                 # 数据模型 (按模块组织)
│   │       ├── __init__.py
│   │       ├── base_entity.py      # 基础实体 (id, created_at, updated_at, is_deleted)
│   │       ├── dataset.py          # Dataset, Asset, SampleItem
│   │       ├── annotation.py       # Annotation, AnnotationRecord
│   │       ├── task.py             # Task, TaskLog, BaseModels
│   │       ├── predict.py          # PredictTask, PredictData
│   │       ├── deploy.py           # AvailableModel
│   │       └── tool.py             # ToolModel
│   │
│   ├── modules/                    # 业务模块
│   │   ├── __init__.py
│   │   │
│   │   ├── dataset/                # 数据集管理模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # API 路由
│   │   │   ├── service.py          # 业务逻辑
│   │   │   ├── schemas.py          # Pydantic 模型 (DTO)
│   │   │   └── crud.py             # 数据库操作
│   │   │
│   │   ├── annotation/             # 标注管理模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── crud.py
│   │   │
│   │   ├── task/                   # 任务管理模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py          # 与 model_trainer 通信
│   │   │   ├── schemas.py
│   │   │   └── crud.py
│   │   │
│   │   ├── predict/                # 预测模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py           # 包含 SSE 端点
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── crud.py
│   │   │
│   │   ├── deploy/                 # 模型部署模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py          # 与 model_deploy 通信
│   │   │   ├── schemas.py
│   │   │   └── crud.py
│   │   │
│   │   ├── tool/                   # 工具模型模块
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── crud.py
│   │   │
│   │   ├── augment/                # 数据增强与质量评估
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── schemas.py
│   │   │
│   │   └── home/                   # 首页统计
│   │       ├── __init__.py
│   │       ├── router.py
│   │       └── service.py
│   │
│   ├── mq/                         # RabbitMQ 消息队列
│   │   ├── __init__.py
│   │   ├── client.py               # RabbitMQ 客户端
│   │   ├── consumer.py             # 消息消费者 (监听 trainer/deploy)
│   │   └── handlers/               # 消息处理器
│   │       ├── __init__.py
│   │       ├── task_status.py      # 任务状态更新处理
│   │       ├── task_log.py         # 任务日志处理
│   │       ├── model_registered.py # 模型注册处理
│   │       └── model_deployed.py   # 模型部署处理
│   │
│   ├── utils/                      # 工具类
│   │   ├── __init__.py
│   │   ├── s3_delegate.py          # S3/MinIO 操作封装
│   │   ├── presigned_cache.py      # 预签名URL缓存
│   │   ├── file_utils.py           # 文件处理工具
│   │   ├── sse_util.py             # SSE 工具
│   │   └── http_client.py          # 异步 HTTP 客户端
│   │
│   └── scheduler/                  # 定时任务
│       ├── __init__.py
│       └── heartbeat.py            # 心跳检查任务
│
├── tests/                          # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   └── modules/
│       ├── test_dataset.py
│       ├── test_task.py
│       └── ...
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 3. 核心模块说明

### 3.1 数据集管理 (dataset)

**功能**：
- 数据集 CRUD 操作
- 文件上传到 S3/MinIO
- 数据集预览（预签名URL）
- 数据集导出为 ZIP
- 文件列表获取

**实体**：
```python
class Dataset(BaseEntity):
    name: str               # 数据集名称
    storage_type: int       # 存储类型 (0=本地, 1=S3, 2=WebDAV)
    data_type: int          # 数据类型 (0=图像, 1=文本, 2=视频, 3=音频)
    save_path: str          # S3 路径
    count: int              # 样本数量
    description: str        # 描述

class Asset(BaseEntity):
    dataset_id: int
    asset_type: str
    file_name: str
    save_path: str

class SampleItem(BaseEntity):
    dataset_id: int
    asset_id: int
    item_type: str
    item_key: str
    payload: str
```

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| POST | /dataset/new | 创建数据集 |
| GET | /dataset/list | 分页查询数据集 |
| GET | /dataset/{id} | 获取数据集详情 |
| DELETE | /dataset/{id} | 删除数据集 |
| POST | /dataset/{id}/upload | 上传文件 |
| GET | /dataset/{id}/samples | 获取样本列表 |
| POST | /dataset/{id}/samples | 创建样本 |
| GET | /dataset/{id}/samples/{sample_id}/preview | 预览样本资源 |

---

### 3.2 标注管理 (annotation)

**功能**：
- 标注项目 CRUD
- 标注记录管理
- 支持多种标注类型（检测、分类、分割）

**实体**：
```python
class Annotation(BaseEntity):
    name: str               # 标注项目名称
    annotation_type: int    # 标注类型 (0=检测, 1=分类, 2=分割)
    classes: str            # 分类项 JSON
    storage_type: int       # 存储类型
    save_path: str          # 存储路径
    prompt: str             # AI 标注提示词
    dataset_id: int         # 关联数据集

class AnnotationRecord(BaseEntity):
    annotation_id: int
    sample_item_id: int
    annotation_type: int
    status: str
    content: str            # 标注内容 JSON
```

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| POST | /annotation/new | 创建标注项目 |
| GET | /annotation/list | 分页查询标注项目 |
| GET | /annotation/{id} | 获取标注详情 |
| DELETE | /annotation/{id} | 删除标注项目 |
| GET | /annotation/{id}/records | 获取标注记录 |
| POST | /annotation/{id}/records | 保存标注记录 |

---

### 3.3 任务管理 (task)

**功能**：
- 创建训练任务
- 任务状态追踪
- 任务日志管理
- 基础模型管理
- 通过 RabbitMQ 接收 model_trainer 消息

**实体**：
```python
class Task(BaseEntity):
    task_type: int          # 任务类型 (0=检测, 1=分类)
    dataset_id: int         # 数据集 ID
    annotation_id: int      # 标注 ID  
    status: int             # 状态 (0=待处理, 1=运行中, 2=后处理, 3=完成, 4=失败)
    config: str             # 配置 JSON
    result: str             # 结果 JSON

class TaskLog(BaseEntity):
    task_id: int
    content: str            # 日志内容
    log_level: str          # 日志级别

class BaseModels(BaseEntity):
    name: str               # 模型名称
    model_type: str         # 模型类型
    description: str        # 描述
```

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| POST | /task/train | 创建训练任务 |
| GET | /task/list | 分页查询任务 |
| GET | /task/{id} | 获取任务详情 |
| GET | /task/{id}/logs | 获取任务日志 |
| GET | /task/base-models | 获取基础模型列表 |

**RabbitMQ 消息处理**：
- `task.status.update` → 更新任务状态
- `task.log` → 写入任务日志
- `model.registered` → 注册新模型到 AvailableModel

---

### 3.4 预测模块 (predict)

**功能**：
- 预测任务管理
- 视频处理（帧提取、推理）
- SSE 实时推送处理进度
- 预测结果存储

**实体**：
```python
class PredictTask(BaseEntity):
    task_type: str          # 任务类型
    source: str             # 输入源
    result: str             # 结果
    status: int             # 状态

class PredictData(BaseEntity):
    predict_task_id: int
    data: str               # 预测数据
```

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| POST | /predict/video | 视频处理（SSE）|
| POST | /predict/image | 图像预测 |
| GET | /predict/{id}/result | 获取预测结果 |
| GET | /predict/list | 预测任务列表 |

---

### 3.5 模型部署 (deploy)

**功能**：
- 可用模型管理
- 模型部署/卸载
- 与 model_deploy 服务通信
- 通过 RabbitMQ 接收部署状态

**实体**：
```python
class AvailableModel(BaseEntity):
    name: str               # 模型名称
    model_path: str         # 模型路径
    model_type: str         # 模型类型
    dataset_id: int         # 关联数据集
    loss: float             # 训练损失
    is_deployed: bool       # 是否已部署
    deployment_id: str      # 部署 ID
```

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| GET | /deploy/models | 获取可用模型列表 |
| POST | /deploy/{model_id}/deploy | 部署模型 |
| POST | /deploy/{model_id}/undeploy | 卸载模型 |
| GET | /deploy/{model_id}/status | 获取部署状态 |

**RabbitMQ 消息处理**：
- `model.deployed` → 更新模型部署状态
- `model.undeployed` → 更新模型卸载状态

---

### 3.6 工具模型 (tool)

**功能**：
- 工具模型注册和管理
- 第三方模型集成

**实体**：
```python
class ToolModel(BaseEntity):
    name: str
    model_type: str
    endpoint: str           # 服务端点
    config: str             # 配置 JSON
```

---

### 3.7 数据增强与质量评估 (augment)

**功能**：
- 调用 auto_augment_pipeline 服务
- 图像增强处理
- 质量评估

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| POST | /augment/process | 数据增强处理 |
| GET | /augment/capabilities | 获取可用能力 |

---

### 3.8 首页统计 (home)

**功能**：
- 数据集统计
- 任务统计
- 模型统计
- 系统状态概览

**API 端点**：
| Method | Path | Description |
|--------|------|-------------|
| GET | /home/stats | 获取统计数据 |

---

## 4. 消息队列集成 (RabbitMQ)

### 4.1 Exchange 和 Queue 设计

```yaml
Exchange: auto_ml_exchange (topic)

Queues:
  - auto_ml.task.status      # 任务状态更新
  - auto_ml.task.log         # 任务日志
  - auto_ml.model.registered # 模型注册
  - auto_ml.model.deployed   # 模型部署
  - auto_ml.model.undeployed # 模型卸载
  - auto_ml.heartbeat        # 服务心跳

Routing Keys:
  - task.status.update
  - task.log
  - model.registered
  - model.deployed
  - model.undeployed
  - service.heartbeat
```

### 4.2 消息消费者

```python
# app/mq/consumer.py
class MessageConsumer:
    """
    消费来自 model_trainer 和 model_deploy 的消息
    将数据写入数据库
    """
    
    async def on_task_status_update(self, message: TaskStatusMessage):
        # 更新 Task 表状态
        
    async def on_task_log(self, message: TaskLogMessage):
        # 写入 TaskLog 表
        
    async def on_model_registered(self, message: ModelRegisteredMessage):
        # 写入 AvailableModel 表
        
    async def on_model_deployed(self, message: ModelDeployedMessage):
        # 更新 AvailableModel 部署状态
```

---

## 5. S3/MinIO 存储设计

### 5.1 Bucket 规划

| Bucket | 用途 |
|--------|------|
| automl-datasets | 数据集文件存储 |
| automl-models | 模型文件存储 |
| automl-annotations | 标注文件存储 |
| automl-augmented | 增强数据存储 |

### 5.2 S3 操作封装

```python
# app/utils/s3_delegate.py
class S3Delegate:
    """
    S3/MinIO 操作封装
    支持多 Bucket、预签名URL缓存、异步操作
    """
    
    async def put_file(self, bucket: str, key: str, data: bytes)
    async def get_file(self, bucket: str, key: str) -> bytes
    async def list_files(self, bucket: str, prefix: str) -> List[str]
    async def delete_file(self, bucket: str, key: str)
    async def create_dir(self, bucket: str, path: str)
    async def get_presigned_url(self, bucket: str, key: str, expires: int) -> str
    async def copy_file(self, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str)
```

---

## 6. 配置管理 (Nacos)

### 6.1 配置数据 ID

| Data ID | 内容 |
|---------|------|
| DB | 数据库连接配置 |
| LOCAL_S3_CONFIG | S3/MinIO 配置 |
| RABBITMQ_CONFIG | RabbitMQ 配置 |

### 6.2 配置优先级

```
环境变量 > Nacos 配置 > 默认值
```

---

## 7. API 响应格式

### 7.1 统一响应

```python
class Result(Generic[T]):
    success: bool           # 是否成功
    code: int              # 状态码
    message: str           # 消息
    data: Optional[T]      # 数据
    timestamp: datetime    # 时间戳
```

### 7.2 分页响应

```python
class PageResult(Generic[T]):
    items: List[T]         # 数据列表
    total: int             # 总数
    page: int              # 当前页
    page_size: int         # 每页数量
    pages: int             # 总页数
```

---

## 8. 定时任务

| 任务 | 周期 | 描述 |
|------|------|------|
| HeartbeatChecker | 5分钟 | 检查 AI Platform 服务健康状态 |

---

## 9. 依赖清单

```txt
# Web 框架
fastapi>=0.109.0
uvicorn[standard]>=0.27.0

# 数据库
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0          # PostgreSQL (可选)
aiomysql>=0.2.0          # MySQL
# 配置中心
nacos-sdk-python>=1.0.0

# 对象存储
boto3>=1.34.0
aioboto3>=12.0.0

# 消息队列
pika>=1.3.0
aio-pika>=9.0.0          # 异步版本

# HTTP 客户端
httpx>=0.26.0

# SSE
sse-starlette>=1.8.0

# 工具
pydantic>=2.5.0
python-multipart>=0.0.22
loguru>=0.7.0
python-dotenv>=1.0.0

```

---

## 10. 迁移计划

### Phase 1: 基础框架搭建
- [ ] 项目结构创建
- [ ] 配置管理 (Nacos + 环境变量)
- [ ] 数据库连接和 ORM 模型
- [ ] 统一响应格式和异常处理
- [ ] S3 操作封装

### Phase 2: 核心模块实现
- [ ] 数据集管理模块
- [ ] 标注管理模块
- [ ] 任务管理模块 (含 RabbitMQ 消费者)
- [ ] 模型部署模块 (含 RabbitMQ 消费者)

### Phase 3: 高级功能
- [ ] 预测模块 (含 SSE)
- [ ] 数据增强模块
- [ ] 工具模型模块
- [ ] 首页统计模块

### Phase 4: 完善与部署
- [ ] 定时任务
- [ ] 单元测试
- [ ] Docker 部署配置
- [ ] 文档完善

---

## 11. 与现有服务的交互

```
┌─────────────────┐     HTTP      ┌─────────────────┐
│   Flutter 前端   │◄────────────►│  automl_server  │
└─────────────────┘               │    (Python)     │
                                  └────────┬────────┘
                                           │
            ┌──────────────────────────────┼──────────────────────────────┐
            │                              │                              │
            ▼                              ▼                              ▼
   ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
   │  model_trainer  │           │  model_deploy   │           │     │
   │    (Python)     │           │    (Python)     │           │    (Python)     │
   └────────┬────────┘           └────────┬────────┘           └─────────────────┘
            │                              │                              
            │         RabbitMQ             │                              
            └──────────────┬───────────────┘                              
                           ▼                                              
                  ┌─────────────────┐                                     
                  │    RabbitMQ     │                                     
                  │    Exchange     │                                     
                  └────────┬────────┘                                     
                           │                                              
                           ▼                                              
                  ┌─────────────────┐                                     
                  │  automl_server  │◄─── 消费消息，写入数据库            
                  │    Consumer     │                                     
                  └─────────────────┘                                     
```

---

## 12. 数据库表结构 (现有)

基于 Java 原实现，以下是需要映射的数据库表：

| 表名 | 对应模块 |
|------|----------|
| dataset | 数据集 |
| asset | 原始资源 |
| sample_item | 样本 |
| annotation | 标注项目 |
| annotation_record | 标注记录 |
| task | 训练任务 |
| task_log | 任务日志 |
| base_models | 基础模型 |
| predict_task | 预测任务 |
| predict_data | 预测数据 |
| available_model | 可用模型 |
| tool_model | 工具模型 |
