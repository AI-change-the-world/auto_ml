"""Offline five-epoch PyTorch smoke test for the custom training runtime."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def train(context: dict[str, Any], report: Callable[..., None]) -> dict[str, Any]:
    import torch
    from torch import nn

    parameters = context.get("parameters") or {}
    class_names = [str(value) for value in context["dataset"]["class_names"]]
    if len(class_names) != 2:
        raise ValueError("this smoke-test package requires exactly two class names")

    epochs = int(parameters.get("epochs", 5))
    sample_count = int(parameters.get("sample_count", 256))
    learning_rate = float(parameters.get("learning_rate", 0.05))
    seed = int(parameters.get("seed", 42))
    device = _resolve_device(context["resources"], torch)
    torch.manual_seed(seed)

    report(event_type="phase", phase="prepare", message="generating offline binary classification samples")
    features, labels = _synthetic_binary_samples(sample_count, torch)
    features = features.to(device)
    labels = labels.to(device)
    model = nn.Sequential(nn.Linear(2, 8), nn.ReLU(), nn.Linear(8, 2)).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    loss_function = nn.CrossEntropyLoss()

    report(event_type="phase", phase="train", message=f"running {epochs} offline smoke-test epochs on {device}")
    final_loss = 0.0
    final_accuracy = 0.0
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = model(features)
        loss = loss_function(logits, labels)
        loss.backward()
        optimizer.step()

        final_loss = float(loss.detach().item())
        final_accuracy = float((logits.argmax(dim=1) == labels).float().mean().item())
        report(
            event_type="metric",
            split="train",
            epoch=epoch,
            metrics={"loss": final_loss, "accuracy": final_accuracy},
        )

    output_dir = Path(context["workspace"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "smoke-model.pt"
    torch.save(
        {
            "model_state": model.cpu().state_dict(),
            "class_names": class_names,
            "input_features": 2,
            "smoke_test": True,
        },
        model_path,
    )
    report(event_type="phase", phase="complete", message="saved smoke-model.pt for S3 persistence")

    return {
        "summary": f"offline smoke classifier completed {epochs} epochs with {sample_count} generated samples",
        "metrics": {"train_loss": final_loss, "train_accuracy": final_accuracy},
        "artifacts": [
            {"path": "smoke-model.pt", "role": "model", "format": "pt", "deployable": False}
        ],
    }


def _synthetic_binary_samples(sample_count: int, torch):
    negative_count = sample_count // 2
    positive_count = sample_count - negative_count
    negative = torch.randn(negative_count, 2) * 0.45 - 1.0
    positive = torch.randn(positive_count, 2) * 0.45 + 1.0
    features = torch.cat((negative, positive))
    labels = torch.cat((torch.zeros(negative_count, dtype=torch.long), torch.ones(positive_count, dtype=torch.long)))
    order = torch.randperm(sample_count)
    return features[order], labels[order]


def _resolve_device(resources: dict[str, Any], torch):
    requested = resources.get("device", "cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable in the selected runtime")
        return torch.device("cuda:0")
    if requested != "cpu":
        raise ValueError(f"unsupported execution device: {requested}")
    return torch.device("cpu")
