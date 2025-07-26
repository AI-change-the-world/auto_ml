# Define a Pydantic model for GAN training requests
from typing import Optional

from pydantic import BaseModel


class SDInitializeRequest(BaseModel):
    enable_img2img: Optional[bool] = False
    enable_inpaint: Optional[bool] = False
    model_path: Optional[str] = "/root/models/sd3m"


class SdDeepOptimizeResponse(BaseModel):
    tip: str
    img: Optional[str] = None


class SdDeepOptimizeRequest(BaseModel):
    """
    SD深度优化请求类

    该类继承自BaseModel，用于定义SD深度优化请求的数据结构
    它包含了优化所需的提示文本、图片和循环次数等信息
    """

    # 优化提示文本，用于指导优化过程
    prompt: str
    # 图片路径或URL，指定需要进行优化的图片
    img: str
    # 循环优化的次数，默认为5次，通过多次迭代来逐步优化结果
    loop_times: int = 5
    model_id: int


class SdAugmentRequest(BaseModel):
    """
    A model representing the parameters required for initiating SD augmentation.

    Attributes:
        job_type (str): The type of job to be performed. It can be 'txt2img', 'img2img', or 'inpaint'.
        lora_name (Optional[str]): The name of the LoRA (Local Rank-one Adaptation) module, if any.
        prompt (str): The prompt text for generating images.
        negative_prompt (Optional[str]): Negative prompt text to avoid certain features in the generated images.
        width (int): The width of the generated images. Default is 1024.
        height (int): The height of the generated images. Default is 1024.
        steps (int): The number of steps in the generation process. Default is 30.
        guidance_scale (float): The scale of guidance for the generation process. Default is 7.5.
        seed (int): The random seed for the generation process. Default is 123.
        count (int): The number of images to generate. Default is 5.
        img (Optional[str]): Base64 encoded image data, required only for 'img2img' and 'inpaint' job types.
        mask (Optional[str]): Base64 encoded mask image data, required only for 'inpaint' job type.
        prompt_optimize (bool): Flag indicating whether to optimize the prompt. Default is False.
    """

    job_type: str  # [txt2img, img2img, inpaint]
    lora_name: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    steps: int = 30
    guidance_scale: float = 7.5
    seed: int = 12345
    count: int = 5
    img: Optional[str] = None
    mask: Optional[str] = None
    # only for img to img augmentation
    prompt_optimize: bool = False
    model_id: Optional[int] = None
    # only for inpaint & img2img augmentation
    strength: float = 0.5


class GANTrainRequest(BaseModel):
    """
    A model representing the parameters required for initiating GAN training.

    This includes details about the model, dataset, and various training configurations.
    """

    # Identifier for the specific model to be trained
    model_id: str

    # Identifier for the task associated with this training
    task_id: Optional[int]

    # Identifier for the source dataset used in training
    dataset_id: int

    # Optional identifier for the target dataset for GANS like cycle_gan (used for evaluation or transfer learning)
    target_dataset_id: Optional[int]

    # Number of complete passes through the training dataset
    epochs: int

    # Size of the batches of data used in each iteration of training (default: 16)
    batch_size: Optional[int] = 16

    # Learning rate for the optimizer (default: 0.0002)
    lr: Optional[float] = 2e-4

    # Interval (in iterations) at which generated images are saved (default: 100)
    image_save_interval: Optional[int] = 100

    # Interval (in iterations) at which the model's state is saved (default: 500)
    model_dump_interval: Optional[int] = 500

    # Size of the images used/generated during training (default: 256x256 pixels)
    image_size: Optional[int] = 256

    # Number of channels in the images (3 for RGB images, default: 3)
    img_channels: Optional[int] = 3

    # input Dimensionality for simple_gan (default: 2048)
    z_dim: Optional[int] = 2048


class GANRequest(BaseModel):
    count: int


class CvAugmentRequest(BaseModel):
    count: int
    b64: str
    types: list[str] = []


class CvAugmentResponse(BaseModel):
    img_url: str
    point: float


class PromptOptimizeRequest(BaseModel):
    model_id: int
    prompt: str
    ref: Optional[str] = None


class PromptOptimizeResponse(BaseModel):
    prompt: str


class SdAugmentResponse(BaseModel):
    img_url: str


class MeasureRequest(BaseModel):
    img1: str
    img2: str
    model_id: int
