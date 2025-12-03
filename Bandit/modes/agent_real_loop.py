import time
import queue

def agent_real_loop(bandit, context_queue, reward_queue):
    print("[agent] starting real agent loop...")
    
    while True:
        # 1) global context 도착했는지 확인
        try:
            G = context_queue.get_nowait()
            arm, idx = bandit.infer_with_context(G)
            print(f"[agent] inferred arm={arm}, idx={idx}")
        except queue.Empty:
            pass
        
        # 2) reward 도착했는지 확인
        try:
            (entry_idx, reward) = reward_queue.get_nowait()
            bandit.give_reward(entry_idx, reward)
            print(f"[agent] reward received → update done")
        except queue.Empty:
            pass

        time.sleep(0.01)
