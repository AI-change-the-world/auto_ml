import os
import shutil
import uuid
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from base.file_delegate import get_operator, s3_properties
from base.nacos_config import get_sync_db
from base.tools import download_from_s3, upload_to_s3
from db.dataset.dataset_crud import get_dataset
from db.task_log.task_log_crud import create_log
from db.task_log.task_log_schema import TaskLogCreate
from PIL import Image
from sqlalchemy.orm import Session
from torch.utils.data import DataLoader, Dataset
from torchvision.utils import save_image
from tqdm import tqdm

import augment.simple_cycle_gan.model as cycle_gan
import augment.simple_gan.model as gan
from augment.req_and_resp import GANTrainRequest


class __Dataset(Dataset):
    def __init__(self, root_dir, image_size=256):
        self.root_dir = root_dir
        self.files = [
            os.path.join(root_dir, f)
            for f in os.listdir(root_dir)
            if f.endswith((".jpg", ".png"))
        ]
        self.transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize([0.5] * 3, [0.5] * 3),
            ]
        )

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        img = Image.open(self.files[idx]).convert("RGB")
        return self.transform(img)


def __train_simple_gan(req: GANTrainRequest, session: Session):
    model_op = get_operator(s3_properties.models_bucket_name)
    op = get_operator(s3_properties.datasets_bucket_name)
    uploader_op = get_operator(s3_properties.augment_bucket_name)

    d = get_dataset(session, req.dataset_id)
    if d is None:
        tlc = TaskLogCreate(
            task_id=req.task_id,
            log_content=f"[error] dataset not found, quiting...",
        )
        create_log(session, tlc)
        return
    folder_name = str(uuid.uuid4())
    tlc = TaskLogCreate(
        task_id=req.task_id, log_content="[pre-train] create temp folder ..."
    )
    create_log(session, tlc)

    os.mkdir(f"./runs/{folder_name}")

    temp_dataset_path = f"./runs/{folder_name}/dataset"
    os.mkdir(temp_dataset_path)
    output_path = f"./runs/{folder_name}/output"
    os.mkdir(output_path)
    tlc = TaskLogCreate(
        task_id=req.task_id,
        log_content=f"[pre-train] downloading dataset from s3 ...",
    )
    create_log(session, tlc)

    for i in op.list(d.local_s3_storage_path):
        if Path(i.path).suffix != "":
            print(i.path)
            file_name = i.path.split("/")[-1]
            download_from_s3(op, i.path, temp_dataset_path + os.sep + file_name)
    z_dim = req.z_dim
    if z_dim <= 0:
        tlc = TaskLogCreate(
            task_id=req.task_id,
            log_content=f"[error] z_dim must be greater than 0",
        )
        create_log(session, tlc)
        return
    image_size = req.image_size
    image_channels = req.img_channels
    if image_channels not in [1, 3]:
        tlc = TaskLogCreate(
            task_id=req.task_id,
            log_content=f"[error] image_channels must be 1 or 3",
        )
        create_log(session, tlc)
        return
    batch_size = req.batch_size
    if batch_size <= 0:
        tlc = TaskLogCreate(
            task_id=req.task_id,
            log_content=f"[error] batch_size must be greater than 0",
        )
        create_log(session, tlc)
        return
    epochs = req.epochs
    if epochs <= 0:
        tlc = TaskLogCreate(
            task_id=req.task_id,
            log_content=f"[error] epochs must be greater than 0",
        )
        create_log(session, tlc)
        return
    lr = req.lr
    save_interval = req.image_save_interval
    model_dump_interval = req.model_dump_interval

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    G = gan.Generator(z_dim, image_channels).to(device)
    D = gan.Discriminator(image_channels).to(device)

    criterion = nn.BCEWithLogitsLoss()
    optimizer_G = torch.optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.999))
    optimizer_D = torch.optim.Adam(D.parameters(), lr=lr / 2, betas=(0.5, 0.999))
    scaler = torch.amp.GradScaler()
    dataloader = DataLoader(
        __Dataset(temp_dataset_path, image_size=image_size),
        batch_size=batch_size,
        shuffle=True,
        drop_last=True,
    )

    for epoch in range(epochs):
        G.train()
        for real_imgs in tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}"):
            real_imgs = real_imgs.to(device)
            bsz = real_imgs.size(0)

            real_labels = torch.ones(bsz, 1, device=device)
            fake_labels = torch.zeros(bsz, 1, device=device)

            # --- Train D ---
            z = torch.randn(bsz, z_dim).to(device)
            with torch.amp.autocast(device_type=device.type):
                fake_imgs = G(z).detach()
                d_real = D(real_imgs)
                d_fake = D(fake_imgs)
                loss_D = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
            optimizer_D.zero_grad()
            scaler.scale(loss_D).backward()
            scaler.step(optimizer_D)

            # --- Train G ---
            z = torch.randn(bsz, z_dim).to(device)
            with torch.amp.autocast(device_type=device.type):
                fake_imgs = G(z)
                d_fake = D(fake_imgs)
                loss_G = criterion(d_fake, real_labels)
            optimizer_G.zero_grad()
            scaler.scale(loss_G).backward()
            scaler.step(optimizer_G)
            scaler.update()

        print(
            f"Epoch {epoch+1}, Loss D: {loss_D.item():.4f}, Loss G: {loss_G.item():.4f}"
        )

        # --- Save generated images ---
        if (epoch + 1) % save_interval == 0:
            img_path = os.path.join(output_path, f"{epoch+1}.png")
            save_image(
                fake_imgs * 0.5 + 0.5, img_path
            )
            # TODO: save to s3
            s3_image_name = f"{req.task_id}_{req.model_id}_{epoch+1}.img"
            upload_to_s3(uploader_op, img_path, s3_image_name)

        # --- Save model checkpoints ---
        if (epoch + 1) % model_dump_interval == 0 and epoch != epochs:
            # TODO: save to local s3
            torch.save(
                G.state_dict(), os.path.join(output_path, f"generator_{epoch+1}.pth")
            )

    # Save final model (to CPU)
    torch.save(G.to("cpu").state_dict(), os.path.join(output_path, "generator.pth"))
    torch.save(D.to("cpu").state_dict(), os.path.join(output_path, "discriminator.pth"))
    # TODO: save to local s3

    # delete temp folder
    shutil.rmtree(f"./runs/{folder_name}")
    tlc = TaskLogCreate(
        task_id=req.task_id,
        log_content=f"[post-train] delete temp folder and temp folder",
    )
    create_log(session, tlc)


def __train_cycle_gan(req: GANTrainRequest, session: Session):
    if req.target_dataset_id is None:
        return
    pass


def train_gan(req: GANTrainRequest):
    if req.task_id is None:
        return
    session = get_sync_db()
