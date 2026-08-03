"""Offline, deployable five-epoch PyTorch image-classification smoke test."""
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

    image_size = 16
    report(event_type="phase", phase="prepare", message="generating offline binary image classification samples")
    images, labels = _synthetic_binary_images(sample_count, image_size, torch)
    images = images.to(device)
    labels = labels.to(device)
    model = _tiny_image_classifier(nn).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    loss_function = nn.CrossEntropyLoss()

    report(event_type="phase", phase="train", message=f"running {epochs} offline smoke-test epochs on {device}")
    final_loss = 0.0
    final_accuracy = 0.0
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
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
    checkpoint_path = output_dir / "smoke-model.pt"
    torch.save(
        {
            "model_state": model.cpu().state_dict(),
            "class_names": class_names,
            "image_size": image_size,
            "smoke_test": True,
        },
        checkpoint_path,
    )
    model.eval()
    onnx_path = output_dir / "smoke-model.onnx"
    example_input = torch.zeros(1, 3, image_size, image_size, device=device)
    with torch.no_grad():
        torch.onnx.export(
            model,
            example_input,
            onnx_path,
            input_names=["images"],
            output_names=["probabilities"],
            dynamic_axes={"images": {0: "batch"}, "probabilities": {0: "batch"}},
            opset_version=17,
        )
    report(event_type="phase", phase="complete", message="exported deployable smoke-model.onnx and checkpoint")

    return {
        "summary": f"offline smoke classifier completed {epochs} epochs with {sample_count} generated samples",
        "metrics": {"train_loss": final_loss, "train_accuracy": final_accuracy},
        "artifacts": [
            {"path": "smoke-model.onnx", "role": "model", "format": "onnx", "deployable": True},
            {"path": "smoke-model.pt", "role": "checkpoint", "format": "pt", "deployable": False},
        ],
        "model": {
            "task_kind": "classification",
            "class_names": class_names,
            "framework": {"id": "pytorch", "version": "2.5"},
            "resume_checkpoint_path": "smoke-model.pt",
            "preprocessing": {"resize": [image_size, image_size], "scale": "0_1", "layout": "NCHW"},
        },
    }


def _synthetic_binary_images(sample_count: int, image_size: int, torch):
    negative_count = sample_count // 2
    positive_count = sample_count - negative_count
    negative = torch.rand(negative_count, 3, image_size, image_size) * 0.25
    positive = torch.rand(positive_count, 3, image_size, image_size) * 0.25
    negative[:, 2, image_size // 4 : image_size * 3 // 4, image_size // 4 : image_size * 3 // 4] += 0.75
    positive[:, 0, image_size // 4 : image_size * 3 // 4, image_size // 4 : image_size * 3 // 4] += 0.75
    images = torch.cat((negative, positive))
    labels = torch.cat((torch.zeros(negative_count, dtype=torch.long), torch.ones(positive_count, dtype=torch.long)))
    order = torch.randperm(sample_count)
    return images[order], labels[order]


def _tiny_image_classifier(nn):
    return nn.Sequential(
        nn.Conv2d(3, 8, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.AdaptiveAvgPool2d((1, 1)),
        nn.Flatten(),
        nn.Linear(8, 2),
        nn.Softmax(dim=1),
    )


def _resolve_device(resources: dict[str, Any], torch):
    requested = resources.get("device", "cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable in the selected runtime")
        return torch.device("cuda:0")
    if requested != "cpu":
        raise ValueError(f"unsupported execution device: {requested}")
    return torch.device("cpu")
