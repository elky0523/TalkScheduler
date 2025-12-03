Gold_Information/
├── 📂 Location_Arm/                # [Input] 장소 추천 후보군 (Search Space)
│   ├── location_context_dong.json      # 행정동 단위 장소 정보
│   └── location_context_gu.json        # 자치구 단위 장소 정보
│
├── 📂 Location_Gold/               # [Input] 장소 정답 데이터 (Ground Truth)
│   ├── Location_Gold_Base_Info_1.json  # Person 1의 장소 정답
│   ├── ...
│   └── Location_Gold_Base_Info_30.json
│
├── 📂 Location_Gold_Weight/        # [Input] 장소 정답 가중치
│   ├── Location_Gold_Weight_Base_Info_1.json
│   ├── ...
│   └── Location_Gold_Weight_Base_Info_30.json
│
├── 📂 Schedule_Arm/                # [Input] 일정 추천 후보군
│   └── schedule_arm_vectors.json       # 일정 벡터 임베딩 후보
│
├── 📂 Schedule_Gold/               # [Input] 일정 정답 데이터
│   ├── Schedule_Gold_Base_Info_1.json
│   ├── ...
│   └── Schedule_Gold_Base_Info_30.json
│
├── 📂 Schedule_Gold_Weight/        # [Input] 일정 정답 가중치
│   ├── Schedule_Gold_Weight_Base_Info_1.json
│   ├── ...
│   └── Schedule_Gold_Weight_Base_Info_30.json
│
├── 📂 Result_Score/                # [Output] 평가 결과 및 분석 스크립트
│   ├── 📂 Result_Location_Dong_Score/  # 동(Dong) 단위 평가 결과 (Person 1~30)
│   ├── 📂 Result_Location_Gu_Score/    # 구(Gu) 단위 평가 결과 (Person 1~30)
│   ├── 📂 Result_Schedule_Score/       # 일정(Schedule) 평가 결과 (Person 1~30)
│   ├── 📂 Result_Score_All/            # 통합 결과 (Aggregated Results - Rank_all.py의 구성만큼)
│   ├── Rank_All.py                     # 전체 종합 순위 산출 스크립트
│   ├── Rank_Dong.py                    # 동 단위 순위 분석 스크립트
│   ├── Rank_Gu.py                      # 구 단위 순위 분석 스크립트
│   └── Rank_Schedule.py                # 일정 순위 분석 스크립트
│
├── 🐍 preference_scorer.py         # [Core] 개별 사용자 선호도 채점 모듈
└── 🐍 process_all_people.py        # [Main] 전체 사용자 일괄 처리 실행 스크립트