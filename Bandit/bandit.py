from bandit.core.history_buffer import HistoryBuffer
from bandit.inference.inferencer import Inferencer

class ContextualBandit:
    def __init__(self, global_provider, arms, model):
        self.global_provider = global_provider
        self.arms = arms  # dict
        self.model = model
        self.buffer = HistoryBuffer()
        self.inferencer = Inferencer(arms, model)

    def infer(self):
        G = self.global_provider.get()
        arm_id = self.inferencer.select_arm(G)
        entry_idx = self.buffer.log_action(G, arm_id, self.arms[arm_id])
        return arm_id, entry_idx
    def infer_with_context(self, G):
        arm_id = self.inferencer.select_arm(G)
        idx = self.buffer.log_action(G, arm_id, self.arms[arm_id])
        return arm_id, idx

    def give_reward(self, entry_idx, reward):
        self.buffer.set_reward(entry_idx, reward)
        samples = self.buffer.get_trainable_samples()
        self.model.update(samples)    # simple design
        
    def rank_arms_with_context(self, G):
        """
        Rank all arms given context G.
        Returns: list of (arm_id, score) tuples sorted by score descending
        """
        ranked = self.inferencer.rank_arms(G)
        return ranked
    
    def save_weights(self, filepath):
        """Save model weights to file"""
        self.model.save_weights(filepath)
        print(f"[Bandit] Weights saved to {filepath}")
    
    def load_weights(self, filepath):
        """Load model weights from file"""
        self.model.load_weights(filepath)
        print(f"[Bandit] Weights loaded from {filepath}")
