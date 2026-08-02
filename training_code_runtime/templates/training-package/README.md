# Training Package Template

Use `training_package.json` to declare a platform-managed runtime, supported
tasks, parameters, and expected artifacts. Do not include `requirements.txt`:
the platform selects an immutable runtime image using `runtime.id`.

The `train(context, report)` entrypoint may be synchronous or async. It writes
artifacts below `context["workspace"]["output_dir"]` and returns a completion
object. The runner owns artifact checksum/size calculation and `result.json`.

Use `report` with event-specific fields only. The runner supplies
`protocol_version`, `execution_id`, `sequence`, and `occurred_at`.

```python
report(event_type="phase", phase="prepare", message="loading data")
report(event_type="log", level="info", message="model initialized")
report(event_type="metric", split="val", epoch=0, metrics={"accuracy": 0.9})
report(event_type="checkpoint", path="checkpoint-1.pt")
```
