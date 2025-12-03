import json
import os
import sys

def calculate_gu_ranking(person_ids):
    # 경로 설정
    data_dir = 'Result_Location_Gu_Score'
    
    # 데이터를 모을 딕셔너리: {구: [점수 리스트]}
    aggregated_scores = {}

    for pid in person_ids:
        filename = f"Person_{pid}_Location_Gu_Score.json"
        filepath = os.path.join(data_dir, filename)

        if not os.path.exists(filepath):
            print(f"Warning: 파일 '{filename}'을 찾을 수 없습니다. 건너뜁니다.")
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for entry in data:
                    gu = entry.get('구')
                    score = entry.get('score')
                    
                    if gu and score is not None:
                        if gu not in aggregated_scores:
                            aggregated_scores[gu] = []
                        aggregated_scores[gu].append(float(score))
                        
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # 평균 계산
    ranking_list = []
    for gu, scores in aggregated_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            ranking_list.append({
                "구": gu,
                "average_score": round(avg_score, 4)
            })

    # 점수 기준 내림차순 정렬
    ranking_list.sort(key=lambda x: x['average_score'], reverse=True)

    return ranking_list

if __name__ == "__main__":
    # 입력 예시: python rank_gu.py 1 4 32 34
    if len(sys.argv) < 2:
        print("사용법: python rank_gu.py [사람번호1] [사람번호2] ...")
        sys.exit(1)

    input_ids = sys.argv[1:]
    result = calculate_gu_ranking(input_ids)

    # 결과 출력
    print(json.dumps(result, indent=2, ensure_ascii=False))