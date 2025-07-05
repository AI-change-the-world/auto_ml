import io
from typing import Generator

import torch
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel
from simple_gan.model import Generator as Model

model_path = "generator.pth"

model = Model(z_dim=2048, img_channels=3).to("cpu")
model.load_state_dict(torch.load(model_path))


class GANRequest(BaseModel):
    count: int


router = APIRouter(
    prefix="/gan",
    tags=["GAN"],
)


@router.post("/generate/stream")
async def generate_stream(req: GANRequest):
    """Stream-generated images from the GAN model"""

    def image_generator() -> Generator[bytes, None, None]:
        with torch.no_grad():
            z = torch.randn(req.count, 2048).to("cpu")
            generated_images = model(z)
            generated_images = (generated_images * 0.5) + 0.5

            for img_tensor in generated_images:
                img = img_tensor.permute(1, 2, 0).clamp(0, 1).mul(255).byte().numpy()
                pil_img = Image.fromarray(img)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)

                img_bytes = buf.getvalue()
                # save to s3
                yield b"--image-boundary\r\n"
                yield b"Content-Type: image/png\r\n\r\n"
                yield buf.read()
                yield b"\r\n"

    return StreamingResponse(
        image_generator(),
        media_type="multipart/x-mixed-replace; boundary=image-boundary",
    )
