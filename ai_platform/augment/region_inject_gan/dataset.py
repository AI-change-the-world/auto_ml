import os

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


class CleanDataset(Dataset):
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


class InjectDataset(Dataset):
    def __init__(self, defect_dir, mask_dir, image_size=256):
        # self.clean_paths = sorted([os.path.join(clean_dir, f) for f in os.listdir(clean_dir)])
        self.defect_paths = sorted(
            [os.path.join(defect_dir, f) for f in os.listdir(defect_dir)]
        )
        self.mask_paths = sorted(
            [os.path.join(mask_dir, f) for f in os.listdir(mask_dir)]
        )
        print(f"defect: {len(self.defect_paths)}  mask: {len(self.mask_paths)}")
        self.transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),  # [0,1]
                transforms.Normalize([0.5] * 3, [0.5] * 3),  # [-1,1]
            ]
        )
        self.mask_transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
            ]  # 不归一化
        )

    def __len__(self):
        return min(len(self.defect_paths), len(self.mask_paths))

    def __getitem__(self, idx):
        # clean = Image.open(self.clean_paths[idx]).convert('RGB')
        defect = Image.open(self.defect_paths[idx]).convert("RGB")
        mask = Image.open(self.mask_paths[idx]).convert("L")  # 单通道

        mask = self.mask_transform(mask)  # shape: [1, H, W]
        mask = (mask > 0.5).float()  # 二值化，强制 0 或 1

        return {
            # "clean": self.transform(clean),
            "defect": self.transform(defect),
            "mask": mask,
        }
