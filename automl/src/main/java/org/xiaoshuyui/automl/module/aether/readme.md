**Aether:** AI Execution and Task Handling via Extensible Routing

> Aether 是古希腊神话中的“上层空气”，象征轻盈而万能的中介

**Basic request**:
```json
{
  "task": "image-captioning",
  "model_id": 1,
  "input": {
    "data": "<base64>|<url>|<path>|<s3>",// default: s3
    "data_type": "image|text|video|audio" // default: image
  },
  "meta": {
    "task_id": 1,
    "sync": true  // default: true
  }
}
```

**Basic response**:
```json
{
  "success": true,
  "output": {
    "detections": [
      {
        "class": "person",
        "confidence": 0.93,
        "bbox": [100, 120, 200, 260]
      }
    ]
  },
  "meta": {
    "time_cost_ms": 53,
    "task_id": 1
  },
  "error": null
}
```