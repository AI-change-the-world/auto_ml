# AI Pipeline Batch Sandbox

该服务通过 RabbitMQ 消费 `pipeline.batch.execute`，在受限子进程中执行镜像内的批量标注脚本，并把进度和结果发布回主服务。

新增平台脚本时，需要同时：

1. 在 `scripts/` 新增 `<script_key>.py`。
2. 在 `automl_server/app/modules/ai_pipeline/batch_scripts.py` 增加同名元数据和前端参数 Schema。

脚本必须提供：

```python
def execute_batch(params, report):
    # params["items"] 的每项有 batch_item_id 和 local_path
    report(processed=1, total=10, message="...")
    return {"items": [{
        "batch_item_id": 1,
        "status": "succeeded",
        "content": {"label_text": "0 0.5 0.5 0.4 0.4"},
    }]}
```

`content` 必须与目标标注项目的记录格式一致。检测项目使用现有的 YOLO `label_text`；脚本不能读取 S3 凭据或修改 Sandbox 工作区以外的文件。
