from sqlalchemy.orm import Session

from base.deprecated import deprecated
from db.task.task import Task


def get_task(db: Session, task_id: int) -> Task:
    return db.query(Task).filter_by(task_id=task_id, is_deleted=0).first()


@deprecated("This function is un used in python, use java instead.")
def delete_task(db: Session, task_id: int):
    task = db.query(Task).filter_by(task_id=task_id).first()
    if task:
        task.is_deleted = 1
        db.commit()
    return task
