import cv2
import numpy as np
from ultralytics import YOLO

# 加载模型和图片
model = YOLO("best.pt")
image = cv2.imread("ref1.png")

# 运行模型
results = model(image)[0]

# 获取检测框坐标
masks = np.zeros(image.shape[:2], dtype=np.uint8)  # 创建黑色背景的 mask

for box in results.boxes.xyxy:
    x1, y1, x2, y2 = map(int, box.tolist())
    # 在 mask 上画白色的矩形（255）
    cv2.rectangle(masks, (x1, y1), (x2, y2), 255, thickness=-1)

# 保存 mask 图像
cv2.imwrite("mask.png", masks)
