from typing import Optional
import yaml
from pydantic import BaseModel

class Coco8Dataset(BaseModel):
    path: str
    train: str
    val: str
    test: Optional[str] = None
    names: dict
    download: Optional[str] = None

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        return cls(
            path=data["path"],
            train=data["train"],
            val=data["val"],
            test=data.get("test"),
            names=data["names"],
            download=data.get("download"),
        )

    def to_yaml(self, file_path: str):
        with open(file_path, "w") as f:
            yaml.dump(self.dict(), f, default_flow_style=False, allow_unicode=True)

    def __repr__(self):
        return f"Coco8Dataset(path={self.path}, train={self.train}, val={self.val}, test={self.test}, download={self.download})"

# 示例用法
# dataset = Coco8Dataset.from_yaml("coco8.yaml")
# print(dataset)
