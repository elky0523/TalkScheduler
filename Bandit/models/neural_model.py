import torch
import torch.nn as nn
import numpy as np
from .base_model import BaseModel

class NeuralModel(BaseModel):
    def __init__(self, d_g, d_a, hidden=64, lr=1e-3):
        super().__init__()
        self.d_g = d_g
        self.d_a = d_a

        self.net = nn.Sequential(
            nn.Linear(d_g + d_a, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1)
        )
        self.optim = torch.optim.Adam(self.net.parameters(), lr=lr)

    def score(self, G, A):
        x = torch.from_numpy(np.concatenate([G, A])).float()
        return float(self.net(x).item())

    def update(self, samples):
        if len(samples) == 0: 
            return

        self.optim.zero_grad()
        loss_sum = 0

        for s in samples:
            G = s["G"]
            A = s["A"]
            r = s["reward"]

            x = torch.from_numpy(np.concatenate([G, A])).float()
            pred = self.net(x)
            loss = (pred - torch.tensor([r], dtype=torch.float))**2
            loss_sum += loss

        loss_sum.backward()
        self.optim.step()
