import json
import numpy as np

class ArmContextProvider:
    def __init__(self, mode="random", num_arms=10, dim=16, file_path=None):
        self.mode = mode
        self.num_arms = num_arms
        self.dim = dim
        self.file_path = file_path

    def load(self):
        if self.mode == "random":
            return {i: np.random.randn(self.dim) for i in range(self.num_arms)}
        elif self.mode == "real":
            with open(self.file_path, "r") as f:
                return json.load(f)  # dict {arm_id: embedding vector}
        else:
            raise ValueError("Unknown arm mode")
