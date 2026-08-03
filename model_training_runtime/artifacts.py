"""Persist verified runtime outputs before their task workspace is removed."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from contracts import ArtifactResult, S3ObjectReference, StorageBucket
from coordinator import ExecutionOutcome
from storage import ObjectStorage, content_reference


@dataclass(frozen=True)
class PersistedArtifact:
    artifact: ArtifactResult
    object: S3ObjectReference


async def persist_execution_artifacts(
    storage: ObjectStorage,
    outcome: ExecutionOutcome,
) -> tuple[PersistedArtifact, ...]:
    """Store the already-verified output contract artifacts immutably.

    The coordinator verifies every output file and digest before this function
    runs.  Artifact object keys are deterministic by execution and digest, so
    RabbitMQ delivery retries cannot overwrite a different result.
    """
    persisted: list[PersistedArtifact] = []
    output_dir = outcome.workspace_root / "output"
    for artifact in outcome.result.artifacts:
        content = (output_dir / artifact.path).read_bytes()
        bucket = (
            StorageBucket.MODELS
            if artifact.role.value in {"model", "checkpoint"}
            else StorageBucket.DEFAULT
        )
        reference = content_reference(
            bucket,
            _artifact_object_key(
                execution_id=str(outcome.execution.execution_id),
                artifact=artifact,
            ),
            content,
        )
        if not await storage.exists(reference):
            await storage.write(reference, content)
        persisted.append(PersistedArtifact(artifact=artifact, object=reference))
    return tuple(persisted)


def _artifact_object_key(*, execution_id: str, artifact: ArtifactResult) -> str:
    file_name = PurePosixPath(artifact.path).name
    safe_name = "".join(
        character if character.isalnum() or character in {"-", "_", "."} else "_"
        for character in file_name
    ).strip("._") or "artifact"
    return (
        f"training-code-runtime/executions/{execution_id}/"
        f"{artifact.sha256}/{safe_name}"
    )
