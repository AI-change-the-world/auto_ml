import torch
from model import Generator
from torchvision.utils import save_image

z_dim = 2048

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = Generator(z_dim=z_dim, img_channels=3).to(device)

model.load_state_dict(torch.load("./output/generator.pth"))
model.eval()

for i in range(5):
    z = torch.randn(1, z_dim).to(device)
    fake_images = model(z)
    save_image(fake_images * 0.5 + 0.5, f"fake_sample_{i}.png")
