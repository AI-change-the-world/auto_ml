import lpips
import torch
from torch import Tensor

loss_fn = lpips.LPIPS(net="squeeze").cuda()

img1 = lpips.im2tensor(
    lpips.load_image("D:/github_repo/auto_ml/ai_platform/gan/good/0.png")
).cuda()
img2 = lpips.im2tensor(
    lpips.load_image("D:/github_repo/auto_ml/ai_platform/gan/good/0.png")
).cuda()


# 转相似度
def lpips_to_similarity(lpips_distance, max_lpips=0.5):
    lpips_clamped = min(lpips_distance, max_lpips)
    similarity = (1 - lpips_clamped / max_lpips) * 100
    return round(similarity, 2)


with torch.no_grad():
    dist: Tensor = loss_fn(img1, img2)

print(lpips_to_similarity(dist.item()))
