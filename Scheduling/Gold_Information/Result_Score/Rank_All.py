import json
import os
import sys
from pathlib import Path

# ==========================================
# 설정: 데이터가 위치한 폴더명 (스크립트와 같은 경로에 있다고 가정)
# ==========================================
# Path.cwd()를 사용하여 현재 스크립트 실행 위치를 기준점으로 잡습니다.
base_path = Path.cwd()
DIR_DONG = base_path / 'Result_Location_Dong_Score'
DIR_GU = base_path / 'Result_Location_Gu_Score'
DIR_SCHEDULE = base_path / 'Result_Schedule_Score'

def load_json_data(filepath):
    """JSON 파일을 안전하게 읽어오는 헬퍼 함수"""
    if not os.path.exists(filepath):
        # 파일이 없을 경우 경고 메시지 출력 후 None 반환
        print(f"[Warning] 파일을 찾을 수 없습니다: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] 파일 읽기 실패 ({filepath}): {e}")
        return None

def process_dong_ranking(person_ids):
    aggregated = {} # {(구, 동): [scores]}

    for pid in person_ids:
        filename = f"Person_{pid}_Location_Dong_Score.json"
        # pathlib 경로와 os.path.join 호환을 위해 문자열 변환 혹은 pathlib 연산 사용 가능
        # 여기서는 기존 로직 유지를 위해 os.path.join 사용
        file_path = DIR_DONG / filename
        data = load_json_data(file_path)
        
        if data:
            for entry in data:
                gu = entry.get('구')
                dong = entry.get('동')
                score = entry.get('score')
                if gu and dong and score is not None:
                    key = (gu, dong)
                    if key not in aggregated:
                        aggregated[key] = []
                    aggregated[key].append(float(score))

    # 평균 계산 및 리스트 변환
    results = []
    for (gu, dong), scores in aggregated.items():
        avg = sum(scores) / len(scores)
        results.append({"구": gu, "동": dong, "average_score": round(avg, 4)})
    
    # 정렬 (내림차순)
    results.sort(key=lambda x: x['average_score'], reverse=True)
    return results

def process_gu_ranking(person_ids):
    aggregated = {} # {구: [scores]}

    for pid in person_ids:
        filename = f"Person_{pid}_Location_Gu_Score.json"
        file_path = DIR_GU / filename
        data = load_json_data(file_path)
        
        if data:
            for entry in data:
                gu = entry.get('구')
                score = entry.get('score')
                if gu and score is not None:
                    if gu not in aggregated:
                        aggregated[gu] = []
                    aggregated[gu].append(float(score))

    # 평균 계산 및 리스트 변환
    results = []
    for gu, scores in aggregated.items():
        avg = sum(scores) / len(scores)
        results.append({"구": gu, "average_score": round(avg, 4)})
    
    # 정렬 (내림차순)
    results.sort(key=lambda x: x['average_score'], reverse=True)
    return results

def process_schedule_ranking(person_ids):
    aggregated = {} # {스케줄키: [scores]}

    for pid in person_ids:
        filename = f"Person_{pid}_Schedule_Score.json"
        file_path = DIR_SCHEDULE / filename
        data = load_json_data(file_path)
        
        if data:
            # 스케줄 파일은 Dict 형태 {"key": score}
            for key, score in data.items():
                if score is not None:
                    if key not in aggregated:
                        aggregated[key] = []
                    aggregated[key].append(float(score))

    # 평균 계산 및 리스트 변환
    results = []
    for key, scores in aggregated.items():
        avg = sum(scores) / len(scores)
        results.append({"schedule": key, "average_score": round(avg, 4)})
    
    # 정렬 (내림차순)
    results.sort(key=lambda x: x['average_score'], reverse=True)
    return results

def main():
    # 1. 입력 인자 확인
    if len(sys.argv) < 2:
        print("사용법: python rank_all.py [사람번호1] [사람번호2] ...")
        print("예시: python rank_all.py 1 2 3")
        sys.exit(1)

    person_ids = sys.argv[1:]
    id_string = ",".join(person_ids)  # "1,2,3" 형태
    
    print(f"[{id_string}]번 참여자에 대한 통합 랭킹 분석을 시작합니다...")

    # 2. 결과 저장용 폴더 구조 생성
    # 구조: Result_Score/Result_Score_All/Result_Score_1,2,3/...
    
    # 상위 폴더 지정
    output_parent_dir = base_path / "Result_Score_All"
    
    # 최종 타겟 폴더 지정
    output_target_dir = output_parent_dir / f"Result_Score_{id_string}"
    
    # mkdir(parents=True)를 사용하여 상위 폴더(Result_Score_All)가 없으면 같이 생성
    if not output_target_dir.exists():
        output_target_dir.mkdir(parents=True, exist_ok=True)
        print(f"폴더 생성 완료: {output_target_dir}")
    else:
        print(f"폴더가 이미 존재합니다: {output_target_dir}")

    # 3. 각 부문별 랭킹 계산
    rank_dong = process_dong_ranking(person_ids)
    rank_gu = process_gu_ranking(person_ids)
    rank_schedule = process_schedule_ranking(person_ids)

    # 4. JSON 파일 저장
    files_to_save = [
        (f"Rank_Dong_{id_string}.json", rank_dong),
        (f"Rank_Gu_{id_string}.json", rank_gu),
        (f"Rank_Schedule_{id_string}.json", rank_schedule)
    ]

    for filename, data in files_to_save:
        # 최종 타겟 폴더 내부에 파일 경로 지정
        filepath = output_target_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"파일 저장 완료: {filepath}")

    print("\n모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()