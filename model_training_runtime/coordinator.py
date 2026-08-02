"""Internal, non-network execution coordination for approved training packages.

The HTTP application uses this coordinator for the experimental direct
execution endpoint. It deliberately does not consume MQ messages or claim
production task state yet.

The service subprocess is a bounded execution mechanism, not a security
boundary for arbitrary user code. A future container or Job backend can be
added after the direct path is validated.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import ValidationError

from admission import ContractAdmissionError, validate_execution_admission, validate_result_admission
from contracts import (
    EXECUTION_PROTOCOL_VERSION,
    ExecutionWorkspace,
    TrainingCodeSubmission,
    TrainingDatasetSourceManifest,
    TrainingExecutionRequest,
    TrainingPackageManifest,
    TrainingResult,
)
from package_validation import PackageArchiveValidationError, validate_package_archive
from runtime import (
    ExecutionLaunch,
    LocalSubprocessExecutor,
    PlatformRuntimeManager,
    ProcessResult,
    RunnerProtocolError,
    RuntimeExecutionError,
    extract_training_package,
    parse_runner_line,
    TrainingExecutor,
)
from storage import DatasetMaterializer, ModelInputMaterializer, ObjectStorage, ObjectStorageError


class ExecutionCoordinatorError(RuntimeExecutionError):
    """The coordinator could not produce one verified terminal outcome."""


@dataclass(frozen=True)
class ExecutionOutcome:
    """Verified in-memory outcome of one local coordinator invocation.

    ``execution`` retains the portable ``/workspace`` paths from the contract.
    ``workspace_root`` is only for the internal caller's inspection and must
    not be exposed to package code or external API consumers.
    """

    execution: TrainingExecutionRequest
    result: TrainingResult
    events: tuple[dict[str, Any], ...]
    logs: tuple[dict[str, Any], ...]
    process: ProcessResult
    workspace_root: Path


class ExecutionCoordinator:
    """Coordinates one executor-backed training run from immutable inputs.

    The caller supplies a submission whose archive and dataset snapshot have
    already been registered and content-pinned.  The coordinator never accepts
    an arbitrary local package path, package-defined Python executable, or
    package-provided storage configuration.
    """

    def __init__(
        self,
        storage: ObjectStorage,
        runtime_manager: PlatformRuntimeManager,
        *,
        executor: TrainingExecutor | None = None,
        runner_path: Path | None = None,
    ) -> None:
        self.storage = storage
        self.runtime_manager = runtime_manager
        if executor is not None and runner_path is not None:
            raise ValueError("executor and runner_path cannot be supplied together")
        self.executor = executor or LocalSubprocessExecutor(runner_path=runner_path)

    async def execute(self, submission: TrainingCodeSubmission) -> ExecutionOutcome:
        """Run one admitted submission and return its verified terminal result.

        Device support is explicit in the selected executor. The direct service
        executor supports CPU and CUDA when the service deployment exposes it;
        physical GPU allocation remains platform-controlled.
        """
        if submission.resources.device not in self.executor.supported_devices:
            raise self._error(
                "validate_resources",
                "UnsupportedExecutorDevice",
                f"selected executor does not support `{submission.resources.device}` executions",
            )

        task_root = self._create_task_workspace(str(submission.execution_id))
        try:
            return await self._execute_in_workspace(submission, task_root)
        except ExecutionCoordinatorError:
            raise
        except RuntimeExecutionError as exc:
            raise self._error_from_runtime(exc) from exc
        except RunnerProtocolError as exc:
            raise self._error("parse_runner_output", "RunnerProtocolError", str(exc)) from exc
        except (
            ContractAdmissionError,
            ObjectStorageError,
            PackageArchiveValidationError,
            ValidationError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            OSError,
            ValueError,
        ) as exc:
            raise self._error("coordinate_execution", exc.__class__.__name__, str(exc)) from exc

    async def _execute_in_workspace(
        self,
        submission: TrainingCodeSubmission,
        task_root: Path,
    ) -> ExecutionOutcome:
        archive_bytes = await self.storage.read(submission.package_archive)
        report = validate_package_archive(archive_bytes)
        manifest = report.manifest
        self._verify_submission_package(submission, manifest, report.sha256)

        source_manifest = await self._load_source_snapshot(submission)
        code_dir = task_root / "code"
        input_dir = task_root / "input"
        output_dir = task_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        archive_path = task_root / "package.zip"
        archive_path.write_bytes(archive_bytes)
        extract_training_package(archive_path, code_dir)
        dataset = await DatasetMaterializer(self.storage).materialize(source_manifest, input_dir)

        model_input_path: Path | None = None
        if submission.model_input is not None:
            file_name = PurePosixPath(submission.model_input.artifact.object.object_key).name
            model_input_path = await ModelInputMaterializer(self.storage).materialize(
                submission.model_input.artifact.object,
                input_dir,
                file_name=file_name,
            )

        execution = self._build_execution(
            submission=submission,
            manifest=manifest,
            dataset=dataset,
            model_input_path=model_input_path,
        )
        validate_execution_admission(manifest, execution)

        prepared_runtime = self.runtime_manager.prepare(
            task_root=task_root,
            runtime_id=submission.runtime.id,
        )
        messages: list[tuple[str, dict[str, Any]]] = []

        def on_line(stream: str, line: str) -> None:
            if stream != "stdout":
                return
            message = parse_runner_line(line)
            if message is not None:
                messages.append((message.channel, message.payload))

        process = await self.executor.execute(
            ExecutionLaunch(
                execution=execution,
                task_root=task_root,
                code_dir=code_dir,
                input_dir=input_dir,
                output_dir=output_dir,
                entrypoint_path=code_dir / manifest.entrypoint,
                prepared_runtime=prepared_runtime,
                runtime_settings=self.runtime_manager.settings,
                model_input_path=model_input_path,
            ),
            line_callback=on_line,
        )
        result, events, logs = self._collect_terminal_messages(execution, messages)
        self._verify_result_file(output_dir, result)
        self._verify_artifact_files(output_dir, result)
        validate_result_admission(manifest, execution, result)
        self._verify_process_status(process, result)
        return ExecutionOutcome(
            execution=execution,
            result=result,
            events=tuple(events),
            logs=tuple(logs),
            process=process,
            workspace_root=task_root,
        )

    async def _load_source_snapshot(
        self,
        submission: TrainingCodeSubmission,
    ) -> TrainingDatasetSourceManifest:
        try:
            payload = await self.storage.read(submission.dataset_source_snapshot)
            return TrainingDatasetSourceManifest.model_validate_json(payload)
        except (ValidationError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise self._error(
                "resolve_dataset_snapshot",
                "InvalidDatasetSnapshot",
                "registered dataset source snapshot is not a valid training dataset source manifest",
            ) from exc

    @staticmethod
    def _verify_submission_package(
        submission: TrainingCodeSubmission,
        manifest: TrainingPackageManifest,
        archive_sha256: str,
    ) -> None:
        if submission.package_archive.sha256 != archive_sha256:
            raise ExecutionCoordinator._error(
                "resolve_package",
                "PackageDigestMismatch",
                "package archive digest does not match the submitted immutable archive reference",
            )
        if submission.package.sha256 != archive_sha256:
            raise ExecutionCoordinator._error(
                "resolve_package",
                "PackageDigestMismatch",
                "submitted package digest does not match the immutable package archive",
            )
        if (submission.package.key, submission.package.version) != (manifest.key, manifest.version):
            raise ExecutionCoordinator._error(
                "resolve_package",
                "PackageIdentityMismatch",
                "submitted package key and version do not match the package archive manifest",
            )
        if submission.runtime != manifest.runtime:
            raise ExecutionCoordinator._error(
                "resolve_package",
                "PackageRuntimeMismatch",
                "submitted runtime does not match the package archive manifest",
            )

    @staticmethod
    def _build_execution(
        *,
        submission: TrainingCodeSubmission,
        manifest: TrainingPackageManifest,
        dataset,
        model_input_path: Path | None,
    ) -> TrainingExecutionRequest:
        workspace = ExecutionWorkspace(
            root_dir="/workspace",
            code_dir="/workspace/code",
            input_dir="/workspace/input",
            output_dir="/workspace/output",
            dataset_manifest_path="/workspace/input/dataset-manifest.json",
        )
        return TrainingExecutionRequest(
            protocol_version=EXECUTION_PROTOCOL_VERSION,
            execution_id=submission.execution_id,
            task=submission.task,
            package=submission.package,
            runtime=submission.runtime,
            workspace=workspace,
            dataset=dataset,
            parameters=submission.parameters,
            resources=submission.resources,
            model_input=submission.model_input,
            model_input_path=(
                (PurePosixPath("/workspace/input") / "model-input" / model_input_path.name).as_posix()
                if model_input_path is not None
                else None
            ),
            package_manifest=manifest,
        )

    def _collect_terminal_messages(
        self,
        execution: TrainingExecutionRequest,
        messages: list[tuple[str, dict[str, Any]]],
    ) -> tuple[TrainingResult, list[dict[str, Any]], list[dict[str, Any]]]:
        events: list[dict[str, Any]] = []
        logs: list[dict[str, Any]] = []
        results: list[TrainingResult] = []
        expected_sequence = 0
        for channel, payload in messages:
            if channel == "event":
                if payload["execution_id"] != str(execution.execution_id):
                    raise self._error(
                        "parse_runner_output",
                        "UnexpectedExecutionId",
                        "runner emitted an event for a different execution",
                    )
                if payload["sequence"] != expected_sequence:
                    raise self._error(
                        "parse_runner_output",
                        "InvalidEventSequence",
                        "runner event sequences must begin at 0 and be contiguous",
                    )
                expected_sequence += 1
                events.append(payload)
            elif channel == "log":
                logs.append(payload)
            elif channel == "result":
                result = TrainingResult.model_validate(payload)
                if result.execution_id != execution.execution_id:
                    raise self._error(
                        "parse_runner_output",
                        "UnexpectedExecutionId",
                        "runner emitted a result for a different execution",
                    )
                results.append(result)
            else:
                raise self._error(
                    "parse_runner_output",
                    "UnknownProtocolChannel",
                    f"runner emitted unsupported protocol channel `{channel}`",
                )
        if len(results) != 1:
            raise self._error(
                "parse_runner_output",
                "InvalidTerminalResultCount",
                "runner must emit exactly one terminal result",
            )
        return results[0], events, logs

    def _verify_result_file(self, output_dir: Path, emitted_result: TrainingResult) -> None:
        result_path = output_dir / "result.json"
        try:
            stored_result = TrainingResult.model_validate_json(result_path.read_bytes())
        except (OSError, ValidationError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise self._error(
                "verify_result",
                "MissingOrInvalidResultFile",
                "runner did not write a valid result.json below the output directory",
            ) from exc
        if stored_result != emitted_result:
            raise self._error(
                "verify_result",
                "ResultMismatch",
                "runner result protocol output does not match output/result.json",
            )

    def _verify_artifact_files(self, output_dir: Path, result: TrainingResult) -> None:
        output_root = output_dir.resolve()
        for artifact in result.artifacts:
            artifact_path = (output_dir / PurePosixPath(artifact.path)).resolve()
            try:
                artifact_path.relative_to(output_root)
            except ValueError as exc:
                raise self._error(
                    "verify_artifacts",
                    "ArtifactWorkspaceEscape",
                    f"artifact `{artifact.path}` escapes the output directory",
                ) from exc
            if not artifact_path.is_file():
                raise self._error(
                    "verify_artifacts",
                    "MissingArtifact",
                    f"declared artifact `{artifact.path}` does not exist",
                )
            if artifact_path.stat().st_size != artifact.size_bytes:
                raise self._error(
                    "verify_artifacts",
                    "ArtifactSizeMismatch",
                    f"declared artifact `{artifact.path}` has an unexpected size",
                )
            if artifact.sha256 is None or self._file_sha256(artifact_path) != artifact.sha256:
                raise self._error(
                    "verify_artifacts",
                    "ArtifactDigestMismatch",
                    f"declared artifact `{artifact.path}` has an unexpected SHA-256",
                )

    def _verify_process_status(self, process: ProcessResult, result: TrainingResult) -> None:
        if result.status == "succeeded" and process.return_code != 0:
            raise self._error(
                "verify_process",
                "SuccessfulResultWithFailedProcess",
                "runner reported success but exited with a non-zero status",
            )
        if result.status != "succeeded" and process.return_code == 0:
            raise self._error(
                "verify_process",
                "FailedResultWithSuccessfulProcess",
                "runner reported a non-success result but exited successfully",
            )

    def _create_task_workspace(self, execution_id: str) -> Path:
        workspace_root = self.runtime_manager.settings.workspace_root.resolve()
        task_root = workspace_root / execution_id
        try:
            workspace_root.mkdir(parents=True, exist_ok=True)
            task_root.mkdir()
        except FileExistsError as exc:
            raise self._error(
                "prepare_workspace",
                "ExecutionWorkspaceExists",
                f"workspace already exists for execution `{execution_id}`",
            ) from exc
        except OSError as exc:
            raise self._error(
                "prepare_workspace",
                exc.__class__.__name__,
                f"unable to create execution workspace: {exc}",
            ) from exc
        return task_root

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _error(stage: str, error_type: str, message: str) -> ExecutionCoordinatorError:
        return ExecutionCoordinatorError(
            message,
            {
                "source": "model_training_runtime",
                "stage": stage,
                "exception_type": error_type,
                "message": message,
            },
        )

    @staticmethod
    def _error_from_runtime(exc: RuntimeExecutionError) -> ExecutionCoordinatorError:
        detail = dict(exc.error_detail)
        detail["source"] = "model_training_runtime"
        return ExecutionCoordinatorError(str(exc), detail)
