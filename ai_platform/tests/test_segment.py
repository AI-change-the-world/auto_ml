import cv2
import supervision as sv
from ultralytics import SAM

# image = cv2.imread(
#     "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/datasets/coco128/images/train2017/000000000061.jpg"
# )

image = cv2.imread(
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/datasets/coco128/images/train2017/000000000071.jpg"
)

model = SAM("sam2.1_s.pt")
print(model.is_sam2)
# 控制范围
# results = model(image, bboxes=[[588, 163, 643, 220]])

results = model(image, bboxes=[[200, 200, 400, 400]])
print(results)
detections = sv.Detections.from_ultralytics(results[0])

polygon_annotator = sv.PolygonAnnotator()
mask_annotator = sv.MaskAnnotator()

annoated_image = mask_annotator.annotate(image.copy(), detections)
annoated_image = polygon_annotator.annotate(annoated_image, detections)

sv.plot_image(annoated_image, (12, 12))
