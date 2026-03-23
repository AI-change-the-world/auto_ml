from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from db.models import AvailableModel, Task, TaskLog


def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter_by(task_id=task_id, is_deleted=0).first()


def update_task(db: Session, task_id: int, updates: Dict[str, Any]) -> Optional[Task]:
    task = db.query(Task).filter_by(task_id=task_id, is_deleted=0).first()
    if not task:
        return None
    for key, value in updates.items():
        if hasattr(task, key):
            setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def create_task_log(db: Session, task_id: int, log_content: str) -> TaskLog:
    log = TaskLog(task_id=task_id, log_content=log_content)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_task_logs(db: Session, task_id: int) -> List[TaskLog]:
    return db.query(TaskLog).filter_by(task_id=task_id).order_by(TaskLog.created_at).all()


def get_available_model(db: Session, model_id: int) -> Optional[AvailableModel]:
    return (
        db.query(AvailableModel)
        .filter_by(available_model_id=model_id, is_deleted=0)
        .first()
    )


def create_available_model(db: Session, model_data: Dict[str, Any]) -> AvailableModel:
    model = AvailableModel(**model_data)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_available_model(
    db: Session, model_id: int, updates: Dict[str, Any]
) -> Optional[AvailableModel]:
    model = (
        db.query(AvailableModel)
        .filter_by(available_model_id=model_id, is_deleted=0)
        .first()
    )
    if not model:
        return None
    for key, value in updates.items():
        if hasattr(model, key):
            setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model
