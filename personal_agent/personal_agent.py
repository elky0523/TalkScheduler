# personal_agent.py

class PersonalAgent:
    def __init__(self, user_id, chat_window, integrated_agent_callback):
        """
        user_id: "user1" or "user2"
        chat_window: ChatWindow instance
        integrated_agent_callback: function to send data to integrated agent
        """
        self.user_id = user_id
        self.chat = chat_window
        self.send_to_integrated = integrated_agent_callback

        self.base_info = None
        self.schedule_info = None

        # GUI에서 메시지가 오면 personal agent로 전달됨
        self.chat.message_handler = self.handle_user_message

        # 시작하자마자 base_info 질문
        self.ask_base_info()

    def ask_base_info(self):
        self.chat.display("Agent: 기본 정보를 입력해주세요.")

    def handle_user_message(self, text):
        """사용자가 채팅창에 입력했을 때 호출된다."""
        if self.base_info is None:
            self.base_info = text
            self.chat.display(f"Agent: 기본 정보 저장됨: {text}")
            return

        # schedule_info 단계라면
        if self.schedule_info is None:
            self.schedule_info = text
            self.chat.display(f"Agent: 스케줄 정보 저장됨: {text}")

            # 통합 에이전트에게 제출
            payload = {
                "user_id": self.user_id,
                "base_info": self.base_info,
                "schedule_info": self.schedule_info
            }
            self.send_to_integrated(payload)
