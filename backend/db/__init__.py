from typing import Optional
from objectbox import Box, Store
from db.task import Task
from db.task_log import TaskLog


class DB:
    __store: Optional[Store] = None
    task_box: Optional[Box] = None
    task_log_box: Optional[Box] = None

    @staticmethod
    def init():
        if DB.__store:
            return
        DB.__store = Store(directory="automl-db")
        DB.task_box = DB.__store.box(Task)
        DB.task_log_box = DB.__store.box(TaskLog)

    @staticmethod
    def close():
        if DB.__store:
            DB.__store.close()
