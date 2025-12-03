import numpy as np
from .base_model import BaseModel

class LinearModel(BaseModel):
    def __init__(self, d_g, d_a, lr=0.01):
        self.M = np.random.randn(d_g, d_a) * 0.1
        self.lr = lr

    def score(self, G, A):
        return float(G @ self.M @ A)

    def update(self, samples):
        for s in samples:
            G = s["G"]
            A = s["A"]
            r = s["reward"]

            pred = self.score(G, A)
            grad = (pred - r)
            grad = np.clip(grad, -3, 3)
            # d/dM = grad * (G outer A)
            self.M -= self.lr * grad * np.outer(G, A)
