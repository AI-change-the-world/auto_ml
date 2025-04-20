from ultralytics import YOLO

model = YOLO(
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/runs/detect/train/weights/best.pt"
)
print(model.names)
l = model.predict(
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/yolo/test.png", stream=False
)

print(l)
