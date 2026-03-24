"""业务模块"""
from .dataset import router as dataset_router
from .annotation import router as annotation_router
from .task import router as task_router
from .deploy import router as deploy_router
from .predict import router as predict_router
from .aether import router as aether_router
from .tool import router as tool_router
from .augment import router as augment_router
from .home import router as home_router

__all__ = [
    "dataset_router",
    "annotation_router",
    "task_router",
    "deploy_router",
    "predict_router",
    "aether_router",
    "tool_router",
    "augment_router",
    "home_router",
]
