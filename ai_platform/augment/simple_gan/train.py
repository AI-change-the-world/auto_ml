import os

import torch
import torch.nn as nn
from dataset import DefectDataset
from model import Discriminator, Generator
from torch.utils.data import DataLoader
from torchvision.utils import save_image
from tqdm import tqdm

# --------- Config ---------
z_dim = 2048  # 生成器输入的噪声向量维度
image_size = 256
image_channels = 3
batch_size = 16
epochs = 1000  # recommended: 1000 or less
lr = 2e-4
lambda_l1 = 10
save_interval = 100
model_dump_interval = 500
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
data_root = "../defect"
output_dir = "../output"
os.makedirs(output_dir, exist_ok=True)

# --------- Initialize Models ---------
G = Generator(z_dim, image_channels).to(device)
D = Discriminator(image_channels).to(device)

criterion = nn.BCEWithLogitsLoss()
l1_loss = nn.L1Loss()
optimizer_G = torch.optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.999))
optimizer_D = torch.optim.Adam(D.parameters(), lr=lr / 2, betas=(0.5, 0.999))

dataloader = DataLoader(DefectDataset(data_root), batch_size=batch_size, shuffle=True)
scaler = torch.amp.GradScaler()


# --------- Training Loop ---------
for epoch in range(epochs):
    G.train()
    for real_imgs in tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}"):
        real_imgs = real_imgs.to(device)
        batch_size = real_imgs.size(0)

        real_labels = torch.ones(batch_size, 1, device=device)
        fake_labels = torch.zeros(batch_size, 1, device=device)

        # Train Discriminator
        z = torch.randn(batch_size, z_dim).to(device)
        with torch.amp.autocast(device_type=device.type):
            fake_imgs = G(z).detach()
            d_real = D(real_imgs)
            d_fake = D(fake_imgs)
            loss_D = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
        optimizer_D.zero_grad()
        scaler.scale(loss_D).backward()
        scaler.step(optimizer_D)

        # Train Generator
        z = torch.randn(batch_size, z_dim).to(device)
        with torch.amp.autocast(device_type=device.type):
            fake_imgs = G(z)
            d_fake = D(fake_imgs)
            loss_G = criterion(d_fake, real_labels)
            recon_loss = l1_loss(fake_imgs, real_imgs)
            loss_G = loss_G + lambda_l1 * recon_loss
        optimizer_G.zero_grad()
        scaler.scale(loss_G).backward()
        scaler.step(optimizer_G)
        scaler.update()

    print(f"Epoch {epoch+1}, Loss D: {loss_D.item():.4f}, Loss G: {loss_G.item():.4f}")

    if (epoch + 1) % save_interval == 0:
        save_image(
            fake_imgs * 0.5 + 0.5, os.path.join(output_dir, f"fake_{epoch+1}.png")
        )

    if (epoch + 1) % model_dump_interval == 0 and epoch != epochs:
        torch.save(
            G.state_dict(), os.path.join(output_dir, f"generator_{epoch + 1}.pth")
        )

# Save final model
# torch.save(G.state_dict(), os.path.join(output_dir, "generator.pth"))
# torch.save(D.state_dict(), os.path.join(output_dir, "discriminator.pth"))

# Save final model (to CPU)
torch.save(G.to("cpu").state_dict(), os.path.join(output_dir, "generator.pth"))
torch.save(D.to("cpu").state_dict(), os.path.join(output_dir, "discriminator.pth"))
