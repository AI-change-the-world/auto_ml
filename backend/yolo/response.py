from pydantic import BaseModel


# 定义 Box 模型
class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


# 定义主模型
class PredictResult(BaseModel):
    name: str
    obj_class: int
    confidence: float
    box: Box

    @classmethod
    def from_dict(cls, data):
        new_dict: dict = {}
        for key, value in data.items():
            if key == "class":
                # new_dict[key] = Box(**value)
                new_dict["obj_class"] = value
            else:
                new_dict[key] = value
        return cls(**new_dict)


class PredictResults(BaseModel):
    image_id: str
    results: list[PredictResult]

    @classmethod
    def from_data(cls, data:list,img:str):
        p : PredictResults  = PredictResults(image_id=img, results=[])
        for r in data:
            p.results.append(PredictResult.from_dict(r))
        
        return p
            
