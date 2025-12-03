class NeuralTrainer:
    def __init__(self, model):
        self.model = model

    def train(self, samples):
        self.model.update(samples)
