import cv2

import numpy as np
img = cv2.imread("/Users/guchengxi/Desktop/projects/auto_ml/ai_platform/output.png")

print(img.shape)

cut_img = img[256:256*3, 256:256*3]

cv2.imwrite("cut_img.png", cut_img)