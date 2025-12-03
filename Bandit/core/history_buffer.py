class HistoryBuffer:
    def __init__(self):
        self.history = []   # list of dicts

    def log_action(self, global_context, arm_id, arm_context):
        entry = {
            "G": global_context,
            "arm_id": arm_id,
            "A": arm_context,
            "reward": None
        }
        self.history.append(entry)
        return len(self.history) - 1  # index for future reward

    def set_reward(self, entry_idx, reward):
        self.history[entry_idx]["reward"] = reward

    def get_trainable_samples(self):
        return [h for h in self.history if h["reward"] is not None]
