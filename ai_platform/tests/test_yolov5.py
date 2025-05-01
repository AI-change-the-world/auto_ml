import cv2
import supervision as sv
from ultralytics import YOLO

model = YOLO("best.pt")
image = cv2.imread("test5.png")
results = model(image)[0]
print(results.to_json())

detections = sv.Detections.from_ultralytics(results)


box_annotator = sv.BoxAnnotator()
annotated_frame = box_annotator.annotate(scene=image.copy(), detections=detections)

cv2.imwrite("result2.jpg", annotated_frame)
