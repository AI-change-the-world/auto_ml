import cv2
import supervision as sv
from ultralytics import YOLO

model = YOLO("yolo11x.pt")
image = cv2.imread("test.jpg")
results = model(image)[0]
detections = sv.Detections.from_ultralytics(results)

print(detections.boxes)


box_annotator = sv.BoxAnnotator()
annotated_frame = box_annotator.annotate(
    scene=image.copy(),
    detections=detections
)

cv2.imwrite("result.jpg", annotated_frame)