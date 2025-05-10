import cv2

img = cv2.imread(
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/road_test.png"
)
h, w, _ = img.shape

img2 = cv2.resize(
    img,
    (
        int(w * 0.5),
        int(h * 0.5),
    ),
)
cv2.imwrite(
    "/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/tests/road_test_resize.png",
    img2,
)
