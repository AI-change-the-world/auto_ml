import io
import time
import uuid

from sse_starlette import EventSourceResponse
import torch
from fastapi import APIRouter
from PIL import Image
from pydantic import BaseModel
from augment.simple_gan.model import Generator as Model
from base.file_delegate import get_operator, s3_properties

model_path = "generator.pth"

model = Model(z_dim=2048, img_channels=3).to("cpu")
model.load_state_dict(torch.load(model_path))


class GANRequest(BaseModel):
    count: int


router = APIRouter(
    prefix="/augment",
    tags=["GAN"],
)


# TODO merge to augment, just for demo
@router.post("/gan/generate/stream")
async def generate_stream(req: GANRequest):
    """Stream-generated images from the GAN model"""

    async def image_generator():
        operator = get_operator(s3_properties.augment_bucket_name)
        with torch.no_grad():
            z = torch.randn(req.count, 2048).to("cpu")
            generated_image = model(z)
            generated_image = (generated_image * 0.5) + 0.5
            # print(f"shape. {generated_image.shape}" )
            for img_tensor in generated_image:
                img_tensor = img_tensor.permute(1, 2, 0).clamp(0, 1).mul(255).byte().numpy()
                pil_img = Image.fromarray(img_tensor)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                img_name = str(uuid.uuid4())+".png"
                img_bytes = buf.getvalue()
                operator.write(img_name, img_bytes)
                yield f"path: {img_name}\n"
                time.sleep(0.5)
        
        # yield "[DONE]"



    return EventSourceResponse(
        image_generator(),
        media_type="text/event-stream",
    )
