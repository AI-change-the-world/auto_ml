"""Training-package boilerplate.

The dormant runtime will call `train(context, report)`. Do not call platform
APIs here: all input is materialized under `context['workspace']['input_dir']`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def train(context: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    output_dir = Path(context["workspace"]["output_dir"])
    dataset = context["dataset"]
    parameters = context.get("parameters", {})

    report(event_type="phase", phase="prepare", message="loading materialized dataset")
    class_names = dataset.get("class_names", [])

    # Replace this section with framework-specific training. Input files are
    # relative to workspace.input_dir according to dataset.items.
    for epoch in range(int(parameters.get("epochs", 1))):
        report(
            event_type="metric",
            split="train",
            epoch=epoch,
            metrics={"loss": 0.0},
        )

    report(event_type="phase", phase="export", message="writing model artifact")
    # The package writes only artifacts. The runner computes their digest and
    # size, creates result.json, and emits the final result line.
    model_path = output_dir / "model.onnx"
    model_path.write_bytes(b"replace-with-exported-model")

    return {
        "summary": "Template completed; replace the placeholder model export.",
        "metrics": {"train_loss": 0.0},
        "artifacts": [
            {
                "path": "model.onnx",
                "role": "model",
                "format": "onnx",
                "deployable": True,
            }
        ],
        "model": {
            "task_kind": context["task"]["task_kind"],
            "class_names": class_names,
            "preprocessing": {},
            "postprocessing": {},
        },
    }
