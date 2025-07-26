import torch
import torch.nn as nn


class SelfAttention(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.query_conv = nn.Conv2d(in_dim, in_dim // 8, 1)
        self.key_conv = nn.Conv2d(in_dim, in_dim // 8, 1)
        self.value_conv = nn.Conv2d(in_dim, in_dim, 1)
        self.softmax = nn.Softmax(dim=-1)
        self.gamma = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        batch, C, width, height = x.size()
        proj_query = self.query_conv(x).view(batch, -1, width * height).permute(0, 2, 1)
        proj_key = self.key_conv(x).view(batch, -1, width * height)
        energy = torch.bmm(proj_query, proj_key)
        attention = self.softmax(energy)
        proj_value = self.value_conv(x).view(batch, -1, width * height)

        out = torch.bmm(proj_value, attention.permute(0, 2, 1))
        out = out.view(batch, C, width, height)

        out = self.gamma * out + x
        return out


class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, 3, padding=1),
            nn.BatchNorm2d(channels),
        )

    def forward(self, x):
        return nn.ReLU(inplace=True)(x + self.block(x))


# --------- Generator ---------
class Generator(nn.Module):
    def __init__(self, z_dim, img_channels):
        super().__init__()
        self.fc = nn.Linear(z_dim, 8 * 8 * 512)
        self.net = nn.Sequential(
            nn.BatchNorm2d(512),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(512, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=True),
            ResBlock(256),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(256, 128, 3, 1, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),
            SelfAttention(128),  # 注意力模块
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 64, 3, 1, 1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=True),
            ResBlock(64),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(64, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(32, img_channels, 3, 1, 1),
            nn.Tanh(),
        )

    def forward(self, z):
        x = self.fc(z).view(-1, 512, 8, 8)
        return self.net(x)


# --------- Discriminator ---------
class Discriminator(nn.Module):
    def __init__(self, img_channels):
        super().__init__()

        def block(in_c, out_c):
            return nn.Sequential(
                nn.Conv2d(in_c, out_c, 4, 2, 1),
                nn.LeakyReLU(0.2, inplace=True),
                nn.Dropout2d(0.25 if in_c <= 128 else 0.35),
            )

        self.net = nn.Sequential(
            block(img_channels, 64),  # 256->128
            block(64, 128),  # 128->64
            block(128, 256),  # 64->32
            block(256, 512),  # 32->16
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(512 * 16 * 16, 1))

    def forward(self, x):
        x = self.net(x)
        x = self.classifier(x)
        return x
