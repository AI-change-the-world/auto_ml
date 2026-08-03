"""Semantic admission checks shared by package upload, worker, and MQ paths."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator, SchemaError
from contracts import TrainingExecutionRequest, TrainingPackageManifest, TrainingResult


class ContractAdmissionError(ValueError):
    """Two independently valid contracts are incompatible with each other."""


def validate_package_manifest(manifest: TrainingPackageManifest) -> None:
    """Validate semantic rules that Pydantic cannot express for a JSON Schema."""
    try:
        Draft202012Validator.check_schema(manifest.parameters_schema)
    except SchemaError as exc:
        raise ContractAdmissionError(f"parameters_schema is not valid JSON Schema: {exc.message}") from exc


def validate_execution_admission(
    manifest: TrainingPackageManifest,
    execution: TrainingExecutionRequest,
) -> None:
    """Verify that a resolved package is allowed to receive this execution."""
    validate_package_manifest(manifest)
    if manifest.key != execution.package.key or manifest.version != execution.package.version:
        raise ContractAdmissionError("execution.package key and version must match the package manifest")
    if manifest.runtime != execution.runtime:
        raise ContractAdmissionError("execution.runtime must match the package manifest runtime")
    if execution.input_mode not in manifest.input_modes:
        raise ContractAdmissionError(
            f"package does not declare input_mode `{execution.input_mode.value}`"
        )
    _validate_workspace(execution)
    _validate_supported_task(manifest, execution)
    _validate_parameters(manifest, execution.parameters)
    _validate_model_input(manifest, execution)


def validate_result_admission(
    manifest: TrainingPackageManifest,
    execution: TrainingExecutionRequest,
    result: TrainingResult,
) -> None:
    """Verify that a successful package result fulfills its declared output contract."""
    validate_execution_admission(manifest, execution)
    if result.execution_id != execution.execution_id:
        raise ContractAdmissionError("result.execution_id must match execution.execution_id")
    if result.status != "succeeded":
        return

    declarations = {
        (declaration.role, declaration.deployable): declaration
        for declaration in manifest.output_contract.artifacts
    }
    seen_declarations: set[tuple[object, bool]] = set()
    for artifact in result.artifacts:
        key = (artifact.role, artifact.deployable)
        declaration = declarations.get(key)
        if declaration is None:
            raise ContractAdmissionError(
                f"artifact `{artifact.path}` has undeclared role/deployable combination "
                f"`{artifact.role.value}`/{artifact.deployable}"
            )
        if key in seen_declarations:
            raise ContractAdmissionError(
                f"multiple result artifacts match declared `{artifact.role.value}`/{artifact.deployable}"
            )
        seen_declarations.add(key)
        if artifact.format not in declaration.formats:
            raise ContractAdmissionError(
                f"artifact `{artifact.path}` format `{artifact.format}` is not declared for "
                f"`{artifact.role.value}`/{artifact.deployable}"
            )

    missing = [
        declaration
        for key, declaration in declarations.items()
        if declaration.required and key not in seen_declarations
    ]
    if missing:
        labels = ", ".join(f"{item.role.value}/{item.deployable}" for item in missing)
        raise ContractAdmissionError(f"successful result is missing required artifacts: {labels}")

    if manifest.output_contract.requires_model_metadata and result.model is None:
        raise ContractAdmissionError("package output contract requires model metadata")
    if result.model is not None:
        if result.model.task_kind != execution.task.task_kind:
            raise ContractAdmissionError("result.model.task_kind must match execution.task.task_kind")
        if result.model.class_names != execution.dataset.class_names:
            raise ContractAdmissionError("result.model.class_names must match execution.dataset.class_names")
        checkpoint_path = result.model.resume_checkpoint_path
        if checkpoint_path is not None:
            matching = [
                artifact
                for artifact in result.artifacts
                if artifact.path == checkpoint_path and artifact.role.value == "checkpoint"
            ]
            if len(matching) != 1:
                raise ContractAdmissionError(
                    "result.model.resume_checkpoint_path must reference one checkpoint artifact"
                )


def _validate_supported_task(
    manifest: TrainingPackageManifest,
    execution: TrainingExecutionRequest,
) -> None:
    task_kind = execution.task.task_kind
    compatible = [item for item in manifest.supported_tasks if item.task_kind == task_kind]
    if not compatible:
        raise ContractAdmissionError(f"package does not support task_kind `{task_kind}`")
    dataset_modalities = set(execution.dataset.data_modalities)
    dataset_annotations = set(execution.dataset.annotation_kinds)
    for supported in compatible:
        if dataset_modalities.issubset(supported.data_modalities) and dataset_annotations.issubset(supported.annotation_kinds):
            return
    raise ContractAdmissionError(
        "package does not support this dataset's data_modalities or annotation_kinds"
    )


def _validate_parameters(manifest: TrainingPackageManifest, parameters: dict[str, Any]) -> None:
    validator = Draft202012Validator(manifest.parameters_schema)
    errors = sorted(validator.iter_errors(parameters), key=lambda error: list(error.absolute_path))
    if not errors:
        return
    error = errors[0]
    location = "$parameters"
    for part in error.absolute_path:
        location += f"[{part!r}]" if isinstance(part, int) else f".{part}"
    raise ContractAdmissionError(f"parameters violate package schema at {location}: {error.message}")


def _validate_model_input(
    manifest: TrainingPackageManifest,
    execution: TrainingExecutionRequest,
) -> None:
    contract = manifest.model_input_contract
    model_input = execution.model_input
    if contract is None:
        if model_input is not None:
            raise ContractAdmissionError("package does not declare a model_input_contract")
        return
    if contract.required and model_input is None:
        raise ContractAdmissionError("package requires a base model or resume checkpoint input")
    if model_input is None:
        return
    artifact = model_input.artifact
    if artifact.framework != contract.framework:
        raise ContractAdmissionError(
            "model input framework must match the package model_input_contract framework"
        )
    if artifact.format not in contract.formats:
        raise ContractAdmissionError(
            f"model input format `{artifact.format}` is not declared by the package"
        )
    if model_input.mode not in contract.modes:
        raise ContractAdmissionError(
            f"model input mode `{model_input.mode.value}` is not declared by the package"
        )
    if model_input.mode.value == "resume" and not artifact.resume_supported:
        raise ContractAdmissionError("resume model input must provide a resumable checkpoint artifact")
    if contract.require_matching_task_kind and artifact.task_kind != execution.task.task_kind:
        raise ContractAdmissionError("model input task_kind must match execution.task.task_kind")
    if (
        model_input.mode.value == "resume"
        and contract.require_matching_class_names_for_resume
        and artifact.class_names != execution.dataset.class_names
    ):
        raise ContractAdmissionError(
            "resume model class_names must match execution.dataset.class_names"
        )


def _validate_workspace(execution: TrainingExecutionRequest) -> None:
    workspace = execution.workspace
    root = PurePosixPath(workspace.root_dir)
    directories = {
        "code_dir": PurePosixPath(workspace.code_dir),
        "input_dir": PurePosixPath(workspace.input_dir),
        "output_dir": PurePosixPath(workspace.output_dir),
    }
    for name, path in directories.items():
        _require_descendant(path, root, f"workspace.{name}")
    values = list(directories.items())
    for index, (left_name, left_path) in enumerate(values):
        for right_name, right_path in values[index + 1 :]:
            if _is_same_or_descendant(left_path, right_path) or _is_same_or_descendant(right_path, left_path):
                raise ContractAdmissionError(
                    f"workspace.{left_name} and workspace.{right_name} must be separate directories"
                )
    _require_descendant(
        PurePosixPath(workspace.dataset_manifest_path),
        directories["input_dir"],
        "workspace.dataset_manifest_path",
    )


def _require_descendant(path: PurePosixPath, parent: PurePosixPath, label: str) -> None:
    if not _is_same_or_descendant(path, parent):
        raise ContractAdmissionError(f"{label} must be located below {parent}")


def _is_same_or_descendant(path: PurePosixPath, parent: PurePosixPath) -> bool:
    return path == parent or parent in path.parents
