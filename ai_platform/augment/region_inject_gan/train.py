import torch
from torch.utils.data import DataLoader
from torch import nn, optim
from torchvision.utils import save_image
import os

from tqdm import tqdm

from augment.region_inject_gan.dataset import InjectDataset, CleanDataset

from augment.region_inject_gan.model import BackgroundGenerator, InjectGenerator, Discriminator,BgDiscriminator
torch.autograd.set_detect_anomaly(True)

def fuse(bg_img, defect_patch, mask):
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

# 模型和优化器
G_bg = BackgroundGenerator(z_dim, img_channels).to(device)
D_bg = BgDiscriminator(img_channels).to(device)
optimizer = optim.Adam(G_bg.parameters(), lr=lr, betas=(0.5, 0.999))
optimizer_D = torch.optim.Adam(D_bg.parameters(), lr=lr / 2, betas=(0.5, 0.999))
criterion = nn.BCEWithLogitsLoss()

# 数据加载
dataset = CleanDataset("./data/good")
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
scaler = torch.amp.GradScaler()

# train bg
# 训练循环
os.makedirs("bg_samples", exist_ok=True)
for epoch in range(epochs):
    G_bg.train()
    for real_imgs in tqdm(loader, desc=f"Epoch {epoch+1}/{epochs}"):
        real_imgs = real_imgs.to(device)
        batch_size = real_imgs.size(0)

        real_labels = torch.ones(batch_size, 1, device=device)
        fake_labels = torch.zeros(batch_size, 1, device=device)

        # Train Discriminator
        z = torch.randn(batch_size, z_dim).to(device)
        with torch.amp.autocast(device_type=device.type):
            fake_imgs = G_bg(z).detach()
            d_real = D_bg(real_imgs)
            d_fake = D_bg(fake_imgs)
            loss_D = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
        optimizer_D.zero_grad()
        scaler.scale(loss_D).backward()
        scaler.step(optimizer_D)

        # Train Generator
        z = torch.randn(batch_size, z_dim).to(device)
        with torch.amp.autocast(device_type=device.type):
            fake_imgs = G_bg(z)
            d_fake = D_bg(fake_imgs)
            loss_G = criterion(d_fake, real_labels)
        optimizer.zero_grad()
        scaler.scale(loss_G).backward()
        scaler.step(optimizer)
        scaler.update()

    print(f"Epoch {epoch+1}, Loss D: {loss_D.item():.4f}, Loss G: {loss_G.item():.4f}")

    if (epoch + 1) % save_interval == 0:
        save_image(
            fake_imgs * 0.5 + 0.5, os.path.join("bg_samples", f"fake_{epoch+1}.png")
        )

    if (epoch + 1) % save_interval == 0:
        torch.save(G_bg.state_dict(), "bg_generator.pth")

# train defect

G_bg = BackgroundGenerator(z_dim, img_channels).to(device)
G_bg.load_state_dict(torch.load("bg_generator.pth"))
G_bg.eval()
for p in G_bg.parameters():
    p.requires_grad = False

G_def = InjectGenerator(z_dim, img_channels).to(device)
D = Discriminator(img_channels).to(device)

opt_G = optim.Adam(G_def.parameters(), lr=lr, betas=(0.5, 0.999))
opt_D = optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.999))

bce_loss = nn.BCELoss()
l1_loss = nn.L1Loss()

dataset = InjectDataset("./data/defect", "./data/mask")
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# 训练循环
os.makedirs("defect_samples", exist_ok=True)
for epoch in range(epochs):
    for i, batch in enumerate(loader):
        clean = batch["clean"].to(device)
        defect = batch["defect"].to(device)
        mask = batch["mask"].to(device)

        B = clean.size(0)
        z_bg = torch.randn(B, z_dim).to(device)
        z_def = torch.randn(B, z_dim).to(device)

        with torch.no_grad():
            bg_img = G_bg(z_bg)

        defect_patch = G_def(z_def, mask)
        fused_img = fuse(bg_img, defect_patch, mask)

        # 判别器更新
        pred_real = D(defect)
        pred_fake = D(fused_img.detach())

        d_loss_real = bce_loss(pred_real, torch.ones_like(pred_real))
        d_loss_fake = bce_loss(pred_fake, torch.zeros_like(pred_fake))
        d_loss = (d_loss_real + d_loss_fake) * 0.5

        opt_D.zero_grad()
        d_loss.backward()
        opt_D.step()

        # 缺陷生成器更新
        pred_fake_for_g = D(fused_img)
        adv_loss = bce_loss(pred_fake_for_g, torch.ones_like(pred_fake_for_g))
        recon_loss = l1_loss(fused_img, defect)
        g_loss = adv_loss + lambda_def * recon_loss

        opt_G.zero_grad()
        g_loss.backward()
        opt_G.step()

        if i % 50 == 0:
            print(f"[Epoch {epoch} Batch {i}] D: {d_loss.item():.4f}, G: {g_loss.item():.4f}")

    if (epoch + 1) % save_interval == 0:
        save_image((bg_img + 1) / 2, f"defect_samples/bg_{epoch}.png")
        save_image((defect_patch + 1) / 2, f"defect_samples/defect_patch_{epoch}.png")
        save_image((fused_img + 1) / 2, f"defect_samples/fused_{epoch}.png")
        torch.save(G_def.state_dict(), "defect_generator.pth")