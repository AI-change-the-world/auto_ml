"""
Runtime dependency checks for model deployment.
"""
from __future__ import annotations

import importlib
from typing import Optional, Tuple


EXPECTED_NUMPY_VERSION = "1.26.4"
EXPECTED_ONNXRUNTIME_VERSION = "1.17.0"


def runtime_dependency_status() -> Tuple[bool, Optional[str]]:
    """
    Validate runtime-side Python dependencies under the current interpreter.

    The runtime subprocess is launched with the same interpreter as model_deploy,
    so a failure here means deployment will fail later as well.
    """
    try:
        import numpy as np
    except Exception as exc:
        return False, f"Failed to import numpy in model_deploy runtime env: {exc}"

    numpy_version = getattr(np, "__version__", "unknown")

    try:
        ort = importlib.import_module("onnxruntime")
    except Exception as exc:
        return False, _build_onnxruntime_error(numpy_version, exc)

    ort_version = getattr(ort, "__version__", "unknown")
    return True, f"numpy={numpy_version}, onnxruntime={ort_version}"


def ensure_runtime_dependencies() -> str:
    ok, message = runtime_dependency_status()
    if not ok:
        raise RuntimeError(message or "Runtime dependency check failed")
    return message or ""


def _build_onnxruntime_error(numpy_version: str, exc: Exception) -> str:
    error_text = str(exc).strip() or exc.__class__.__name__
    guidance = (
        "ONNX runtime dependencies are not usable in the current Python environment. "
        f"Detected numpy={numpy_version}. "
        "The deployment runtime in this project expects a compatible pair such as "
        f"numpy=={EXPECTED_NUMPY_VERSION} and onnxruntime=={EXPECTED_ONNXRUNTIME_VERSION}. "
        "Reinstall them in the same interpreter used to start model_deploy, for example: "
        f"pip install --force-reinstall \"numpy=={EXPECTED_NUMPY_VERSION}\" "
        f"\"onnxruntime=={EXPECTED_ONNXRUNTIME_VERSION}\". "
        f"Original error: {error_text}"
    )

    lowered = error_text.lower()
    if "_array_api" in lowered or "compiled using numpy 1.x" in lowered:
        return "Detected a NumPy/onnxruntime ABI mismatch. " + guidance
    return guidance
