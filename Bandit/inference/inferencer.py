import numpy as np

class Inferencer:
    def __init__(self, arms, model):
        self.arms = arms
        self.model = model

    def select_arm(self, G):
        scores = {}
        for arm_id, A in self.arms.items():
            scores[arm_id] = self.model.score(G, A)
        return max(scores, key=scores.get)
    
    def rank_arms(self, G):
        """
        Return full ranking of all arms from best to worst.
        
        Returns:
            ranked_arms: list of (arm_id, score) tuples sorted by score descending
        """
        scores = {}
        for arm_id, A in self.arms.items():
            scores[arm_id] = self.model.score(G, A)
        
        # Sort by score descending
        ranked_arms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked_arms
    
    def get_top_k(self, G, k=3):
        """
        Get top k arms.
        
        Returns:
            list of (arm_id, score) tuples for top k arms
        """
        ranked = self.rank_arms(G)
        return ranked[:k]
    
    def filter_and_rank(self, G, filter_fn, k=None):
        """
        Filter arms and return ranking.
        
        Args:
            G: global context
            filter_fn: function that takes arm_id and returns True to include
            k: if specified, return only top k
            
        Returns:
            list of (arm_id, score) tuples
        """
        scores = {}
        for arm_id, A in self.arms.items():
            if filter_fn(arm_id):
                scores[arm_id] = self.model.score(G, A)
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if k is not None:
            ranked = ranked[:k]
            
        return ranked