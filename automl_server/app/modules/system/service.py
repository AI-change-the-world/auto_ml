"""系统能力聚合服务"""
from typing import Dict, Optional

from app.config.settings import get_settings
from app.utils.http_client import HttpClient

from .schemas import (
    CapabilityActionState,
    CapabilityModuleState,
    CapabilityServiceHealth,
    CapabilitySnapshotResponse,
)
from .runtime import get_capability_runtime_state


class SystemCapabilityService:
    """聚合子服务在线能力，供前端做 capability 控制。"""

    @staticmethod
    def _disabled_reason(label: str) -> str:
        return f"{label} disabled by platform capability config"

    @staticmethod
    def _resolve_allowed(enabled: bool, available: bool, offline_reason: Optional[str], label: str) -> tuple[bool, Optional[str]]:
        if not enabled:
            return False, SystemCapabilityService._disabled_reason(label)
        if not available:
            return False, offline_reason
        return True, None

    async def _probe_health(self, label: str, base_url: str) -> CapabilityServiceHealth:
        client = HttpClient(base_url=base_url, timeout=5)
        try:
            response = await client.get("/health")
            if response.status_code != 200:
                return CapabilityServiceHealth(
                    key=label,
                    label=label,
                    available=False,
                    reason=f"{label} returned HTTP {response.status_code}",
                    raw_status=None,
                )

            payload = response.json()
            raw_status = payload.get("status") if isinstance(payload, dict) else None
            available = raw_status in {"healthy", "ok"}
            reason = None if available else f"{label} status={raw_status or 'unknown'}"
            return CapabilityServiceHealth(
                key=label,
                label=label,
                available=available,
                reason=reason,
                raw_status=raw_status,
            )
        except Exception as exc:
            return CapabilityServiceHealth(
                key=label,
                label=label,
                available=False,
                reason=f"{label} unreachable: {exc}",
                raw_status=None,
            )
        finally:
            await client.close()

    def _module_state(
        self,
        available: bool,
        reason: Optional[str],
        actions: Dict[str, tuple[bool, Optional[str]]],
    ) -> CapabilityModuleState:
        return CapabilityModuleState(
            available=available,
            reason=reason,
            actions={
                key: CapabilityActionState(allowed=allowed, reason=action_reason)
                for key, (allowed, action_reason) in actions.items()
            },
        )

    async def get_capability_snapshot(self) -> CapabilitySnapshotResponse:
        settings = get_settings()
        runtime_state = get_capability_runtime_state()
        capability_config = runtime_state.get_config()
        version, updated_at = runtime_state.get_meta()
        trainer_health = await self._probe_health(
            "model_trainer",
            settings.model_trainer.base_url,
        )
        deploy_health = await self._probe_health(
            "model_deploy",
            settings.model_deploy.base_url,
        )
        assist_health = await self._probe_health(
            "auto_augment_pipeline",
            settings.auto_augment_pipeline.base_url,
        )

        training_reason = trainer_health.reason
        deploy_reason = deploy_health.reason
        assist_reason = assist_health.reason
        dataset_enabled = capability_config.dataset.enabled
        annotation_enabled = capability_config.annotation.enabled
        training_enabled = capability_config.training.enabled
        deployment_enabled = capability_config.deployment.enabled
        dataset_reason = None if dataset_enabled else self._disabled_reason("dataset")
        annotation_reason = None if annotation_enabled else self._disabled_reason("annotation")
        training_module_available = training_enabled and trainer_health.available
        deployment_module_available = deployment_enabled and deploy_health.available
        assist_allowed, assist_action_reason = self._resolve_allowed(
            annotation_enabled,
            assist_health.available,
            assist_reason,
            "annotation assist",
        )
        create_task_allowed, create_task_reason = self._resolve_allowed(
            training_enabled,
            trainer_health.available,
            training_reason,
            "training",
        )
        deploy_allowed, deploy_action_reason = self._resolve_allowed(
            deployment_enabled,
            deploy_health.available,
            deploy_reason,
            "deployment",
        )

        return CapabilitySnapshotResponse(
            version=version,
            updated_at=updated_at,
            services={
                "model_trainer": trainer_health,
                "model_deploy": deploy_health,
                "auto_augment_pipeline": assist_health,
            },
            modules={
                "dataset": self._module_state(
                    available=dataset_enabled,
                    reason=dataset_reason,
                    actions={
                        "browse": (dataset_enabled, dataset_reason),
                        "create": (dataset_enabled, dataset_reason),
                        "upload": (dataset_enabled, dataset_reason),
                    },
                ),
                "annotation": self._module_state(
                    available=annotation_enabled,
                    reason=annotation_reason,
                    actions={
                        "manual_label": (annotation_enabled, annotation_reason),
                        "assist_label": (assist_allowed, assist_action_reason),
                    },
                ),
                "training": self._module_state(
                    available=training_module_available,
                    reason=create_task_reason,
                    actions={
                        "create_task": (create_task_allowed, create_task_reason),
                        "view_history": (training_enabled, None if training_enabled else self._disabled_reason("training")),
                        "view_detail": (training_enabled, None if training_enabled else self._disabled_reason("training")),
                    },
                ),
                "deployment": self._module_state(
                    available=deployment_module_available,
                    reason=deploy_action_reason,
                    actions={
                        "list_models": (deployment_enabled, None if deployment_enabled else self._disabled_reason("deployment")),
                        "deploy_model": (deploy_allowed, deploy_action_reason),
                        "undeploy_model": (deploy_allowed, deploy_action_reason),
                        "predict": (deploy_allowed, deploy_action_reason),
                        "view_api": (deploy_allowed, deploy_action_reason),
                        "upload_onnx": (deploy_allowed, deploy_action_reason),
                    },
                ),
            },
        )


_service = SystemCapabilityService()


def get_system_capability_service() -> SystemCapabilityService:
    return _service
