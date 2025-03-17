from ultralytics import YOLO

model = YOLO('yolo11n.pt')

res = model.predict('test.jpg', stream=False)
for r in res:
    print(r.to_json())