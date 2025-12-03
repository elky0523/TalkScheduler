# integrated_agent.py

# 임베더 불러오기
from embedding.infer_pipeline import embed_for_agent
from embedding.infer_pipeline import init_infer_pipeline
import threading
import time
import queue
import numpy as np

class IntegratedAgent:
    def __init__(self, chat_window, num_users, bandit_in_queue, bandit_out_queue):
        self.chat = chat_window
        self.chat.message_handler = self.handle_user_message

        self.expected = num_users
        self.collected = []

        self.notify_personal_agents = None
        self.bandit_in_q = bandit_in_queue
        self.bandit_out_q = bandit_out_queue
        # 🔥 밴딧 리스너 스레드 시작
        if self.bandit_out_q is not None:
            threading.Thread(target=self.listen_bandit, daemon=True).start()
            print("IntegratedAgent: bandit listener started.")
        # ✅ 여기서 단 한 번만 초기화
        init_infer_pipeline()
        print("IntegratedAgent: infer pipeline initialized.")

    def listen_bandit(self):
        """밴딧 서버가 보낸 infer 결과를 듣는 백그라운드 스레드"""
        print("[IntegratedAgent] bandit listener running...")

        while True:
            try:
                msg = self.bandit_out_q.get_nowait()

                msg_type = msg.get("type")

                if msg_type == "infer_result":
                    arm = msg["arm"]
                    idx = msg["idx"]
                    self.chat.display(f"Bandit 결과: arm={arm}, idx={idx}")

                elif msg_type == "error":
                    self.chat.display(f"Bandit 오류: {msg.get('detail')}")

                else:
                    self.chat.display(f"Bandit 메시지 수신: {msg}")

            except queue.Empty:
                pass

            time.sleep(0.01)

    def handle_user_message(self, text):
        # "integrate" 트리거    
        text = text.strip().lower()
        if text == "integrate":
            self.chat.display("Agent: 통합 시작합니다.")
            self.notify_personal_agents("request_schedule_info")
            return

        self.chat.display("Agent: 알 수 없는 명령입니다. (integrate만 지원)")

    def receive_from_personal(self, payload):
        """PersonalAgent가 넘긴 정보를 받는다."""
        self.collected.append(payload)
        self.chat.display(f"Agent: 개인 에이전트 {payload['user_id']} 제출 받음.")

        if len(self.collected) == self.expected:
            self.finish_integration()

    def finish_integration(self):

        self.chat.display("Agent: 모든 사용자 정보 수집 완료.")
        self.chat.display("Agent: 임베딩 중 ...")

        # 1) 텍스트 결합
        combined_text = ""
        for p in self.collected:
            combined_text += f"[User {p['user_id']} Base]\n{p['base_info']}\n\n"
            combined_text += f"[User {p['user_id']} Schedule]\n{p['schedule_info']}\n\n"

        # 2) embed_for_agent 존재 여부 체크
        if embed_for_agent is None:
            self.chat.display("❌ 임베딩 모듈을 불러오지 못했습니다. (embed_for_agent is None)")
            self.finish_bandit_dummy()
            return

        try:
            embedding_vector = embed_for_agent(combined_text)

            # ⭐ 핵심: 통합 에이전트 내부 상태에 저장
            self.current_context_embedding = embedding_vector  

            self.chat.display("Agent: 임베딩 완료!")
            self.chat.display(f"임베딩 벡터 차원: {len(embedding_vector)}")
            embedding_vector_16 = self.reduce_to_16dims(embedding_vector)

        except Exception as e:
            self.chat.display("❌ 임베딩 중 오류 발생!")
            self.chat.display(str(e))
            self.finish_bandit_dummy()
            return

        # 3) 실제 밴딧과 연결할 부분(현재는 더미)
        # self.finish_bandit_dummy()
        self.bandit_in_q.put({
            "type": "context",
            "context": embedding_vector_16
        })


    def finish_bandit_dummy(self):
        """밴딧 부분 테스트용"""
        self.chat.display("Agent: 밴딧 추론 중 ... (dummy)")

        # ⭐ 밴딧에게 넘길 때 이렇게 넘기게 될 예정
        # bandit.infer_with_context(self.current_context_embedding)

        self.chat.display("Agent: 추천 결과 → '월요일 오후 3시'")
    def reduce_to_16dims(self, vec):
        
        vec = np.array(vec)
        block = len(vec) // 16
        small = []
        for i in range(16):
            start = i * block
            end = (i+1) * block
            small.append(np.mean(vec[start:end]))
        return small