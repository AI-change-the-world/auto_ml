import glob
from tqdm import tqdm
import cv2

imgs = glob.glob("./test/*/*.png")

save_dir = "./dataset/"

count = 0
for img in tqdm(imgs):
    img_name = f"{count}.png"
    _img = cv2.imread(img)
    _img = cv2.resize(_img, (256, 256))
    cv2.imwrite(save_dir + img_name, _img)
    count += 1
