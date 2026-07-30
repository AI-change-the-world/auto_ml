"""Small helper module to verify imports from the uploaded ZIP package."""
from __future__ import annotations


def parse_ratio(value: object, name: str) -> float:
    ratio = float(value)
    if not 0 < ratio <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return ratio


def build_center_box(class_index: int, box_width: float, box_height: float) -> str:
    if class_index < 0:
        raise ValueError("class_index must be greater than or equal to 0")
    return f"{class_index} 0.500000 0.500000 {box_width:.6f} {box_height:.6f}"
