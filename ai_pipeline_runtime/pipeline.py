from __future__ import annotations

import logging
from typing import Any, Callable

from models import (
    ExecuteCapabilityRequest,
    PipelineDefinition,
    PipelineRunResult,
    StepExecutionResult,
    TaskPayload,
)

logger = logging.getLogger(__name__)


class PipelineRunner:
    def __init__(
        self,
        executor: Callable[[str, ExecuteCapabilityRequest], Any],
    ) -> None:
        self._executor = executor

    def run(self, definition: PipelineDefinition, payload: TaskPayload) -> PipelineRunResult:
        return self.run_with_options(definition, payload)

    def run_with_options(
        self,
        definition: PipelineDefinition,
        payload: TaskPayload,
        *,
        params: dict[str, Any] | None = None,
    ) -> PipelineRunResult:
        context: dict[str, Any] = {"input": payload}
        step_results: list[StepExecutionResult] = []
        runtime_params = params or {}
        logger.info(
            "Pipeline run start pipeline=%s steps=%s params_keys=%s",
            definition.name,
            len(definition.steps),
            sorted(runtime_params.keys()),
        )
        scoped_param_keys = {
            "*",
            *(step.name for step in definition.steps),
            *(step.capability for step in definition.steps),
        }
        global_params = {
            key: value
            for key, value in runtime_params.items()
            if key not in scoped_param_keys
        }

        for step in definition.steps:
            step_input = self._build_step_input(
                step.input_key, step.context_mapping, context)
            step_params = dict(step.params)
            step_params.update(global_params)
            step_params.update(runtime_params.get(step.name, {}))
            step_params.update(runtime_params.get(step.capability, {}))
            step_params.update(runtime_params.get("*", {}))
            logger.info(
                "Pipeline step start pipeline=%s step=%s capability=%s provider=%s provider_role=%s input_key=%s context_mapping_keys=%s params_keys=%s",
                definition.name,
                step.name,
                step.capability,
                step.provider,
                step.provider_role,
                step.input_key,
                sorted(step.context_mapping.keys()),
                sorted(step_params.keys()),
            )
            result = self._executor(
                step.capability,
                ExecuteCapabilityRequest(
                    provider=step.provider,
                    provider_role=step.provider_role,
                    input=step_input,
                    params=step_params,
                ),
            )
            output_key = step.output_key or step.name
            context[output_key] = result
            step_results.append(
                StepExecutionResult(
                    name=step.name,
                    capability=step.capability,
                    output_key=output_key,
                )
            )
            logger.info(
                "Pipeline step end pipeline=%s step=%s output_key=%s output_type=%s",
                definition.name,
                step.name,
                output_key,
                type(result).__name__,
            )

        logger.info(
            "Pipeline run end pipeline=%s step_count=%s context_keys=%s",
            definition.name,
            len(step_results),
            sorted(context.keys()),
        )
        return PipelineRunResult(
            pipeline=definition.name,
            description=definition.description,
            steps=step_results,
            context={key: self._to_jsonable(value)
                     for key, value in context.items()},
        )

    def _build_step_input(
        self, input_key: str, context_mapping: dict[str, str], context: dict[str, Any]
    ) -> TaskPayload:
        base_input = self._resolve_context_value(input_key, context)
        if base_input is None:
            raise ValueError(
                f"pipeline input key `{input_key}` does not exist")
        if isinstance(base_input, TaskPayload):
            payload = base_input.model_copy(deep=True)
        elif isinstance(base_input, dict):
            payload = TaskPayload.model_validate(base_input)
        else:
            raise ValueError(
                f"pipeline input key `{input_key}` must resolve to TaskPayload-compatible data"
            )

        for target_field, source_key in context_mapping.items():
            value = self._resolve_context_value(source_key, context)
            if hasattr(value, "model_dump"):
                value = value.model_dump(mode="json")

            if target_field == "metadata":
                metadata = dict(payload.metadata)
                if isinstance(value, dict):
                    metadata.update(value)
                else:
                    metadata[source_key] = value
                payload.metadata = metadata
                continue

            setattr(payload, target_field, value)
        return TaskPayload.model_validate(payload.model_dump(mode="json", warnings=False))

    def _to_jsonable(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        return value

    def _resolve_context_value(self, key: str, context: dict[str, Any]) -> Any:
        if key in context:
            return context[key]

        current: Any = context
        for part in key.split("."):
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
                continue
            if hasattr(current, part):
                current = getattr(current, part)
                continue
            if hasattr(current, "model_dump"):
                current = current.model_dump(mode="json")
                if isinstance(current, dict) and part in current:
                    current = current[part]
                    continue
            return None
        return current
