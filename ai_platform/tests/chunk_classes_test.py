from typing import List


def _chunk_classes() -> List[List[str]]:
    return [classes[i : i + batch_size] for i in range(0, len(classes), batch_size)]


classes = ["1", "2"]

batch_size = 10


print(_chunk_classes())
