import os

import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision.utils import save_image
from tqdm import tqdm

from augment.region_inject_gan.dataset import CleanDataset, InjectDataset
from augment.region_inject_gan.model import (BackgroundGenerator,
                                             BgDiscriminator, Discriminator,
                                             InjectGenerator,
                                             VGGPerceptualLoss)

torch.autograd.set_detect_anomaly(True)


def color_consistency_loss(pred, target, mask):
    pred_color = (pred * mask).sum(dim=[2, 3]) / (mask.sum(dim=[2, 3]) + 1e-6)
    target_color = (target * mask).sum(dim=[2, 3]) / (mask.sum(dim=[2, 3]) + 1e-6)
    return nn.functional.l1_loss(pred_color, target_color)


def blur_mask(mask, kernel_size=15, sigma=5):
    # mask: (B,1,H,W), float
    # Apply a Gaussian blur using conv2d
    channels = mask.shape[1]
    x = torch.arange(-kernel_size // 2 + 1.0, kernel_size // 2 + 1.0)
    x = torch.exp(-(x**2) / (2 * sigma**2))
    kernel_1d = x / x.sum()
    kernel_2d = torch.outer(kernel_1d, kernel_1d)
    kernel_2d = kernel_2d.to(mask.device).unsqueeze(0).unsqueeze(0)
    kernel_2d = kernel_2d.expand(channels, 1, kernel_size, kernel_size)
    blurred = F.conv2d(mask, kernel_2d, padding=kernel_size // 2, groups=channels)
    return blurred


def fuse(bg_img, defect_patch, mask):
    """
    将缺陷图合成到背景图中（只在 mask 区域）
    """
    mask = mask.expand_as(bg_img)  # 扩展到 [B, 3, H, W]
    return bg_img * (1 - mask) + defect_patch * mask


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ⚙️ 超参数
z_dim = 512
img_channels = 3
epochs = 1000
save_interval = 200
batch_size = 8
lambda_bg = 1.0
lambda_def = 10.0
lr = 0.0002
lambda_l1 = 10

# 模型
G_bg = BackgroundGenerator(z_dim, img_channels).to(device)
D_bg = BgDiscriminator(img_channels).to(device)

# 优化器 & loss
optimizer = optim.Adam(G_bg.parameters(), lr=lr, betas=(0.5, 0.999))
optimizer_D = optim.Adam(D_bg.parameters(), lr=lr / 2, betas=(0.5, 0.999))
criterion = nn.BCEWithLogitsLoss()
l1_loss = nn.L1Loss()

# 数据加载
dataset = CleanDataset("./data/good")
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# 混合精度
scaler = torch.amp.GradScaler()

# 训练开始
os.makedirs("bg_samples", exist_ok=True)
for epoch in range(epochs):
    G_bg.train()
    for real_imgs in tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}"):
        real_imgs = real_imgs.to(device)
        bsz = real_imgs.size(0)

        # Label smoothing
        real_labels = torch.ones(bsz, 1, device=device) * 0.9
        fake_labels = torch.zeros(bsz, 1, device=device)

        # === Train Discriminator ===
        z = torch.randn(bsz, z_dim).to(device)
        with torch.amp.autocast(device_type=device.type):
            fake_imgs = G_bg(z).detach()
            d_real = D_bg(real_imgs)
            d_fake = D_bg(fake_imgs)
            loss_D_real = criterion(d_real, real_labels)
            loss_D_fake = criterion(d_fake, fake_labels)
            loss_D = 0.5 * (loss_D_real + loss_D_fake)

        optimizer_D.zero_grad()
        scaler.scale(loss_D).backward()
        scaler.step(optimizer_D)

        # === Train Generator ===
        z = torch.randn(bsz, z_dim).to(device)
        with torch.amp.autocast(device_type=device.type):
            fake_imgs = G_bg(z)
            d_fake = D_bg(fake_imgs)
            adv_loss = criterion(d_fake, real_labels)
            recon_loss = l1_loss(fake_imgs, real_imgs)
            loss_G = adv_loss + lambda_l1 * recon_loss

        optimizer.zero_grad()
        scaler.scale(loss_G).backward()
        scaler.step(optimizer)
        scaler.update()

    print(f"Epoch {epoch+1}, Loss D: {loss_D.item():.4f}, Loss G: {loss_G.item():.4f}")

    # === 每轮保存多样性样本 ===
    if (epoch + 1) % save_interval == 0:
        G_bg.eval()
        with torch.no_grad():
            z_sample = torch.randn(8, z_dim).to(device)
            fake_samples = G_bg(z_sample)
        save_image(fake_samples * 0.5 + 0.5, f"bg_samples/fake_{epoch+1}.png", nrow=4)

    # === 保存模型 ===
    if (epoch + 1) % save_interval == 0:
        torch.save(G_bg.state_dict(), "bg_generator.pth")

# ========== 超参数 ==========
lambda_l1 = 10.0
lambda_lpips = 5.0
lambda_percep = 1.0
lambda_color = 5.0

z_dim = 512
img_channels = 3
batch_size = 16
epochs = 1000
lr = 2e-4
save_interval = 200
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ========== 模型初始化 ==========
G_bg = BackgroundGenerator(z_dim, img_channels).to(device)
G_bg.load_state_dict(torch.load("bg_generator.pth"))
G_bg.eval()
for p in G_bg.parameters():
    p.requires_grad = False

G_def = InjectGenerator(z_dim, img_channels).to(device)
D = Discriminator(img_channels).to(device)

optimizer = optim.Adam(G_def.parameters(), lr=lr, betas=(0.5, 0.999))
opt_D = optim.Adam(D.parameters(), lr=lr / 2, betas=(0.5, 0.999))

l1_loss = nn.L1Loss()
vgg_loss = VGGPerceptualLoss().to(device)

try:
    from lpips import LPIPS
    lpips_loss = LPIPS(net="alex").to(device)
    use_lpips = True
except:
    print("LPIPS not available, skipping.")
    use_lpips = False

# ========== 数据 ==========
dataset = InjectDataset("./data/defect", "./data/mask")
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# ========== 训练 ==========
os.makedirs("defect_samples", exist_ok=True)

for epoch in range(epochs):
    G_def.train()
    for i, batch in enumerate(tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}")):
        defect = batch["defect"].to(device)         # [B, 3, 256, 256]
        mask = batch["mask"].to(device)             # [B, 1, 256, 256]
        mask = (mask > 0.5).float()                 # 二值化
        mask_rgb = mask.expand_as(defect)           # 扩展到 RGB

        B = defect.size(0)
        z_bg = torch.randn(B, z_dim).to(device)
        z_def = torch.randn(B, z_dim).to(device)

        with torch.no_grad():
            bg_img = G_bg(z_bg)
            defect_target = fuse(bg_img, defect, mask_rgb)

        # 生成缺陷补丁并合成
        pred_patch = G_def(z_def, mask, bg_img)
        fused_img = fuse(bg_img, pred_patch, mask_rgb)

        # 蒙版平滑（可选）
        soft_mask = blur_mask(mask)
        soft_mask_rgb = soft_mask.expand_as(defect)

        # 多项 loss 组合
        l1 = (torch.abs(fused_img - defect_target) * soft_mask_rgb).sum() / soft_mask_rgb.sum().clamp(min=1e-6)
        percep = vgg_loss(fused_img, defect_target)
        color = color_consistency_loss(fused_img, bg_img, soft_mask_rgb)
        total_loss = lambda_l1 * l1 + lambda_percep * percep + lambda_color * color

        if use_lpips:
            lpips = lpips_loss(fused_img, defect_target).mean()
            total_loss += lambda_lpips * lpips
        else:
            lpips = torch.tensor(0.0)

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        if i % 20 == 0:
            print(f"[Epoch {epoch+1}/{epochs}] Step [{i}/{len(loader)}] "
                  f"L1: {l1.item():.4f} Percep: {percep.item():.4f} Color: {color.item():.4f} LPIPS: {lpips.item():.4f}")

    # 保存图像
    if (epoch + 1) % save_interval == 0:
        save_image((bg_img + 1) / 2, f"defect_samples/bg_{epoch+1}.png")
        save_image((pred_patch + 1) / 2, f"defect_samples/pred_patch_{epoch+1}.png")
        save_image((fused_img + 1) / 2, f"defect_samples/fused_{epoch+1}.png")
        save_image((defect + 1) / 2, f"defect_samples/defect_gt_{epoch+1}.png")
