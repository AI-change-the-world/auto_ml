# Training Package Template

Use `training_package.json` to declare a platform-managed runtime, supported
tasks, parameters, and expected artifacts. Do not include `requirements.txt`:
the platform selects an immutable runtime image using `runtime.id`.

The `train(context, report)` entrypoint may be synchronous or async. It writes
artifacts below `context["workspace"]["output_dir"]` and returns a completion
object. The runner owns artifact checksum/size calculation and `result.json`.

To bundle optional initial weights with this custom model, place the file in
the ZIP, for example `weights/initial.pt`. The runner extracts the whole ZIP
into the code directory, so `train.py` can load it with
`Path(__file__).resolve().parent / "weights" / "initial.pt"`. Omit the file
to train from scratch.

There is no manifest field or second upload for bundled weights: the script
owns the relative path and decides whether to load it. This keeps a script and
its compatible weights as one immutable custom-model version.

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
