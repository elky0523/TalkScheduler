# bandit/core/load_user_scores.py

import json
from pathlib import Path


def load_json_safe(path: Path):
    """파일이 없으면 None, 있으면 JSON dict/list 반환."""
    if not path.exists():
        print(f"[Warning] JSON 파일 없음: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] JSON 로딩 실패: {path} ({e})")
        return None


def load_all_user_scores(user_ids, scheduling_root="Scheduling"):
    """
    user_ids: ["1", "2", "3"]
    return:
        {
            "1": { "dong": [...], "gu": [...], "schedule": {...} },
            ...
        }
    """

    root = Path(scheduling_root)

    # 하위 폴더
    p_dong = root / "Result_Location_Dong_Score"
    p_gu = root / "Result_Location_Gu_Score"
    p_schedule = root / "Result_Schedule_Score"

    user_cache = {}

    for uid in user_ids:
        uid = str(uid)

        # 파일명
        f_dong = p_dong / f"Person_{uid}_Location_Dong_Score.json"
        f_gu = p_gu / f"Person_{uid}_Location_Gu_Score.json"
        f_sch = p_schedule / f"Person_{uid}_Schedule_Score.json"

        # 로딩
        dong_data = load_json_safe(f_dong) or []
        gu_data = load_json_safe(f_gu) or []
        schedule_data = load_json_safe(f_sch) or {}

        # schedule_data 키 변환 ("score_2025-12-06-18" → "2025-12-06-18")
        cleaned_schedule = {}
        for k, v in schedule_data.items():
            if k.startswith("score_"):
                cleaned_schedule[k.replace("score_", "")] = v
            else:
                cleaned_schedule[k] = v

        # user_cache 저장
        user_cache[uid] = {
            "dong": dong_data,
            "gu": gu_data,
            "schedule": cleaned_schedule
        }

    print(f"[load_all_user_scores] loaded users: {list(user_cache.keys())}")
    return user_cache
