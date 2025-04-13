from objectbox import *


@Entity()
class TaskLog:
    id = Id()
    task_id = String()  # UUID
    content = String()
    Date(py_type=int)
