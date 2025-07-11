# Define a Pydantic model for GAN training requests
from typing import Optional

from pydantic import BaseModel


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


class SdAugmentRequest(BaseModel):
    count: int
    prompt: str


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
