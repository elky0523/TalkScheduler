# bandit/core/dataset_loader.py

import json
import itertools
from pathlib import Path

from bandit.core.compute_rank_all import compute_rank_all
from embedding.infer_pipeline import embed_for_agent  # for global context embedding


class DatasetLoader:
    def __init__(self,
                 user_ids,
                 base_info_dir,
                 schedule_info_dir,
                 dong_score_dir,
                 gu_score_dir,
                 schedule_score_dir,
                 schedule_arm_path,
                 g_dim=16):
        """
        user_ids: 전체 사용자 id 리스트 ["1","2","3","4"...]
        base_info_dir: Base_Info_x.json dir
        schedule_info_dir: Schedule_Info_x.json dir
        
        score files:
            Person_x_Location_Dong_Score.json
            Person_x_Location_Gu_Score.json
            Person_x_Schedule_Score.json

        schedule_arm_path: schedule_arm_vectors.json
        """
        self.user_ids = [str(uid) for uid in user_ids]
        self.base_info_dir = Path(base_info_dir)
        self.schedule_info_dir = Path(schedule_info_dir)

        self.dong_dir = Path(dong_score_dir)
        self.gu_dir = Path(gu_score_dir)
        self.schedule_dir = Path(schedule_score_dir)

        self.schedule_arm_path = Path(schedule_arm_path)
        self.g_dim = g_dim

        # 로드용 캐시
        self.user_cache = {}

    def load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------------------------------------------------
    # STEP 1 : raw score JSON load → user_cache 생성
    # -------------------------------------------------------------------------
    def build_user_cache(self):
        for uid in self.user_ids:

            dong_path = self.dong_dir / f"Person_{uid}_Location_Dong_Score.json"
            gu_path = self.gu_dir / f"Person_{uid}_Location_Gu_Score.json"
            schedule_path = self.schedule_dir / f"Person_{uid}_Schedule_Score.json"

            dong = self.load_json(dong_path)
            gu = self.load_json(gu_path)
            schedule = self.load_json(schedule_path)

            self.user_cache[uid] = {
                "dong": dong,
                "gu": gu,
                "schedule": schedule
            }

    # -------------------------------------------------------------------------
    # STEP 2 : 모든 사용자 permutation 생성
    # -------------------------------------------------------------------------
    def all_user_groups(self):
        groups = []
        for r in range(2, len(self.user_ids) + 1):
            for comb in itertools.combinations(self.user_ids, r):
                groups.append(list(comb))
        return groups

    # -------------------------------------------------------------------------
    # STEP 3 : base+schedule JSON merge → embed
    # -------------------------------------------------------------------------
    def embed_user_group(self, group_ids):
        try:
            merged_text = ""

            for uid in group_ids:
                base_path = self.base_info_dir / f"Base_Info_{uid}.json"
                sched_path = self.schedule_info_dir / f"Schedule_Info_{uid}.json"

                base_json = self.load_json(base_path)
                sched_json = self.load_json(sched_path)

                merged_user = {**base_json, **sched_json}

                merged_text += json.dumps(merged_user, ensure_ascii=False) + "\n"

        except Exception:
            # fallback: 그냥 텍스트 concat
            merged_text = "\n".join([f"[User {u}]" for u in group_ids])

        # embed_for_agent → 16-dim 반환 (projected)
        g_vec = embed_for_agent(merged_text)
        return g_vec

    # -------------------------------------------------------------------------
    # STEP 4 : reward 계산 함수
    # simple baseline : top=1.0, bottom≈0
    # -------------------------------------------------------------------------
    def reward_from_rank(self, rank_list, key_field, arm_key):
        """
        rank_list: list of dicts (dong/gu/schedule rank)
        key_field: "schedule"
        arm_key: "2025-12-13-16"
        """
        for idx, row in enumerate(rank_list):
            if row[key_field] == arm_key:
                return 1 - idx / len(rank_list)

        return 0.0  # not found case

    # -------------------------------------------------------------------------
    # STEP 5 : dataset 생성
    # -------------------------------------------------------------------------
    def load(self):

        print("[dataset] building cache...")
        self.build_user_cache()

        print("[dataset] load schedule arms...")
        schedule_arms = self.load_json(self.schedule_arm_path)   # dict {arm_key: [vector]}

        dataset = []

        print("[dataset] generating user groups...")
        groups = self.all_user_groups()

        print(f"[dataset] total user groups = {len(groups)}")

        for group in groups:

            # 1) ranking 계산
            ranks = compute_rank_all(group, self.user_cache)
            sched_rank = ranks["schedule_rank"]  # list sorted

            # 2) embedding vector (global context)
            g_vec = self.embed_user_group(group)

            # 3) 각 arm에 대해 dataset entry 생성
            for arm_key, arm_vec in schedule_arms.items():
                reward = self.reward_from_rank(sched_rank, "schedule", arm_key)

                entry = {
                    "global_context": g_vec,
                    "arm_context": arm_vec,
                    "chosen_arm": arm_key,
                    "reward": reward
                }
                dataset.append(entry)

        print(f"[dataset] final dataset size = {len(dataset)}")
        return dataset
