"""业务模块"""
from .dataset import router as dataset_router
from .annotation import router as annotation_router
from .task import router as task_router
from .deploy import router as deploy_router
from .inference import router as inference_router
from .home import router as home_router
from .system import router as system_router

__all__ = [
    "dataset_router",
    "annotation_router",
    "task_router",
    "deploy_router",
    "inference_router",
    "home_router",
    "system_router",
]
