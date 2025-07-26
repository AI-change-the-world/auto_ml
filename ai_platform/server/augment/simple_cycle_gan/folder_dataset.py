import os

import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import Dataset


# --------- 数据集 ---------
class ImageFolderDataset(Dataset):
    def __init__(self, folder):
        self.paths = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.endswith(("jpg", "png"))
        ]
        self.transform = transforms.Compose(
            [
                transforms.Resize((256, 256)),
                transforms.ToTensor(),
                transforms.Normalize([0.5] * 3, [0.5] * 3),
            ]
        )

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        img = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(img)
