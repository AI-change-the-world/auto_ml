"""
模型运行时服务
每个模型实例作为一个独立的 FastAPI 服务运行
"""
import argparse
import base64
import io
from typing import List, Optional

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from utils.logger import logger


# ============ 请求/响应模型 ============

class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    box: Box


class ClassificationResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float


class PredictResponse(BaseModel):
    success: bool
    results: List[DetectionResult]
    image_width: int
    image_height: int


class ClassifyResponse(BaseModel):
    success: bool
    result: ClassificationResult


class HealthResponse(BaseModel):
    status: str
    model_path: str
    device: str


# ============ 模型推理类 ============

class ONNXRuntime:
    """ONNX 运行时封装"""

    def __init__(self, model_path: str, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.session = None
        self.input_name = None
        self.input_shape = None
        self.class_names = []

        self._load_model()

    def _load_model(self):
        """加载 ONNX 模型"""
        try:
            # 配置运行时会话
            providers = ["CUDAExecutionProvider"] if self.device == "cuda" else [
                "CPUExecutionProvider"]
            self.session = ort.InferenceSession(
                self.model_path, providers=providers)

            # 获取输入信息
            input_meta = self.session.get_inputs()[0]
            self.input_name = input_meta.name
            self.input_shape = input_meta.shape

            logger.info(f"Model loaded: {self.model_path}")
            logger.info(f"Input shape: {self.input_shape}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def preprocess(self, image: Image.Image) -> np.ndarray:
        """预处理图像"""
        # 获取输入尺寸
        input_size = self.input_shape[2] if self.input_shape[2] else 640

        # 调整图像大小
        image = image.resize((input_size, input_size))

        # 转换为 numpy 数组
        img_array = np.array(image).astype(np.float32)

        # 归一化
        img_array = img_array / 255.0

        # 调整维度 (H, W, C) -> (1, C, H, W)
        if len(img_array.shape) == 3:
            img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)

        return img_array

    def postprocess_detections(
        self,
        outputs: List[np.ndarray],
        orig_width: int,
        orig_height: int,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> List[DetectionResult]:
        """后处理检测结果（YOLOv8/v11 格式）"""
        results = []

        # YOLOv8/v11 输出格式处理
        # 输出通常是 [batch, 84, 8400] 或 [batch, num_boxes, 84]
        predictions = outputs[0][0]  # 取第一个 batch

        # 转置为 [num_boxes, 84]
        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        # 解析检测结果
        for pred in predictions:
            # YOLO 格式: [x_center, y_center, width, height, conf, class0_conf, class1_conf, ...]
            if len(pred) < 5:
                continue

            x_center, y_center, width, height = pred[0:4]
            confidence = float(pred[4])

            if confidence < conf_threshold:
                continue

            # 获取类别
            class_scores = pred[5:]
            class_id = int(np.argmax(class_scores))
            class_conf = float(class_scores[class_id])

            # 转换坐标
            x1 = (x_center - width / 2) / self.input_shape[2] * orig_width
            y1 = (y_center - height / 2) / self.input_shape[2] * orig_height
            x2 = (x_center + width / 2) / self.input_shape[2] * orig_width
            y2 = (y_center + height / 2) / self.input_shape[2] * orig_height

            class_name = self.class_names[class_id] if class_id < len(
                self.class_names) else f"class_{class_id}"

            results.append(DetectionResult(
                class_id=class_id,
                class_name=class_name,
                confidence=confidence * class_conf,
                box=Box(x1=x1, y1=y1, x2=x2, y2=y2)
            ))

        # NMS (简化版)
        results = self._nms(results, iou_threshold)

        return results

    def _nms(self, detections: List[DetectionResult], iou_threshold: float) -> List[DetectionResult]:
        """非极大值抑制"""
        if not detections:
            return detections

        # 按置信度排序
        detections = sorted(
            detections, key=lambda x: x.confidence, reverse=True)

        keep = []
        while detections:
            best = detections[0]
            keep.append(best)
            detections = [d for d in detections[1:]
                          if self._iou(best.box, d.box) < iou_threshold]

        return keep

    def _iou(self, box1: Box, box2: Box) -> float:
        """计算 IoU"""
        x1 = max(box1.x1, box2.x1)
        y1 = max(box1.y1, box2.y1)
        x2 = min(box1.x2, box2.x2)
        y2 = min(box1.y2, box2.y2)

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
        area2 = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def predict(self, image: Image.Image) -> List[DetectionResult]:
        """执行推理"""
        orig_width, orig_height = image.size

        # 预处理
        input_tensor = self.preprocess(image)

        # 推理
        outputs = self.session.run(None, {self.input_name: input_tensor})

        # 后处理
        results = self.postprocess_detections(outputs, orig_width, orig_height)

        return results


# ============ FastAPI 应用 ============

app = FastAPI(title="Model Runtime Service")
runtime: Optional[ONNXRuntime] = None
model_path: str = ""
device: str = "cpu"


@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    global runtime

    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to ONNX model")
    parser.add_argument("--port", type=int, default=9001, help="Service port")
    parser.add_argument("--device", default="cpu", help="Device to run on")
    args, _ = parser.parse_known_args()

    global model_path, device
    model_path = args.model
    device = args.device

    try:
        runtime = ONNXRuntime(model_path, device)
        logger.info(f"Runtime service started with model: {model_path}")
    except Exception as e:
        logger.error(f"Failed to start runtime: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy" if runtime else "unhealthy",
        model_path=model_path,
        device=device
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    """
    执行目标检测推理

    - **file**: 图像文件
    """
    if not runtime:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 读取图像
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # 执行推理
        results = runtime.predict(image)

        return PredictResponse(
            success=True,
            results=results,
            image_width=image.width,
            image_height=image.height
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/base64")
async def predict_base64(data: dict):
    """
    使用 base64 编码的图像进行推理

    - **image**: base64 编码的图像字符串
    """
    if not runtime:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 解码 base64
        image_data = base64.b64decode(data["image"])
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # 执行推理
        results = runtime.predict(image)

        return PredictResponse(
            success=True,
            results=results,
            image_width=image.width,
            image_height=image.height
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to ONNX model")
    parser.add_argument("--port", type=int, default=9001, help="Service port")
    parser.add_argument("--device", default="cpu", help="Device to run on")
    args = parser.parse_args()

    uvicorn.run(app, host="0.0.0.0", port=args.port)
