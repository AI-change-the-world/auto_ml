# Model Deploy Service

轻量级模型部署服务，专门针对 YOLO + ONNX 的模型部署方案。

## 架构特点

- **控制面/数据面分离**: Deploy Service 负责控制，Model Runtime 负责执行
- **模型即部署单元**: 管理的是"部署"而不是进程
- **ONNX 统一格式**: 训练 → 导出 ONNX → 部署
- **轻量级**: 不依赖 K8s/Triton，Docker Compose 即可运行

## 整体架构

```
                ┌──────────────────────┐
                │      主系统          │
                │  （模型管理 / API）   │
                └─────────┬────────────┘
                          ↓
                     MQ / HTTP
                          ↓
        ┌────────────────────────────┐
        │   model-deploy-service     │  ← 控制层（核心）
        │     (Python / FastAPI)     │
        └─────────┬──────────────────┘
                  ↓
        ┌────────────────────────────┐
        │     Runtime Manager        │
        │   （模型实例管理 / 调度）    │
        └──────┬─────────────────────┘
               ↓
     ┌──────────────────────┐
     │    model-runtime     │
     │    ONNX Runtime      │
     │    (独立进程)         │
     │    Port: 9001+       │
     └──────────────────────┘
```

## 核心组件

### 1. Runtime Manager
- 启动/停止模型实例进程
- 端口分配管理 (9001-9100)
- 健康检查
- 自动重启

### 2. Model Runtime
- 每个模型一个独立的 FastAPI 服务
- ONNX Runtime 推理
- 支持目标检测和分类

### 3. Deploy Service
- 部署/卸载模型
- 推理请求路由
- 部署状态管理

## 快速开始

### 本地运行

```bash
cd model_deploy
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/auto_ml"
export S3_ACCESS_KEY="minioadmin"
export S3_SECRET_KEY="minioadmin"
export S3_ENDPOINT="http://localhost:9000"
export S3_MODELS_BUCKET="auto-ml-models"
export RUNTIME_BASE_PORT=9001
export RUNTIME_MAX_PORT=9100

# 启动服务
python server.py
```

### Docker 运行

```bash
# 构建镜像
docker build -t model-deploy ./model_deploy

# 运行容器
docker run -d \
  -p 8082:8080 \
  -p 9001-9100:9001-9100 \
  -e DATABASE_URL="mysql+pymysql://user:password@host:3306/auto_ml" \
  -e S3_ACCESS_KEY="minioadmin" \
  -e S3_SECRET_KEY="minioadmin" \
  -e S3_ENDPOINT="http://minio:9000" \
  -e S3_MODELS_BUCKET="auto-ml-models" \
  model-deploy
```

### Docker Compose

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件配置你的环境变量

# 启动所有服务
docker-compose up -d model-deploy
```

## API 接口

### 健康检查
```bash
GET /health
```

### 部署模型
```bash
POST /deploy
Content-Type: application/json

{
  "model_id": 1,
  "device": "cpu",
  "version": "v1"
}
```

响应：
```json
{
  "success": true,
  "deployment_id": 1,
  "port": 9001
}
```

### 卸载模型
```bash
POST /undeploy/{deployment_id}
```

### 获取部署列表
```bash
GET /deployments
```

### 执行推理
```bash
POST /predict/{model_id}
Content-Type: multipart/form-data

file: <image_file>
```

### Base64 推理
```bash
POST /predict/{model_id}/base64
Content-Type: application/json

{
  "image": "base64_encoded_image_string"
}
```

### 检查部署健康
```bash
GET /deploy/{model_id}/health
```

### 重启运行时
```bash
POST /runtime/{model_id}/restart
```

### 转换 YOLO 到 ONNX
```bash
POST /convert/yolo-to-onnx
Content-Type: application/json

{
  "pt_path": "/path/to/model.pt",
  "output_path": "/path/to/model.onnx"
}
```

## 工作流程

### 1. 部署流程
```
1. 接收部署请求 (API)
2. 从 S3 拉取 ONNX 模型
3. 校验模型文件
4. 启动 Runtime 实例 (独立进程)
5. 注册实例 (端口/PID)
6. 健康检查
```

### 2. 推理流程
```
1. 接收推理请求
2. 查找对应的 Runtime 实例
3. 转发请求到实例
4. 返回推理结果
```

### 3. 卸载流程
```
1. 接收卸载请求
2. 停止 Runtime 进程
3. 释放端口
4. 更新部署状态
```

## 目录结构

```
model_deploy/
├── core/
│   ├── runtime_manager.py   # 运行时管理
│   └── deploy_service.py    # 部署服务逻辑
├── runtime/
│   └── runtime_server.py    # 模型运行时服务
├── db/
│   ├── base.py              # 数据库基础
│   ├── models.py            # 数据模型
│   └── crud.py              # 数据库操作
├── utils/
│   ├── config.py            # 配置管理
│   └── logger.py            # 日志配置
├── server.py                # FastAPI 主服务
├── requirements.txt
└── Dockerfile
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接 URL | - |
| S3_ACCESS_KEY | S3 Access Key | - |
| S3_SECRET_KEY | S3 Secret Key | - |
| S3_ENDPOINT | S3 服务端点 | - |
| S3_MODELS_BUCKET | 模型存储 Bucket | - |
| RUNTIME_BASE_PORT | 运行时起始端口 | 9001 |
| RUNTIME_MAX_PORT | 运行时最大端口 | 9100 |
| MODEL_CACHE_DIR | 模型缓存目录 | ./models |
| HOST | 服务监听地址 | 0.0.0.0 |
| PORT | 服务端口 | 8080 |

## 模型格式

### ONNX 模型要求
- 输入: `(1, 3, 640, 640)` - BCHW 格式
- 输出: YOLO 标准输出格式
- 预处理: 归一化到 0-1

### 从 YOLO 导出 ONNX
```python
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
model.export(format="onnx", imgsz=640)
```

## 能力边界

✅ 多模型部署  
✅ 多实例扩展  
✅ 推理路由  
✅ 健康检查  
✅ 与训练服务打通  

本质上已经是：**轻量版 AI 推理平台（≈ Triton 简化版）**

## 后续建议

1. **模型版本管理 + 灰度发布**
2. **推理日志 + QPS 统计**
3. **GPU 资源管理**
4. **模型热更新（蓝绿发布）**