from typing import Dict, List, Optional
import numpy as np

# Reward magnitude constants
STRONG_REWARD = 1.0  # Direct selection reward
WEAK_REWARD = 0.1    # Indirect selection reward (gu → dong propagation)


class BaseModel:
    
    def __init__(self, d_g, d_a, lr = 0.01):
        self.d_g = d_g
        self.d_a = d_a
        self.lr = lr
        
        # Initialize weight matrix with small random values
        self.M = np.random.randn(d_g, d_a) * 0.1
        
        # Training history for analysis
        self.training_history = []
        
    def score(self, G, A) -> float:
        return float(G @ self.M @ A)
    
    def update(self, samples: List[Dict]) -> None:
        if len(samples) == 0:
            return
        
        for s in samples:
            G = s["G"]
            A = s["A"]
            r = s["reward"]
            
            pred = self.score(G, A)
            grad = (pred - r)
            grad = np.clip(grad, -3, 3)
            
            # Update: M -= lr * grad * (G ⊗ A)
            self.M -= self.lr * grad * np.outer(G, A)
            
            # Log training
            self.log_training(s)
    
    # ========================================================================
    # Hierarchical Reward Methods
    # ========================================================================
    
    def create_weak_rewards(self,G: np.ndarray,dong_arms: Dict[str, np.ndarray],selected_gu: str):
        weak_samples = []
        for dong_key, arm_vec in dong_arms.items():
            if dong_key.startswith(selected_gu + "_"):
                weak_samples.append({
                    'G': G.copy() if isinstance(G, np.ndarray) else np.array(G),
                    'A': arm_vec.copy() if isinstance(arm_vec, np.ndarray) else np.array(arm_vec),
                    'reward': WEAK_REWARD,
                    'arm_id': dong_key,
                    'reward_type': 'weak'
                })
        
        return weak_samples
    
    def create_strong_reward(
        self,
        G: np.ndarray,
        arm_vec: np.ndarray,
        arm_id: str,
        reward_type_name: str = "schedule"
    ) -> Dict:
        return {
            'G': G.copy() if isinstance(G, np.ndarray) else np.array(G),
            'A': arm_vec.copy() if isinstance(arm_vec, np.ndarray) else np.array(arm_vec),
            'reward': STRONG_REWARD,
            'arm_id': arm_id,
            'reward_type': 'strong',
            'selection_type': reward_type_name
        }
    
    def update_with_reward_type(
        self, 
        samples: List[Dict], 
        reward_types: List[str]
    ) -> None:

        enriched = []
        for sample, rtype in zip(samples, reward_types):
            s = sample.copy()
            s['reward_type'] = rtype
            enriched.append(s)
        self.update(enriched)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def log_training(self, sample: Dict) -> None:
        """Log training sample for analysis."""
        self.training_history.append({
            'reward': sample.get('reward'),
            'arm_id': sample.get('arm_id'),
            'reward_type': sample.get('reward_type', 'unknown'),
            'selection_type': sample.get('selection_type', 'unknown')
        })
    
    def get_training_stats(self) -> Dict:
        if not self.training_history:
            return {
                'total_updates': 0,
                'strong_rewards': 0,
                'weak_rewards': 0,
                'avg_reward': 0.0
            }
        
        strong_count = sum(1 for h in self.training_history if h.get('reward_type') == 'strong')
        weak_count = sum(1 for h in self.training_history if h.get('reward_type') == 'weak')
        avg = np.mean([h['reward'] for h in self.training_history])
        
        return {
            'total_updates': len(self.training_history),
            'strong_rewards': strong_count,
            'weak_rewards': weak_count,
            'avg_reward': float(avg)
        }
    
    def reset_history(self) -> None:
        """Clear training history."""
        self.training_history = []
    
    def reset_model(self) -> None:
        """Reset model to initial random weights."""
        self.M = np.random.randn(self.d_g, self.d_a) * 0.1
        self.reset_history()
    
    def save_model(self, filepath: str) -> None:
        """Save model weights to file."""
        np.save(filepath, self.M)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str) -> None:
        """Load model weights from file."""
        self.M = np.load(filepath)
        print(f"Model loaded from {filepath}")