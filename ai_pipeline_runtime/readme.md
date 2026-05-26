# AI Pipeline Runtime

独立的 AI 能力运行时，作为可选插件式能力提供辅助标注链路所需的能力注册、调用和轻量 pipeline 编排。当前主要用于图像理解、草稿标注、白框图生成、白框图提取和白框图还原。

## 组成

1. `config.py`
   负责本地 YAML / Nacos 配置加载，以及 provider、pipeline 的运行时配置。
2. `providers.py`
   封装模型供应商，当前包含：
   - `openai_compatible`
   - `dashscope_multimodal`
   - `mock`
3. `capabilities/`
   放可复用能力，每个能力都可以独立调用：
   - `describe_image`
   - `draft_annotation`
   - `draft_annotation_preview`
   - `render_white_annotation_overlay`
   - `understand_white_annotations`
   - `extract_white_annotations`
   - `assist_annotation`
4. `ocr.py`
   内置 `RapidOCR`，用于白框图文字识别和类目归一。
5. `pipeline.py`
   轻量串行编排器，只负责组织步骤。
6. `service.py`
   组合配置、provider、能力注册和 pipeline 运行。
7. `app.py`
   FastAPI 适配层，适合 Docker Compose 内部服务模式。

## 能力说明

### `describe_image`

输入图像，输出图像描述和场景摘要。

### `draft_annotation`

输入原图，输出结构化 JSON 草稿标注。

### `draft_annotation_preview`

输出 bbox 草稿并生成 OpenCV 预览图后上传到 S3。

### `render_white_annotation_overlay`

输入原图和类别列表，生成纯白框和纯白标签的叠加图。

### `extract_white_annotations`

输入叠加图，先提取白色框，再用 OCR 识别文字并还原成结构化标注。

### `understand_white_annotations`

输入白框叠加图，由多模态模型直接还原结构化标注。

### `assist_annotation`

组合白框生成、提取和多模态还原的辅助标注流程。

## Pipeline

当前提供的示例 pipeline：

- `vision_label_bundle`: 图像理解 + BBox 草稿
- `direct_bbox_preview`: 直接理解 BBox + 预览图
- `overlay_extract`: 白框图提取 BBox
- `overlay_understand_mllm`: 多模态理解白框 BBox
- `render_then_extract_overlay`: 生成白框并提取 BBox

## 扩展性

- `provider` 是可插拔的，后续可继续接入更多多模态或图像编辑模型
- `capability` 是独立单元，新增能力只需要补充新的能力实现和注册
- `pipeline` 只负责编排，适合按业务把现有能力重新组合
- OCR 和规则后处理可以继续替换或增强，不会绑死在单一实现上
- 后续如果扩展到视频、音频或更多结构化标注能力，可以继续沿用同一套接入方式

## 配置方式

运行配置通过主服务下发 `definition` 和 `resource_bindings`。
MQ 配置从 Nacos 读取 `AUTO_ML_CONFIG`。
`sample_config.yaml` 提供了本地示例配置。

## 运行方式

按需启用时可单独启动该服务。

```bash
pip install -r ai_pipeline_runtime/requirements.txt
cd ai_pipeline_runtime
uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

## Docker

从 `ai_pipeline_runtime` 目录构建：

```bash
cd ai_pipeline_runtime
docker build -t ai-pipeline-runtime .
```

运行：

```bash
docker run --rm -p 8010:8010 ai-pipeline-runtime
```

## API

### 健康检查

`/health` 会返回服务状态和版本号，当前版本为 `1.0.0`。

```bash
curl http://127.0.0.1:8010/health
```

### 获取能力列表

```bash
curl http://127.0.0.1:8010/v1/capabilities
```

### 直接调用单个能力

```bash
curl -X POST http://127.0.0.1:8010/v1/capabilities/draft_annotation/run \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "mock_vision",
    "input": {
      "image": {
        "path": "/absolute/path/to/image.png"
      },
      "classes": ["安全帽", "安全背心", "绝缘手套"]
    },
    "params": {
      "score_threshold": 0.2
    }
  }'
```

### 运行命名 pipeline

```bash
curl -X POST http://127.0.0.1:8010/v1/pipelines/vision_label_bundle/run \
  -H "Content-Type: application/json" \
  -d '{
    "image": {
      "path": "/absolute/path/to/image.png"
    },
    "classes": ["安全帽", "安全背心"]
  }'
```

### 运行白框图的 OpenCV + OCR 路线

```bash
curl -X POST http://127.0.0.1:8010/v1/pipelines/overlay_extract/run \
  -H "Content-Type: application/json" \
  -d '{
    "overlay_image": {
      "path": "/absolute/path/to/overlay.png"
    },
    "classes": ["安全帽", "安全背心"]
  }'
```

### 运行白框图的多模态理解路线

```bash
curl -X POST http://127.0.0.1:8010/v1/pipelines/overlay_understand_mllm/run \
  -H "Content-Type: application/json" \
  -d '{
    "overlay_image": {
      "path": "/absolute/path/to/overlay.png"
    },
    "classes": ["安全帽", "安全背心"]
  }'
```

### 运行生成白框图再提取的完整路线

```bash
curl -X POST http://127.0.0.1:8010/v1/pipelines/render_then_extract_overlay/run \
  -H "Content-Type: application/json" \
  -d '{
    "image": {
      "path": "/absolute/path/to/image.png"
    },
    "classes": ["安全帽", "安全背心"]
  }'
```
