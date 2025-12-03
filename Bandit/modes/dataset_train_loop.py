def dataset_train_loop(bandit, dataset):
    for step, sample in enumerate(dataset):
        G = sample["global_context"]
        arm = sample["arm"]
        reward = sample["reward"]
        A = bandit.arms[arm]

        # inference-like logging (index 반환)
        idx = bandit.buffer.log_action(G, arm, A)

        # now reward is known immediately
        bandit.give_reward(idx, reward)

        if step % 1000 == 0:
            print(f"[train] step={step}")
