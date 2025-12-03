import numpy as np

class GlobalContextProvider:
    def __init__(self, mode="random", dim=16):
        self.mode = mode
        self.dim = dim

    def get(self):
        if self.mode == "random":
            return np.random.randn(self.dim)
        elif self.mode == "real":
            # TODO: 실제 스케줄, 시간대 등에서 feature 추출
            return self._load_real_context()
        else:
            raise ValueError("Unknown context mode")

    def _load_real_context(self):
        # placeholder
        return np.random.randn(self.dim)
