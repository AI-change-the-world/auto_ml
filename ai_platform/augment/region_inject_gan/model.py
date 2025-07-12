import torch
import torch.nn as nn
import torch.nn.functional as F

# ------------------------
# Self-Attention 模块
# ------------------------
class SelfAttention(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.query_conv = nn.Conv2d(in_dim, in_dim // 8, 1)
        self.key_conv = nn.Conv2d(in_dim, in_dim // 8, 1)
        self.value_conv = nn.Conv2d(in_dim, in_dim, 1)
        self.softmax = nn.Softmax(dim=-1)
        self.gamma = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        B, C, W, H = x.size()
        proj_query = self.query_conv(x).view(B, -1, W * H).permute(0, 2, 1)
        proj_key = self.key_conv(x).view(B, -1, W * H)
        energy = torch.bmm(proj_query, proj_key)
        attention = self.softmax(energy)
        proj_value = self.value_conv(x).view(B, -1, W * H)

        out = torch.bmm(proj_value, attention.permute(0, 2, 1)).view(B, C, W, H)
        return self.gamma * out + x


# ------------------------
# 安全版 Residual Block
# ------------------------
class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu1 = nn.ReLU(inplace=False)

        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)
        self.relu_out = nn.ReLU(inplace=False)

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu1(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out = out + residual
        out = self.relu_out(out)
        return out


# ------------------------
# 背景生成器 BackgroundGenerator
# ------------------------
class BackgroundGenerator(nn.Module):
    def __init__(self, z_dim, img_channels):
        super().__init__()
        self.fc = nn.Linear(z_dim, 8 * 8 * 512)

        self.block1 = nn.Sequential(
            nn.BatchNorm2d(512),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(512, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=False),
        )
        self.res1 = ResBlock(256)

        self.block2 = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(256, 128, 3, 1, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=False),
            SelfAttention(128),
        )

        self.block3 = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 64, 3, 1, 1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=False),
        )
        self.res2 = ResBlock(64)

        self.block4 = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(64, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2, inplace=False),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(32, img_channels, 3, 1, 1),
            nn.Tanh(),
        )

    def forward(self, z):
        x = self.fc(z).view(-1, 512, 8, 8)
        x = self.block1(x)
        x = self.res1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.res2(x)
        x = self.block4(x)
        return x


# ------------------------
# 缺陷注入生成器 InjectGenerator
# ------------------------
class InjectGenerator(nn.Module):
    def __init__(self, z_dim, img_channels):
        super().__init__()
        self.fc = nn.Linear(z_dim, 8 * 8 * 512)

        self.block1 = nn.Sequential(
            nn.BatchNorm2d(513),  # 512 + 1(mask)
            nn.Upsample(scale_factor=2),
            nn.Conv2d(513, 256, 3, 1, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=False),
        )
        self.res1 = ResBlock(256)

        self.block2 = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(256, 128, 3, 1, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=False),
            SelfAttention(128),
        )

        self.block3 = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 64, 3, 1, 1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=False),
        )
        self.res2 = ResBlock(64)

        self.block4 = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(64, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2, inplace=False),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(32, img_channels, 3, 1, 1),
            nn.Tanh()
        )

    def forward(self, z, mask):
        x = self.fc(z).view(-1, 512, 8, 8)
        mask = F.interpolate(mask, size=(8, 8), mode='nearest')
        x = torch.cat([x, mask], dim=1)
        x = self.block1(x)
        x = self.res1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.res2(x)
        x = self.block4(x)
        return x


# ------------------------
# 判别器 Discriminator
# ------------------------
class Discriminator(nn.Module):
    def __init__(self, img_channels):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(img_channels, 64, 4, stride=2, padding=1),  # 128x128
            nn.LeakyReLU(0.2, inplace=False),
            nn.Conv2d(64, 128, 4, stride=2, padding=1),  # 64x64
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=False),
            nn.Conv2d(128, 256, 4, stride=2, padding=1),  # 32x32
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=False),
            SelfAttention(256),
            nn.Conv2d(256, 512, 4, stride=2, padding=1),  # 16x16
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, inplace=False),
            nn.Conv2d(512, 1, 4, stride=2, padding=1),  # 8x8
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)
    

class BgDiscriminator(nn.Module):
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
