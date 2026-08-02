# Training Package Template

Use `training_package.json` to declare a platform-managed runtime, supported
tasks, parameters, and expected artifacts. Do not include `requirements.txt`:
the platform selects an immutable runtime image using `runtime.id`.

The `train(context, report)` entrypoint may be synchronous or async. It writes
artifacts below `context["workspace"]["output_dir"]` and returns a completion
object. The runner owns artifact checksum/size calculation and `result.json`.

If this package declares `model_input_contract`, the worker materializes the
selected immutable model input below `context["workspace"]["input_dir"]` and
passes its path in `context["model_input_path"]`. Use `context["model_input"]`
to distinguish `initialize` from `resume`; only a model-package checkpoint
explicitly registered as resumable may use `resume`.

When returning `model`, include its `framework` identity. To allow a completed
run to become a future resume source, return `resume_checkpoint_path` pointing
to one produced artifact with role `checkpoint`.

Use `report` with event-specific fields only. The runner supplies
`protocol_version`, `execution_id`, `sequence`, and `occurred_at`.

```python
report(event_type="phase", phase="prepare", message="loading data")
report(event_type="log", level="info", message="model initialized")
report(event_type="metric", split="val", epoch=0, metrics={"accuracy": 0.9})
report(event_type="checkpoint", path="checkpoint-1.pt")
```
