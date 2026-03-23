## 目标

做一个独立的 AI 能力层，专门服务于“辅助标注”这件事。

关键原则：

1. 业务归业务，AI 归 AI。
2. 核心能力必须可以单独嵌入调用，不强依赖 pipeline。
3. pipeline 只是一层可选编排，不应该反过来绑死能力实现。
4. 配置优先走 YAML，部署时可选接入 Nacos 做统一配置和热更新。

## 推荐架构

这个目录下现在的实现已经按下面的分层拆开：

1. `config.py`
   负责本地 YAML / Nacos 配置加载，以及 provider、pipeline 的运行时配置。
2. `providers.py`
   封装模型供应商，当前包含：
   - `openai_compatible`
   - `mock`
3. `capabilities.py`
   放真正可复用的能力，每个能力都可以独立调用：
   - `describe_image`
   - `draft_annotation`
   - `render_white_annotation_overlay`
   - `understand_white_annotations`
   - `extract_white_annotations`
4. `ocr.py`
   内置 `RapidOCR`，专门处理叠加白字识别和类目归一。
5. `pipeline.py`
   轻量串行编排器，只负责组织步骤，不承载业务逻辑。
6. `service.py`
   组合配置、provider、能力注册和 pipeline 运行。
7. `app.py`
   可选的 FastAPI 适配层，适合 Docker Compose 内部服务模式。

## 为什么这样拆

你的场景本质上不是“先上 workflow”，而是“先有可组合的 AI 能力”。

所以这里的设计重点是：

1. 单能力可嵌入
   例如业务侧直接调用 `draft_annotation` 或 `extract_white_annotations`，不需要先定义 pipeline。
2. pipeline 可选
   当你要串联“图像理解 + 草稿标注 + 白框提取”时，再把这些能力按步骤串起来。
3. provider 可替换
   以后你想把 Qwen、OpenAI 兼容接口、自建多模态模型混用，改配置即可。
4. 算法和模型解耦
   OpenCV 白框提取属于确定性算法能力，不应该混在大模型调用逻辑里。

## 当前能力说明

### 1. `describe_image`

输入图像，调用多模态模型输出图像描述，适合：

- 图中发生了什么
- 场景理解
- 分类辅助
- 标注前摘要

### 2. `draft_annotation`

输入原图，调用多模态模型输出结构化 JSON 标注草稿：

- `label`
- `bbox`
- `label_anchor`
- `confidence`

这个能力现在默认是强约束模式：

- 必须传入 `classes`
- `label` 只能从 `classes` 中选
- 不允许大模型自由发挥类目
- `label_anchor` 会被要求放在 bbox 附近，便于后续直接叠字或画标注

这更适合你说的场景，比如只允许：

- `安全帽`
- `安全背心`
- `绝缘手套`

### 3. `extract_white_annotations`

输入叠加了白框/白字的图，先用 OpenCV 提取白色框，再用内置 `RapidOCR` 做全图 OCR，最后把文字归属给最近的框。

这比较贴近你说的那种模式：

1. 先生成带框的叠加图
2. 再提取白框位置
3. 再读取白字标签
4. 最终还原成结构化 `bndbox + label`

为了减少 OCR 自由发挥，`RapidOCR` 识别出来的文本还会再和 `classes` 做一次归一匹配，尽量只回到你定义好的类目集合。

这个能力现在还额外处理两件事：

- 重叠框去重，尽量避免同一个框被重复返回
- 文字和框的就近匹配，不再是简单截一条带子去 OCR

### 4. `understand_white_annotations`

这是另一条路线：

1. 先让图像编辑模型画出纯白色框和纯白色标签
2. 把这张叠加图直接交给多模态模型
3. 让它把白框和白字再还原成结构化标注

这条路线保留着，适合：

- OpenCV 提框效果不稳定的场景
- 白框重叠特别复杂的场景
- 需要把视觉理解再兜一层的时候

### 5. `render_white_annotation_overlay`

这是“标注生成”能力本身：

1. 输入原图
2. 指定允许的 `classes`
3. 调用图像编辑模型
4. 输出一张只含纯白框和纯白标签的叠加图

这个 capability 的目标不是直接返回结构化标注，而是稳定地产生后续可解析的中间产物。

推荐约束是：

- 只允许画纯白色框和纯白色文字
- 标签文本只能来自 `classes`
- 标签必须靠近对应框
- 不允许增加图例、箭头、说明文字、水印

## 配置方式

默认会读取：

- `auto_augment_pipeline/sample_config.yaml`

也可以通过环境变量覆盖：

- `AUTO_AUGMENT_CONFIG`
- `AUTO_AUGMENT_USE_NACOS`
- `NACOS_SERVER_ADDR`
- `NACOS_DATA_ID`
- `NACOS_GROUP`
- `AUTO_AUGMENT_WATCH_NACOS`

`sample_config.yaml` 里已经包含了：

- provider 配置示例
- 默认 provider
- 四个示例 pipeline

OCR 不需要额外配置 provider，默认使用内置 `RapidOCR`。
图像编辑推荐单独配一个 `image_edit_provider`，比如 `nano banana2 pro`。

## 运行方式

```bash
pip install -r auto_augment_pipeline/requirements.txt
uvicorn auto_augment_pipeline.app:app --host 0.0.0.0 --port 8010 --reload
```

## Docker

从仓库根目录构建：

```bash
docker build -f auto_augment_pipeline/Dockerfile -t auto-augment-pipeline .
```

运行：

```bash
docker run --rm -p 8010:8010 auto-augment-pipeline
```

## API

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

## 后续建议

接下来最值得继续补的，不是把 pipeline 做重，而是把能力做厚：

1. 增加视频帧采样 / 音频转写能力
2. 增加后处理能力，比如框合并、标签归一化、置信度重排
3. 增加批处理任务执行器，而不是一开始就上复杂工作流引擎
4. 如果后面有需要，再把 OCR 抽象成可切换 provider

## 结论

这个方向更适合你当前的目标：

- 能力是黑盒，可直接嵌入
- 服务只是可选适配层
- pipeline 是薄编排，不抢核心地位
- 后面扩视频、音频、OCR、规则后处理都比较顺
