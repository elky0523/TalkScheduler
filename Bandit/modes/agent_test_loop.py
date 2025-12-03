import time
import numpy as np
import random

def agent_test_loop(bandit, context_dim=16, reward_prob=0.3):
    print("[agent-test] starting test loop...")

    pending_actions = []  # (idx, arm) 저장

    while True:
        # 1) every 0.2 sec, generate a fake context
        G = np.random.randn(context_dim)
        arm, idx = bandit.infer_with_context(G)
        pending_actions.append((idx, arm))
        print(f"[test] inferred arm {arm} (idx={idx})")

        # 2) with prob = reward_prob, simulate reward arrival
        if pending_actions and random.random() < reward_prob:
            idx, arm = random.choice(pending_actions)
            reward = float(arm % 2 == 0)
            print(f"[test] reward {reward} for arm {arm}")
            bandit.give_reward(idx, reward)

        time.sleep(0.2)
