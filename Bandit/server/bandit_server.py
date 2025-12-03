# bandit/server/bandit_server.py

import queue
import time
import threading

class BanditServer:
    def __init__(self, bandit_model, inbound_queue, outbound_queue):
        self.model = bandit_model
        self.in_q = inbound_queue
        self.out_q = outbound_queue

        self.last_idx = None
        self.last_arm = None
        self.last_context = None

        self._running = False  # ← 종료 플래그

    def start(self):
        """서버 스레드 시작"""
        self._running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        """서버 종료 요청"""
        self._running = False

    def run(self):
        print("[bandit] server started.")

        while self._running:
            try:
                msg = self.in_q.get(timeout=0.05)   # ← time.sleep 대신 queue timeout
                self.handle_message(msg)
            except queue.Empty:
                pass

        print("[bandit] server stopped.")

    def handle_message(self, msg):
        msg_type = msg["type"]

        if msg_type == "context":
            G = msg["context"]
            arm, idx = self.model.infer_with_context(G)

            self.last_arm = arm
            self.last_idx = idx
            self.last_context = G

            self.out_q.put({
                "type": "infer_result",
                "arm": arm,
                "idx": idx
            })
            print(f"[bandit] inferred arm={arm}, idx={idx}")

        elif msg_type == "reward":
            reward = msg["reward"]
            idx = msg.get("idx", self.last_idx)

            if idx is None:
                print("[bandit] ERROR: reward arrived but no last idx")
                return

            self.model.give_reward(idx, reward)
            print(f"[bandit] updated: idx={idx}, reward={reward}")

        else:
            print(f"[bandit] Unknown message type: {msg_type}")
