<div align="center">
  <img src="./readme/icon_with_text.png" width="300" height="300">
</div>

<p align="center">📘 其他语言版本</p>
<p align="center">
  <a href="README_en.md">English</a> | <a href="README.md">简体中文</a>
</p>

<p align="center">
  <strong>一站式计算机视觉 AutoML 平台</strong>
</p>

<p align="center">
  <a href="#-功能特性">功能特性</a> •
  <a href="#-技术架构">技术架构</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-项目结构">项目结构</a> •
  <a href="#-开发指南">开发指南</a>
</p>

---

## 📖 项目简介

AutoML 是一个开源的端到端计算机视觉平台，提供从**数据管理**、**图像标注**、**模型训练**到**模型部署**的完整工作流。平台采用现代化微服务架构，支持可视化操作，让 AI 模型开发变得简单高效。

**核心优势：**
- 🎯 **全流程覆盖**：数据集管理 → 标注 → 训练 → 部署，一站式完成
- 🏷️ **专业标注工具**：支持 BBox、OBB 旋转框、Polygon 多边形等多种标注类型
- 🚀 **微服务架构**：基于 Docker + RabbitMQ + Nacos 的分布式架构，易于扩展
- 💾 **对象存储集成**：支持 MinIO/S3 存储，高效管理大规模数据集和模型
- 🌐 **现代前端**：React 19 + TypeScript + Ant Design 6，流畅的用户体验
- 🔌 **插件化设计**：训练和部署服务独立运行，支持灵活扩展

---

## ✨ 功能特性

### 📂 数据集管理
- 支持图像、视频、文本等多种数据类型
- ZIP/TAR 批量导入，快速构建数据集
- S3/MinIO 对象存储，支持大规模数据管理
- 数据集预览、导出、追加等完整操作

### 🏷️ 图像标注
- **BBox 标注**：标准边界框标注，适用于目标检测
- **OBB 标注**：旋转边界框，适用于倾斜目标检测
- **Polygon 标注**：多边形标注，适用于实例分割
- 标注项目管理，支持自定义类别
- 基于 Konva 的高性能渲染引擎
- 撤销/重做、快捷键等高效标注体验

### 🧪 模型训练
- 支持 YOLO 等主流目标检测模型
- 可视化训练任务管理
- 实时训练日志查看
- 基础模型库管理
- 基于 RabbitMQ 的异步任务调度

### ☁️ 模型部署
- 一键部署训练完成的模型
- 动态端口分配，支持多模型并发部署
- RESTful API 推理接口
- 模型健康检查与状态监控
- 热加载/卸载，无需重启服务

### 🏠 可视化仪表盘
- 数据集、标注、模型统计信息
- 最近活动追踪
- 存储使用情况
- 快速创建入口

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React + TypeScript)               │
│                    http://localhost:5173                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│                  AutoML Server (FastAPI)                     │
│                    Port: 45678                               │
│  ┌──────────┬──────────┬──────┬────────┬────────┐           │
│  │ Dataset  │Annotation│ Task │ Deploy │  Home  │           │
│  └──────────┴──────────┴──────┴────────┴────────┘           │
└────┬──────────────┬──────────────┬──────────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌────────┐    ┌──────────┐   ┌──────────┐
│ MySQL  │    │  MinIO   │   │ RabbitMQ │
│  :3306 │    │  :9000   │   │  :5672   │
└────────┘    └──────────┘   └────┬─────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
          ┌─────────▼─────────┐      ┌─────────▼─────────┐
          │  Model Trainer    │      │  Model Deploy     │
          │  Port: 8081       │      │  Port: 8082       │
          │                   │      │  Runtime: 9001+   │
          └───────────────────┘      └───────────────────┘
```

### 技术栈

**前端**
- React 19 + TypeScript
- Vite 8（构建工具）
- Ant Design 6（UI 组件库）
- React Router 7（路由管理）
- Zustand（状态管理）
- Konva + React-Konva（Canvas 渲染）
- i18next（国际化）
- Axios（HTTP 客户端）

**后端**
- Python 3.10+
- FastAPI（Web 框架）
- SQLAlchemy 2.0 + AsyncIO（异步 ORM）
- Uvicorn（ASGI 服务器）

**基础设施**
- MySQL 8.0（关系型数据库）
- MinIO（对象存储）
- RabbitMQ（消息队列）
- Nacos（配置中心）
- Docker & Docker Compose（容器编排）

**微服务**
- Model Trainer Service（模型训练服务）
- Model Deploy Service（模型部署服务）

---

## 🚀 快速开始

### 环境要求

- **Docker** 20.10+ 和 **Docker Compose** 2.0+
- **Node.js** 18+（前端开发）
- **Python** 3.10+（后端开发）
- **Git** 2.0+

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/auto_ml.git
cd auto_ml

# 2. 配置环境变量
cp .env.example .env
# 根据需要修改 .env 文件中的配置

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f
```

服务启动后访问：
- **前端开发服务器**：`http://localhost:5173`（需单独启动，见下方开发模式）
- **AutoML Server API**：`http://localhost:45678`
- **API 文档 (Swagger)**：`http://localhost:45678/swagger-ui`
- **Model Trainer**：`http://localhost:8081`
- **Model Deploy**：`http://localhost:8082`
- **RabbitMQ 管理界面**：`http://localhost:15672` (账号: automl / automl123456)
- **MinIO 控制台**：`http://localhost:9010` (账号: minioadmin / minioadmin123)
- **Nacos 控制台**：`http://localhost:8848`

### 方式二：开发模式

#### 1. 启动基础设施

```bash
# 仅启动数据库、消息队列、对象存储等基础服务
docker-compose up -d mysql rabbitmq minio nacos
```

#### 2. 启动前端

```bash
cd frontend_v2

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

前端将运行在 `http://localhost:5173`，已配置代理转发到后端。

#### 3. 启动后端

```bash
cd automl_server

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python run.py
```

后端将运行在 `http://localhost:45678`。

#### 4. 启动微服务（可选）

```bash
# 模型训练服务
cd model_trainer
pip install -r requirements.txt
python server.py

# 模型部署服务
cd model_deploy
pip install -r requirements.txt
python server.py
```

---

## 📁 项目结构

```
auto_ml/
├── frontend_v2/              # 前端项目 (React + TypeScript)
│   ├── src/
│   │   ├── api/             # API 客户端
│   │   ├── pages/           # 页面组件
│   │   │   ├── home/        # 首页
│   │   │   ├── dataset/     # 数据集管理
│   │   │   ├── annotation/  # 标注工具
│   │   │   ├── task/        # 训练任务
│   │   │   └── deploy/      # 模型部署
│   │   ├── layouts/         # 布局组件
│   │   ├── stores/          # 状态管理
│   │   ├── types/           # TypeScript 类型定义
│   │   └── i18n/            # 国际化配置
│   └── package.json
│
├── automl_server/           # 主服务 (FastAPI)
│   ├── app/
│   │   ├── modules/         # 业务模块
│   │   │   ├── dataset/     # 数据集模块
│   │   │   ├── annotation/  # 标注模块
│   │   │   ├── task/        # 训练任务模块
│   │   │   ├── deploy/      # 部署模块
│   │   │   └── home/        # 首页模块
│   │   ├── db/              # 数据库模型
│   │   ├── mq/              # RabbitMQ 消息处理
│   │   ├── config/          # 配置管理
│   │   └── common/          # 公共组件
│   └── requirements.txt
│
├── model_trainer/           # 模型训练微服务
│   ├── core/                # 训练核心逻辑
│   ├── utils/               # 工具类
│   └── server.py            # 服务入口
│
├── model_deploy/            # 模型部署微服务
│   ├── core/                # 部署核心逻辑
│   ├── runtime/             # 模型运行时
│   ├── utils/               # 工具类
│   └── server.py            # 服务入口
│
├── auto_augment_pipeline/   # 数据增强管道（可选）
│
├── docker-compose.yml       # Docker 编排配置
├── mysql/init/              # 数据库初始化脚本
├── nacos/                   # Nacos 配置
└── readme/                  # 文档图片
```

---

## 🛠️ 开发指南

### 数据库管理

数据库初始化脚本位于 `mysql/init/01_init_automl.sql`，容器首次启动时自动执行。

如需重置数据库：
```bash
docker-compose down -v
docker-compose up -d mysql
```

### 配置管理

项目使用 Nacos 作为配置中心，配置文件位于 `nacos/automl-config.yaml`。

主要配置项：
- MySQL 连接信息
- MinIO/S3 存储配置
- RabbitMQ 消息队列配置
- 微服务地址配置

### API 文档

启动服务后访问 Swagger UI：
```
http://localhost:45678/swagger-ui
```

### 前端开发

```bash
cd frontend_v2

# 安装依赖
pnpm install

# 启动开发服务器（热重载）
pnpm dev

# 构建生产版本
pnpm build

# 代码检查
pnpm lint
```

### 后端开发

```bash
cd automl_server

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（热重载）
python run.py

# 或直接使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 45678
```

---


## 🔧 常见问题

### 1. 服务启动失败

检查 Docker 容器状态和日志：
```bash
docker-compose ps
docker-compose logs <service-name>
```

### 2. 数据库连接错误

确保 MySQL 容器已启动并健康：
```bash
docker-compose exec mysql mysql -u automl -p auto_ml
```

### 3. MinIO 访问问题

检查 MinIO 控制台 `http://localhost:9010`，确认 buckets 已创建：
- `auto-ml-datasets`
- `auto-ml-models`
- `auto-ml-annotations`

### 4. 前端无法连接后端

确认 `.env.development` 中的代理配置正确：
```
VITE_API_BASE_URL=http://localhost:45678
```

---

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 [AGPL License](LICENSE) 开源协议。

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Ant Design](https://ant.design/)
- [Konva](https://konvajs.org/)
- [YOLO](https://github.com/ultralytics/ultralytics)
- [RabbitMQ](https://www.rabbitmq.com/)
- [MinIO](https://min.io/)

---

<div align="center">
  <strong>AutoML</strong> - 让计算机视觉开发更简单
</div>
