import torch
from model import Generator

model_path = "../output/generator_1000.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = Generator(z_dim=2048, img_channels=3).to(device)

model.load_state_dict(torch.load(model_path))
model.eval()

torch.save(model.to("cpu").state_dict(), "generator.pth")
