class BaseModel:
    def score(self, G, A):
        raise NotImplementedError

    def update(self, samples):
        raise NotImplementedError
