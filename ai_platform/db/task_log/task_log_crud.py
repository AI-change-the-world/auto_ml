from sqlalchemy.orm import Session

from db.task_log.task_log import TaskLog
from db.task_log.task_log_schema import TaskLogCreate


def create_log(db: Session, log: TaskLogCreate) -> TaskLog:
    db_log = TaskLog(**log.model_dump())
    db.merge(db_log)  # 如果 task_id 已存在则更新
    db.commit()
    return db_log


def get_log(db: Session, task_id: int) -> TaskLog:
    return db.query(TaskLog).filter_by(task_id=task_id).first()


def delete_log(db: Session, task_id: int):
    log = db.query(TaskLog).filter_by(task_id=task_id).first()
    if log:
        db.delete(log)
        db.commit()
    return log
