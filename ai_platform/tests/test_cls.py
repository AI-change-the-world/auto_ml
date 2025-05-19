import json

import cv2
from ultralytics import YOLO

model = YOLO("yolo11n-cls.pt")
image = cv2.imread("test5.png")
results = model(image)[0]

print(type(results.to_json()))

j = json.loads(results.to_json())
print(j)
