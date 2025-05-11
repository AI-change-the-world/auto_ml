from typing import List, Union

from base.file_delegate import get_operator, s3_properties
from base.logger import logger
from db.tool_model.tool_model import ToolModel
from label.client import ProvidedModelClient, get_model
from yolo.response import PredictResults


def label_with_gd(img_path:str, classes: List[str], tool_model: ToolModel) -> Union[PredictResults, None]:
    op = get_operator(s3_properties.datasets_bucket_name)
    model = get_model(tool_model)
    logger.info(f"label_with_gd model ; model is None : {model is None}  {type(model)}")
    assert model is not None and  isinstance(model, ProvidedModelClient)
    img_data = op.read(img_path)
    res = model.predict(img_data, classes)
    return res