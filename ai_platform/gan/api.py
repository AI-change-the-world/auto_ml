import torch
from fastapi import APIRouter
from simple_gan.model import Generator

model_path = "generator.pth"

model = Generator(z_dim=2048, img_channels=3).to("cpu")
model.load_state_dict(torch.load(model_path))


router = APIRouter(
    prefix="/gan",
    tags=["GAN"],
)
