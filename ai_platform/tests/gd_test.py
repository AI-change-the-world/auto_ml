import cv2
from groundingdino.util.inference import (annotate, load_image, load_model,
                                          predict)

model = load_model(
    "./gd/groundingdino/config/GroundingDINO_SwinT_OGC.py",
    "groundingdino_swint_ogc.pth",
)
# /Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/road_template2.png
# /Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/road_test2.png
# /Users/guchengxi/Desktop/projects/auto_ml/ai_platform/output.jpg
IMAGE_PATH = "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/output.jpg"
TEXT_PROMPT = "traffic signs . person . hat . safety vest ."
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25

image_source, image = load_image(IMAGE_PATH)

boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption=TEXT_PROMPT,
    box_threshold=BOX_TRESHOLD,
    text_threshold=TEXT_TRESHOLD,
    device="cpu",
)

print(f"Boxes: {boxes}")
print(f"logits: {logits}")
print(f"phrases: {phrases}")

annotated_frame = annotate(
    image_source=image_source, boxes=boxes, logits=logits, phrases=phrases
)
cv2.imwrite("annotated_image.jpg", annotated_frame)
