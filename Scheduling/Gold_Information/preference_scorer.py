import json
import numpy as np
from pathlib import Path
import datetime

# ==========================================
# 1. 파일 경로 설정 (폴더 구조 반영)
# ==========================================
base_path = Path.cwd()

# 입력 데이터 경로 (Scheduling/Gold_Information 구조 반영)
gold_info_root = base_path / "Scheduling" / "Gold_Information"

location_gold_path = base_path / "Location_Gold"
location_gold_weight_path = base_path / "Location_Gold_Weight"
schedule_gold_path = base_path / "Schedule_Gold"
schedule_gold_weight_path = base_path / "Schedule_Gold_Weight"

# Context 및 Arm Vector 경로
dong_context_path = base_path / "Location_Arm" / "location_context_dong.json"
gu_context_path = base_path / "Location_Arm" / "location_context_gu.json"
schedule_arm_vectors_path = base_path / "Schedule_Arm" / "schedule_arm_vectors.json"

# [수정됨] 기본 출력 루트 경로
output_base_path = base_path / "Result_Score"


class PreferenceScorer:
    """사용자 선호도 기반 장소 및 스케줄 점수 계산"""
    
    def __init__(self, person_id):
        self.person_id = person_id
        self.location_gold = None
        self.location_weight = None
        self.schedule_gold = None
        self.schedule_weight = None
        
        self._load_person_data()
        
    def _load_person_data(self):
        """사용자의 4가지 JSON 파일 로드"""
        try:
            with open(location_gold_path / f"Location_Gold_Base_Info_{self.person_id}.json", 'r', encoding='utf-8') as f:
                self.location_gold = json.load(f)
            
            with open(location_gold_weight_path / f"Location_Gold_Weight_Base_Info_{self.person_id}.json", 'r', encoding='utf-8') as f:
                self.location_weight = json.load(f)
            
            with open(schedule_gold_path / f"Schedule_Gold_Base_Info_{self.person_id}.json", 'r', encoding='utf-8') as f:
                self.schedule_gold = json.load(f)
            
            with open(schedule_gold_weight_path / f"Schedule_Gold_Weight_Base_Info_{self.person_id}.json", 'r', encoding='utf-8') as f:
                self.schedule_weight = json.load(f)
        except FileNotFoundError as e:
            print(f"❌ 파일 로드 실패: {e}")
            raise

    def _calculate_location_similarity(self, location_context):
        """위치 유사도 계산"""
        features = ['X', 'Y', 'age_score', 'population_score', 'cost_score', 
                   'subway_score', 'bus_score', 'car_score', 'store_score']
        
        gold_vector = np.array([self.location_gold.get(f, 0) for f in features])
        context_vector = np.array([location_context.get(f, 0) for f in features])
        
        similarities = []
        for i, feature in enumerate(features):
            if feature in ['X', 'Y']:
                max_distance = 0.3
                distance = abs(gold_vector[i] - context_vector[i])
                similarity = max(0, 1 - (distance / max_distance))
            else:
                difference = abs(gold_vector[i] - context_vector[i])
                similarity = max(0, 1 - difference)
            
            similarities.append(similarity)
        
        weight_keys = ['w_X', 'w_Y', 'w_age_score', 'w_population_score', 
                      'w_cost_score', 'w_subway_score', 'w_bus_score', 
                      'w_car_score', 'w_store_score']
        
        weights = np.array([self.location_weight.get(w, 0) for w in weight_keys])
        weighted_score = np.dot(similarities, weights)
        return round(float(weighted_score), 4)
    
    def calculate_dong_scores(self):
        """동 선호도 점수 계산"""
        with open(dong_context_path, 'r', encoding='utf-8') as f:
            dong_contexts = json.load(f)
        
        results = []
        for dong in dong_contexts:
            score = self._calculate_location_similarity(dong)
            results.append({
                "구": dong.get("구", ""),
                "동": dong.get("동", ""),
                "score": score
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def calculate_gu_scores(self):
        """구 선호도 점수 계산"""
        with open(gu_context_path, 'r', encoding='utf-8') as f:
            gu_contexts = json.load(f)
        
        results = []
        for gu in gu_contexts:
            score = self._calculate_location_similarity(gu)
            results.append({
                "구": gu.get("구", ""),
                "score": score
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def _parse_schedule_arm(self, arm_key):
        """스케줄 키 파싱"""
        parts = arm_key.split('-')
        year, month, day, hour = map(int, parts)
        date_obj = datetime.date(year, month, day)
        weekday = date_obj.weekday()
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return {
            'year': year, 'month': month, 'day': day, 'hour': hour,
            'weekday': weekday, 'weekday_name': weekday_names[weekday]
        }
    
    def _calculate_schedule_similarity(self, schedule_vector, parsed_date):
        """스케줄 유사도 계산"""
        weekday_idx = parsed_date['weekday']
        weekday_name = parsed_date['weekday_name']
        
        gold_vals = {
            'weekday': self.schedule_gold.get(weekday_name, 0),
            'today_off': self.schedule_gold.get('Today_Dayoff', 0),
            'tmr_off': self.schedule_gold.get('Tomorrow_Dayoff', 0),
            'time': self.schedule_gold.get('Time', 0)
        }
        
        arm_vals = {
            'weekday': schedule_vector[weekday_idx],
            'today_off': schedule_vector[7],
            'tmr_off': schedule_vector[8],
            'time': schedule_vector[9]
        }
        
        similarities = []
        similarities.append(gold_vals['weekday'] if arm_vals['weekday'] == 1 else 0.0)
        similarities.append(gold_vals['today_off'] if arm_vals['today_off'] == 1 else 0.0)
        similarities.append(gold_vals['tmr_off'] if arm_vals['tmr_off'] == 1 else 0.0)
        time_diff = abs(gold_vals['time'] - arm_vals['time'])
        similarities.append(max(0, 1 - (time_diff / 12)))
        
        weights = [
            self.schedule_weight.get(f'w_{weekday_name}', 0),
            self.schedule_weight.get('w_Today_Dayoff', 0),
            self.schedule_weight.get('w_Tomorrow_Dayoff', 0),
            self.schedule_weight.get('w_Time', 0)
        ]
        
        weighted_score = np.dot(similarities, weights)
        return round(float(weighted_score), 4)
    
    def calculate_schedule_scores(self):
        """스케줄 점수 계산"""
        with open(schedule_arm_vectors_path, 'r', encoding='utf-8') as f:
            schedule_arms = json.load(f)
        
        results = {}
        for arm_key, arm_vector in schedule_arms.items():
            parsed_date = self._parse_schedule_arm(arm_key)
            score = self._calculate_schedule_similarity(arm_vector, parsed_date)
            results[f"score_{arm_key}"] = score
        
        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))


def process_person(person_id, output_root=output_base_path):
    """
    특정 사람에 대한 모든 점수 계산 및 
    요청된 폴더 구조에 맞춰 파일 저장
    """
    print(f"Processing Person {person_id}...")
    
    # 1. 하위 폴더 경로 정의
    gu_dir = output_root / "Result_Location_Gu_Score"
    dong_dir = output_root / "Result_Location_Dong_Score"
    sch_dir = output_root / "Result_Schedule_Score"
    
    # 2. 폴더 생성 (없으면 자동 생성)
    for d in [gu_dir, dong_dir, sch_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    scorer = PreferenceScorer(person_id)
    
    # 3. 동 점수 계산 및 저장
    # 파일명: Person_{id}_Location_Dong_Score.json
    dong_scores = scorer.calculate_dong_scores()
    dong_file = dong_dir / f"Person_{person_id}_Location_Dong_Score.json"
    
    with open(dong_file, 'w', encoding='utf-8') as f:
        json.dump(dong_scores, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 동 점수 저장: {dong_file.name}")
    
    # 4. 구 점수 계산 및 저장
    # 파일명: Person_{id}_Location_Gu_Score.json
    gu_scores = scorer.calculate_gu_scores()
    gu_file = gu_dir / f"Person_{person_id}_Location_Gu_Score.json"
    
    with open(gu_file, 'w', encoding='utf-8') as f:
        json.dump(gu_scores, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 구 점수 저장: {gu_file.name}")
    
    # 5. 스케줄 점수 계산 및 저장
    # 파일명: Person_{id}_Schedule_Score.json
    schedule_scores = scorer.calculate_schedule_scores()
    sch_file = sch_dir / f"Person_{person_id}_Schedule_Score.json"
    
    with open(sch_file, 'w', encoding='utf-8') as f:
        json.dump(schedule_scores, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 스케줄 점수 저장: {sch_file.name}")
    print()


if __name__ == "__main__":
    print("=" * 80)
    print("사용자 선호도 기반 장소 및 스케줄 점수 계산 시스템")
    print(f"출력 경로: {output_base_path}")
    print("=" * 80)
    print()
    
    # 예시: 1번 사람만 처리
    process_person(1)
    
    print("✅ 완료!")