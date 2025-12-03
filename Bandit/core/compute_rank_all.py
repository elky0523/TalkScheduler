# bandit/core/compute_rank_all.py

import json
from pathlib import Path


def compute_rank_all(user_ids, user_cache):
    """
    user_ids: ["1", "2", "3"]
    user_cache: {
        "1": {
            "dong": [...],      # LIST [{구, 동, score}]
            "gu": [...],        # LIST [{구, score}]
            "schedule": {...}   # DICT {"score_2025-12-13-16": value}
        },
        ...
    }

    return:
    {
        "dong_rank": [...],
        "gu_rank": [...],
        "schedule_rank": [...]
    }
    """

    # --------------------------------------------------------
    # 0) user_cache validation
    # --------------------------------------------------------
    for uid in user_ids:
        if uid not in user_cache:
            raise ValueError(f"user_cache is missing for user_id={uid}")

    # --------------------------------------------------------
    # 1) Dong Ranking
    # --------------------------------------------------------
    dong_scores = {}   # {(gu, dong): [scores]}

    for uid in user_ids:
        entries = user_cache[uid]["dong"]  # list

        for entry in entries:
            gu = entry.get("구")
            dong = entry.get("동")
            score = entry.get("score")

            if gu and dong and score is not None:
                key = (gu, dong)
                dong_scores.setdefault(key, []).append(float(score))

    dong_rank = []
    for (gu, dong), scores in dong_scores.items():
        avg = sum(scores) / len(scores)
        dong_rank.append({
            "구": gu,
            "동": dong,
            "average_score": round(avg, 4)
        })

    dong_rank.sort(key=lambda x: x["average_score"], reverse=True)

    # --------------------------------------------------------
    # 2) Gu Ranking
    # --------------------------------------------------------
    gu_scores = {}   # {gu: [scores]}

    for uid in user_ids:
        entries = user_cache[uid]["gu"]

        for entry in entries:
            gu = entry.get("구")
            score = entry.get("score")

            if gu and score is not None:
                gu_scores.setdefault(gu, []).append(float(score))

    gu_rank = []
    for gu, scores in gu_scores.items():
        avg = sum(scores) / len(scores)
        gu_rank.append({
            "구": gu,
            "average_score": round(avg, 4)
        })

    gu_rank.sort(key=lambda x: x["average_score"], reverse=True)

    # --------------------------------------------------------
    # 3) Schedule Ranking
    # IMPORTANT: keys like "score_2025-12-13-16" → "2025-12-13-16"
    # --------------------------------------------------------
    schedule_scores = {}   # {clean_key: [scores]}

    for uid in user_ids:
        sched_dict = user_cache[uid]["schedule"]

        for raw_key, score in sched_dict.items():
            if score is None:
                continue

            # ⚠ Remove prefix "score_"
            if raw_key.startswith("score_"):
                clean_key = raw_key.replace("score_", "", 1)
            else:
                clean_key = raw_key   # unexpected case: use raw

            schedule_scores.setdefault(clean_key, []).append(float(score))

    schedule_rank = []
    for sched_key, scores in schedule_scores.items():
        avg = sum(scores) / len(scores)
        schedule_rank.append({
            "schedule": sched_key,
            "average_score": round(avg, 4)
        })

    schedule_rank.sort(key=lambda x: x["average_score"], reverse=True)

    # --------------------------------------------------------
    # 4) Final Return
    # --------------------------------------------------------
    return {
        "dong_rank": dong_rank,
        "gu_rank": gu_rank,
        "schedule_rank": schedule_rank
    }
