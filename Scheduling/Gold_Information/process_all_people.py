import json
import sys

from preference_scorer import process_person

def main():
    print("=" * 80)
    print("전체 30명에 대한 장소 및 스케줄 선호도 점수 계산")
    print("=" * 80)
    print()
    
    for person_id in range(1, 31):
        try:
            process_person(person_id)
        except Exception as e:
            print(f"❌ Person {person_id} 처리 중 오류: {e}")
            continue
    
    print()
    print("=" * 80)
    print("✅ 전체 처리 완료!")
    print("=" * 80)
    print()
    print("생성된 파일:")
    print("  - Person_{1-30}_Dong_Scores.json (30개)")
    print("  - Person_{1-30}_Gu_Scores.json (30개)")
    print("  - Person_{1-30}_Schedule_Scores.json (30개)")
    print("  총 90개 파일")

if __name__ == "__main__":
    main()
