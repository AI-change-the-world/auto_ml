from objectbox import *


@Entity()
class Task:
    id = Id()
    task_id = String()  # UUID
    status = String()  # 状态: pending / running / complete
    Date(py_type=int)
