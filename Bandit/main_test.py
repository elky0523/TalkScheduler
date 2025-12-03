# main.py

import queue
from bandit.core.global_context import GlobalContextProvider
from bandit.core.arm_context import ArmContextProvider
from bandit.models.linear_model import LinearModel
from bandit.models.neural_model import NeuralModel
from bandit.bandit import ContextualBandit

from bandit.modes.dataset_train_loop import dataset_train_loop
from bandit.modes.agent_real_loop import agent_real_loop
from bandit.modes.agent_test_loop import agent_test_loop
from bandit.core.dataset_loader import DatasetLoader
# ---------------------------------------------------
# main dispatcher
# ---------------------------------------------------
def main(mode="agent-test"):
    print(f"\n[main] running in mode = {mode}\n")

    # -----------------------------------------------
    # Arm context (전 모드 공통)
    # -----------------------------------------------
    arm_pv = ArmContextProvider(mode="random", num_arms=5, dim=16)
    arms = arm_pv.load()

    # -----------------------------------------------
    # Model 선택 (전 모드 공통)
    # -----------------------------------------------
    model = LinearModel(d_g=16, d_a=16)
    # model = NeuralModel(d_g=16, d_a=16)

    # -----------------------------------------------
    # Bandit 객체 생성
    # global_pv 사용 여부는 모드에 따라 다름
    #   dataset 모드 → global provider 필요 없음
    #   agent 모드 → global provider 필요 없음
    #   agent-test 모드 → global provider 필요 없음
    #   단, 내부 API 일관성을 위해 넣기는 함
    # -----------------------------------------------
    # Real agent 모드에서는 절대 global_pv.get()을 호출하지 않는다.
    global_pv = GlobalContextProvider(mode="random", dim=16)

    bandit = ContextualBandit(global_pv, arms, model)

    # -----------------------------------------------
    # Mode Dispatch
    # -----------------------------------------------
    if mode == "dataset":
        dataset_loader = DatasetLoader(
            mode="random",  # 또는 "real"
            file_path="dataset.csv",  # real 모드일 때만 필요
            g_dim=16,
            num_arms=5,
            size=1004  # random dataset size
        )
        dataset = dataset_loader.load()
        dataset_train_loop(bandit, dataset)

    elif mode == "agent":
        # 외부 시스템이 context_queue / reward_queue에 값을 전달하는 구조
        context_queue = queue.Queue()
        reward_queue = queue.Queue()
        agent_real_loop(bandit, context_queue, reward_queue)

    elif mode == "agent-test":
        # agent-test 모드는 내부에서 랜덤 context를 생성함
        agent_test_loop(bandit)

    else:
        raise ValueError(f"Unknown mode: {mode}")


# ---------------------------------------------------
# run
# ---------------------------------------------------
if __name__ == "__main__":
    main("dataset")
