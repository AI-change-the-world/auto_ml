import os

import torch
from folder_dataset import ImageFolderDataset
from model import CycleConsistencyLoss, Discriminator, GANLoss, Generator
from torch.utils.data import DataLoader
from torchvision.utils import save_image


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    epochs = 10000
    batch_size = 32
    lr = 2e-4

    G_AB = Generator().to(device)
    G_BA = Generator().to(device)
    D_A = Discriminator().to(device)
    D_B = Discriminator().to(device)

    gan_loss = GANLoss()
    cycle_loss = CycleConsistencyLoss()

    opt_G = torch.optim.Adam(
        list(G_AB.parameters()) + list(G_BA.parameters()), lr=lr, betas=(0.5, 0.999)
    )
    opt_D_A = torch.optim.Adam(D_A.parameters(), lr=lr / 2, betas=(0.5, 0.999))
    opt_D_B = torch.optim.Adam(D_B.parameters(), lr=lr / 2, betas=(0.5, 0.999))

    dataset_A = ImageFolderDataset("./good_92")
    dataset_B = ImageFolderDataset("./defect")
    loader_A = DataLoader(dataset_A, batch_size=batch_size, shuffle=True)
    loader_B = DataLoader(dataset_B, batch_size=batch_size, shuffle=True)

    os.makedirs("./outputs", exist_ok=True)

    for epoch in range(epochs):
        for real_A, real_B in zip(loader_A, loader_B):
            real_A = real_A.to(device)
            real_B = real_B.to(device)

            # === Train Generators ===
            fake_B = G_AB(real_A)
            fake_A = G_BA(real_B)

            rec_A = G_BA(fake_B)
            rec_B = G_AB(fake_A)

            loss_G = gan_loss(D_B(fake_B), True) + gan_loss(D_A(fake_A), True)
            loss_G += cycle_loss(real_A, rec_A) + cycle_loss(real_B, rec_B)

            opt_G.zero_grad()
            loss_G.backward()
            opt_G.step()

            # === Train Discriminators ===
            loss_D_A = gan_loss(D_A(real_A), True) + gan_loss(
                D_A(fake_A.detach()), False
            )
            loss_D_B = gan_loss(D_B(real_B), True) + gan_loss(
                D_B(fake_B.detach()), False
            )

            opt_D_A.zero_grad()
            loss_D_A.backward()
            opt_D_A.step()

            opt_D_B.zero_grad()
            loss_D_B.backward()
            opt_D_B.step()

        print(
            f"[Epoch {epoch+1}] G: {loss_G.item():.4f} | D_A: {loss_D_A.item():.4f} | D_B: {loss_D_B.item():.4f}"
        )

        if (epoch + 1) % 1000 == 0:
            save_image((fake_B * 0.5 + 0.5), f"./outputs/fakeB_epoch{epoch+1}.png")
            save_image((fake_A * 0.5 + 0.5), f"./outputs/fakeA_epoch{epoch+1}.png")

    torch.save(G_AB.to("cpu").state_dict(), "./outputs/generator_A.pth")


if __name__ == "__main__":
    train()
