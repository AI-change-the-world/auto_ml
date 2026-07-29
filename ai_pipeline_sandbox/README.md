# AI Pipeline Batch Sandbox

批量标注工具以 ZIP 包发布。ZIP 根目录的 `batch_script.json` 是工具元数据和运行参数的唯一来源：平台上传时解析并保存它，工具列表按它展示名称、描述、兼容类型和参数数量，执行弹窗按它动态生成表单。

因此，上传页面只选择 ZIP，不再维护一套容易与脚本脱节的名称、类型、入口和参数表单。需要修改这些信息时，修改 ZIP 内的清单后重新上传即可。

## 包结构

以下是一个可上传的视觉大模型标注工具。`batch_script.json` 必须位于 ZIP 根目录，不能被额外目录包起来。

```text
vision_llm_labeler.zip
├── batch_script.json       # 必需：工具与参数清单
├── main.py                 # 必需：与 entrypoint 对应
├── prompt.py               # 可选：入口同目录 Python 模块
├── config/
│   └── labels.json          # 可选：静态配置
├── weights/
│   └── model.onnx           # 可选：模型权重
└── src/
    └── helpers.py           # 可选：其他源码
```

ZIP 可以携带源码、配置和模型文件，但不会在运行时自动安装依赖。第三方 Python 依赖必须预先安装在 `ai_pipeline_sandbox` 镜像中；包内的 `requirements.txt` 仅可作为说明文件，不会被执行。

## 运行配置

Sandbox 的 RabbitMQ、MinIO 和执行资源限制统一从 Nacos 的 `AUTO_ML_CONFIG` 读取。`ai-pipeline-sandbox` 配置段包含 `timeout_seconds`、`max_output_bytes`、`memory_bytes`、`cpu_seconds` 和 `max_processes`。

容器只保留 Nacos 连接所需的引导环境变量。未启用或无法连接 Nacos 时，代码才使用同名本地环境变量和内置默认值，便于独立调试。资源限制通过 Nacos listener 实时更新，listener 不可用时会回退为轮询，并应用到后续批次；RabbitMQ 和 MinIO 配置在容器启动时生效。

## 清单格式

`batch_script.json` 的完整示例：

```json
{
  "key": "vision_llm_labeler",
  "version": "1.0.0",
  "name": "视觉大模型标注",
  "description": "使用外部视觉模型为图像检测项目生成标注草稿。",
  "entrypoint": "main.py",
  "supported_data_types": [0],
  "supported_annotation_types": [0],
  "parameters": [
    {
      "key": "base_url",
      "label": "Base URL",
      "value_type": "string",
      "required": true,
      "description": "兼容 OpenAI API 的服务地址"
    },
    {
      "key": "api_key",
      "label": "API Key",
      "value_type": "secret",
      "required": true,
      "description": "仅在本次 sandbox 执行时解密"
    },
    {
      "key": "model_name",
      "label": "模型",
      "value_type": "select",
      "options": ["gpt-4.1-mini", "gpt-4.1"],
      "default_value": "gpt-4.1-mini"
    },
    {
      "key": "classes",
      "label": "类别",
      "value_type": "string",
      "widget": "textarea",
      "value_source": "annotation_classes",
      "required": true,
      "description": "优先使用所选标注项目的类别；没有类别时手动输入。"
    },
    {
      "key": "prompt",
      "label": "补充提示词",
      "value_type": "string",
      "widget": "textarea",
      "description": "留空时使用内置 bbox 输出提示词。"
    }
  ]
}
```

### 顶层字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `key` | 是 | 工具唯一标识，格式为小写字母开头的 `a-z`、数字、`_`、`-`，最长 128 个字符。同一 `key` 重新上传会更新该工具包。 |
| `version` | 是 | 当前包版本，最长 64 个字符。 |
| `name` | 是 | 工具列表显示名称，最长 255 个字符。 |
| `description` | 否 | 工具用途说明，最长 2000 个字符。 |
| `entrypoint` | 是 | ZIP 内相对 Python 路径，例如 `main.py` 或 `src/main.py`。必须以 `.py` 结尾，不能使用绝对路径或 `..`。 |
| `supported_data_types` | 是 | 支持的数据集类型数组。工具列表、执行时的数据集筛选和服务端校验都以它为准。 |
| `supported_annotation_types` | 是 | 支持的标注项目类型数组。执行时仅允许选择其中的标注项目。 |
| `parameters` | 否 | 运行参数定义数组，最多 50 项。前端会按数组顺序渲染。 |

数据集类型：`0` 图像，`1` 文本，`2` 视频，`3` 音频。

标注类型：`0` 检测，`1` 分类，`2` 分割，`3` MLLM，`4` 姿态，`5` LLM，`6` DPO，`7` DPO 二选一，`8` DPO 多选一，`9` DPO 参考增强，`10` DPO 多轮。

### `parameters` 字段

每个参数对象使用以下字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `key` | 是 | 小写唯一标识，规则与工具 `key` 相同。脚本通过 `params["script_params"][key]` 读取。 |
| `label` | 否 | 表单标签；未填写时使用 `key`。 |
| `value_type` | 否 | `string`、`number`、`boolean`、`select`、`secret`，默认 `string`。 |
| `required` | 否 | 是否必填，默认 `false`。 |
| `default_value` | 否 | 默认值，必须与 `value_type` 一致；`secret` 不允许默认值。 |
| `description` | 否 | 表单字段下方的说明，最长 500 个字符。 |
| `options` | 条件必填 | 仅 `select` 使用，必须是非空字符串或数字数组。 |
| `widget` | 否 | 目前支持 `textarea`（多行文本）和 `number`。默认根据 `value_type` 选择控件。 |
| `value_source` | 否 | 目前支持 `annotation_classes`。标注项目已有类别时，平台自动使用其类别并隐藏该输入；没有类别时保留字段让用户填写。仅支持 `string`。 |

`secret` 会使用密码输入框。值在主服务数据库中加密保存，任务查询仅返回 `******`，只有下发本次 MQ 执行消息时才会解密。加密密钥读取 Nacos 的 `ai-pipeline-batch.secret_key`，其值必须是稳定的 Fernet key。

## 脚本入口契约

入口模块必须提供 `execute_batch`。它可为同步或异步函数；推荐接收 `params` 与 `report` 两个参数：

```python
from typing import Any, Callable


def execute_batch(params: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    script_params = params["script_params"]
    base_url = script_params["base_url"]
    api_key = script_params["api_key"]
    model_name = script_params["model_name"]

    results = []
    items = params["items"]
    for index, item in enumerate(items, start=1):
        # item["local_path"] 是当前 sandbox 工作目录中的输入文件副本。
        # 调用模型并把结果转换为目标标注项目需要的 content。
        results.append({
            "batch_item_id": item["batch_item_id"],
            "status": "succeeded",
            "content": {
                "format": "yolo",
                "label_text": "0 0.5 0.5 0.4 0.4"
            }
        })
        report(processed=index, total=len(items), message="sample completed")

    return {"items": results}
```

`params` 包含以下内容：

| 字段 | 说明 |
| --- | --- |
| `run_id`、`chunk_key` | 本次任务和子批次标识，可用于日志关联。 |
| `annotation` | 目标标注项目快照，包含 `annotation_id`、`annotation_type`、`classes`、`prompt`。 |
| `script_params` | 根据清单校验后的运行参数。 |
| `items` | 本次子批次的样本。每项至少包含 `batch_item_id`、`sample_item_id`、`item_key`、`local_path`，以及数据集资源和样本快照信息。 |

`report(processed=..., total=..., message=...)` 可多次调用，用于任务详情页的实时进度和事件展示。

返回值必须是 `{"items": [...]}`。每个输入样本应返回一项，并使用对应的 `batch_item_id`：

| 字段 | 说明 |
| --- | --- |
| `batch_item_id` | 必填，来自输入项。不能使用 `sample_item_id` 代替。 |
| `status` | `succeeded`、`skipped` 或 `failed`。未返回的样本会被记为失败。 |
| `content` | `succeeded` 时必填，必须是目标标注类型可保存的 JSON 对象。 |
| `message` | `skipped` 时的可选原因。 |
| `error` | `failed` 时的可选错误信息。 |

检测标注的 `content` 可使用现有 YOLO 结构：

```json
{
  "format": "yolo",
  "label_text": "0 0.5 0.5 0.4 0.4"
}
```

其他标注类型必须返回与该类型标注记录一致的 `content`。sandbox 不会替脚本转换大模型原始输出。

## 打包与上传

在工具目录内执行打包，确保压缩后的根目录就是清单和入口文件：

```bash
cd vision_llm_labeler
zip -r ../vision_llm_labeler.zip batch_script.json main.py prompt.py config weights src
cd ..
unzip -l vision_llm_labeler.zip
```

`unzip -l` 的输出中应直接看到 `batch_script.json` 和 `main.py`，而不是 `vision_llm_labeler/batch_script.json`。随后在“批量标注工具”页面右上角选择“上传脚本包”。

上传会校验以下约束：ZIP 最大 100 MB、最多 512 个文件、解压后最多 512 MB；清单最大 256 KB；不允许绝对路径、`..` 路径或符号链接；`entrypoint` 必须存在于 ZIP 内。每个任务会保存当时的脚本包路径、入口、版本和参数快照，因此工具升级或删除不会影响已创建任务。

## 内置脚本

平台内置脚本可随镜像发布：在 `scripts/` 新增 `<script_key>.py`，并在 `automl_server/app/modules/ai_pipeline/batch_scripts.py` 注册同名元数据和参数定义。上传 ZIP 的用户工具不需要修改平台源码。

脚本进程只会收到任务输入、参数和本次工作目录；运行时受到 CPU、内存、进程数、时间和输出大小限制。
