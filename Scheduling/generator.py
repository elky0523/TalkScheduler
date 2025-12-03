import json
from datetime import datetime, timedelta
import sys
import random

# --- 전역 상수 및 매핑 설정 ---
numbers = list(range(1, 31))
USER_IDX = sorted(random.sample(numbers, 3))
FILE_NAME_TEMPLATE = "./Schedule_Information/Schedule_Info_{i}.json"
BASE_INFO_TEMPLATE = "./Base_Information/Base_Info_{i}.json"
GENERAL_INFO_FILE = "General_Info.json"

# 2025년 12월 한국 공휴일 리스트 (성탄절)
HOLIDAY_LIST = ["2025-12-25"] 

# 요일 매핑 (영문 -> 한글)
day_map_en_to_ko = {
    "Mon": "월요일",
    "Tue": "화요일",
    "Wed": "수요일",
    "Thu": "목요일",
    "Fri": "금요일",
    "Sat": "토요일",
    "Sun": "일요일"
}

# 요일 매핑 (요일 번호 -> 한글 축약)
day_map_weekday = {0: "(월)", 1: "(화)", 2: "(수)", 3: "(목)", 4: "(금)", 5: "(토)", 6: "(일)"}

# 최소 약속 시간 (General_Info.json에서 로드될 예정)
MIN_DURATION_HOURS = 0 

# --- 데이터 로드 및 저장 함수 ---

def load_json_data(file_name):
    """지정된 JSON 파일을 로드하고 오류를 처리합니다."""
    # Note: 이 함수는 파일이 반드시 존재하고 유효한 JSON 형식임을 가정합니다.
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"오류: {file_name} 파일을 찾을 수 없습니다. 프로그램을 종료합니다.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"오류: {file_name} 파일의 JSON 형식이 올바르지 않습니다. 프로그램을 종료합니다.", file=sys.stderr)
        sys.exit(1)

def save_output_to_file(content, filename):
    """주어진 내용을 텍스트 파일로 저장합니다."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {filename} 파일에 텍스트를 저장했습니다.")
    except IOError as e:
        print(f"❌ {filename} 파일 저장 중 오류 발생: {e}", file=sys.stderr)

def save_json_output(data, filename):
    """주어진 딕셔너리 데이터를 JSON 파일로 저장합니다."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # 딕셔너리를 JSON 형식으로 저장 (들여쓰기 4칸, 아스키 코드 외 문자 허용)
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ {filename} 파일에 JSON 데이터를 저장했습니다.")
    except IOError as e:
        print(f"❌ {filename} 파일 저장 중 오류 발생: {e}", file=sys.stderr)

# --- 프롬프트 생성 함수 ---

def format_schedule(schedule, is_work=False):
    """근무 및 약속 스케줄을 텍스트로 포맷합니다."""
    schedule_parts = []
    # Mon, Tue, Wed, Thu, Fri, Sat, Sun 순서로 정렬
    sorted_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    for day in sorted_days:
        if day in schedule and schedule[day]:
            # 리스트 내의 모든 시간 범위를 처리 (예시와 일관성을 위해 첫 번째 범위만 사용)
            time_ranges = []
            for start_time, end_time in schedule[day]:
                # 시간 포맷 (예: 9.0 -> 9, 10.5 -> 10.5)
                start_str = f"{start_time:.1f}".replace(".0", "")
                end_str = f"{end_time:.1f}".replace(".0", "")
                time_ranges.append(f"{start_str}~{end_str}")
            
            time_str = ", ".join(time_ranges)
            day_ko = day_map_en_to_ko[day]
            
            if is_work:
                # 근무 스케줄: "월요일 10.5~17.5"
                schedule_parts.append(f"{day_ko} {time_str}")
            else:
                # 약속 스케줄: "월요일 18~21시"
                schedule_parts.append(f"{day_ko} {time_str}시")
                
    return ", ".join(schedule_parts)

def generate_user_data_parts(user_data, user_number):
    """단일 사용자 데이터를 기반으로 스케줄 및 위치 프롬프트 부분을 생성합니다."""
    
    # Schedule Parts
    fixed_schedule_str = format_schedule(user_data.get("fixed_schedule", {}), is_work=True)
    preferred_meeting_schedule_str = format_schedule(user_data.get("preferred_meeting_schedule", {}), is_work=False)
    
    # 근무 스케줄은 마지막에 '시입니다.'가 붙어야 하므로, format_schedule에서 '시'를 제거한 후 여기서 붙임
    schedule_part = (
        f"사용자 {user_number}은 보통 {fixed_schedule_str}시에 고정된 일정이 있습니다.\n"
        f"선호하는 약속 요일 및 시간은 {preferred_meeting_schedule_str}입니다."
    )
    
    # Location Parts
    age = user_data.get("age")
    gender_str = "남자" if user_data.get("gender") == "Male" else "여자"
    residence = user_data.get("current_residence")

    # 좌표를 '[위도, 경도]' 문자열 형식으로 변환
    # replace(' ', '')를 사용하여 띄어쓰기를 제거합니다.
    freq_visited = [str(coord).replace(' ', '') for coord in user_data.get("frequently_visited_area", [])]
    preferred = [str(coord).replace(' ', '') for coord in user_data.get("preferred_areas", [])]

    location_part = (
        f"사용자 {user_number}은 {age}세 {gender_str}로, {residence}에 거주하고 있습니다.\n"
        f"자주 방문하는 장소는 {', '.join(freq_visited)}이고, "
        f"선호하는 지역은 {', '.join(preferred)}입니다."
    )
    
    return schedule_part, location_part

def generate_prompts(user_base_data, general_data):
    """모든 사용자 정보와 일반 정보를 통합하여 최종 프롬프트 두 개를 생성합니다."""
    
    schedule_prompts = []
    location_prompts = []
    
    for i, user_number in enumerate(USER_IDX):
        user_data = user_base_data[i]
        schedule_part, location_part = generate_user_data_parts(user_data, user_number)
        
        schedule_prompts.append(schedule_part)
        location_prompts.append(location_part)
        
    start_date = general_data['start']
    end_date = general_data['end']
    duration = general_data['min_meeting_duration_hours']
    theme = general_data['Theme']
    
    # General Schedule Part
    general_schedule_part = (
        f"사용자들은 {start_date}부터 {end_date} 사이에 {theme}를 테마로 약속을 잡으려고 하고 있습니다. 약속의 예상 시간은 {duration}시간입니다."
    )
    
    # General Location Part
    general_location_part = (
        f"사용자들은 {theme}를 테마로 약속을 잡으려고 하고 있습니다. 약속의 예상 시간은 {duration}시간입니다."
    )
    
    final_schedule_prompt = "\n\n".join(schedule_prompts) + "\n\n" + general_schedule_part
    final_location_prompt = "\n\n".join(location_prompts) + "\n\n" + general_location_part
    
    return final_schedule_prompt, final_location_prompt

# --- 벡터화 함수 ---

def is_holiday(date_str: str) -> int:
    """주어진 날짜가 휴일인지 여부를 반환합니다 (1: 휴일, 0: 평일)."""
    if date_str in HOLIDAY_LIST:
        return 1
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return 0

    # 주말 (토:5, 일:6)
    if date_obj.weekday() >= 5:
        return 1
        
    return 0

def date_time_to_vector(date_str: str, hour: int) -> list:
    """
    날짜 문자열과 시간을 입력받아 10차원 특성 벡터를 반환합니다.
    (월, 화, 수, 목, 금, 토, 일, 오늘 휴일 여부, 내일 휴일 여부, 시간)
    """
    try:
        today = datetime.strptime(date_str, '%Y-%m-%d').date()
        tomorrow = today + timedelta(days=1)
    except ValueError:
        return [0] * 10

    # 1. 요일 원-핫 인코딩 (월=0, ..., 일=6)
    day_of_week_index = today.weekday()
    day_vector = [0] * 7
    day_vector[day_of_week_index] = 1

    # 2. 휴일 여부 확인
    is_today_holiday = is_holiday(date_str)
    is_tomorrow_holiday = is_holiday(tomorrow.strftime('%Y-%m-%d'))

    # 3. 최종 벡터 생성
    feature_vector = day_vector + [is_today_holiday, is_tomorrow_holiday, hour]
    
    return feature_vector

# --- 스케줄 교집합 및 Arm 벡터 생성 함수 ---

def filter_by_min_duration(slots, min_duration):
    """주어진 시간 슬롯 리스트에서 최소 지속 시간보다 짧은 슬롯을 제거합니다."""
    filtered_slots = []
    # 부동 소수점 오차 처리 (1e-6)
    MIN_DURATION_EPSILON = min_duration - 1e-6
    for start, end in slots:
        if end - start >= MIN_DURATION_EPSILON:
            filtered_slots.append([start, end])
    return filtered_slots

def find_intersection_of_two_schedules(slots_a, slots_b):
    """두 개의 시간 슬롯 리스트의 교집합을 찾습니다. (필터링은 호출자가 담당)"""
    if not slots_a or not slots_b:
        return []
        
    result = []
    i = j = 0
    
    slots_a.sort()
    slots_b.sort()

    while i < len(slots_a) and j < len(slots_b):
        start_a, end_a = slots_a[i]
        start_b, end_b = slots_b[j]
        
        # 교집합의 시작점과 끝점 계산
        intersection_start = max(start_a, start_b)
        intersection_end = min(end_a, end_b)
        
        # 교집합이 존재하면 결과에 추가
        if intersection_start < intersection_end:
            result.append([intersection_start, intersection_end])
            
        # 다음 슬롯으로 이동: 더 빨리 끝나는 슬롯의 인덱스를 증가시킴
        # 부동 소수점 비교에 주의
        if end_a <= end_b + 1e-6:
            i += 1
        if end_b <= end_a + 1e-6:
            j += 1
            
    return result

def find_all_schedules_intersection(schedules, min_duration):
    """모든 스케줄의 공통 교집합을 찾습니다."""
    
    all_dates = set()
    if not schedules:
        return {}
        
    for schedule in schedules:
        all_dates.update(schedule.keys())
        
    common_availability = {}
    sorted_dates = sorted(list(all_dates))

    for date_str in sorted_dates:
        
        current_slots_list = []
        is_available_for_all = True
        
        for schedule in schedules:
            slots = schedule.get(date_str)
            if not slots:
                is_available_for_all = False
                break
            current_slots_list.append(slots)
            
        if not is_available_for_all:
            continue

        common_slots = current_slots_list[0]
        
        for i in range(1, len(current_slots_list)):
            common_slots = find_intersection_of_two_schedules(common_slots, current_slots_list[i])
            if not common_slots:
                break

        # 최종적으로 최소 지속 시간 필터링 적용
        final_filtered_slots = filter_by_min_duration(common_slots, min_duration)
        
        if final_filtered_slots:
            common_availability[date_str] = final_filtered_slots
            
    return common_availability

def generate_schedule_arm_vector(common_slots, min_duration):
    """
    공통 가용 시간대에서 최소 지속 시간을 만족하는 모든 시작 시간을 찾아
    10차원 벡터로 변환하여 Dictionary 형식으로 반환합니다.
    """
    schedule_arm_vectors = {}
    
    # 날짜를 순서대로 처리
    sorted_dates = sorted(common_slots.keys())

    for date_str in sorted_dates:
        slots = common_slots[date_str]
        
        for start_hour, end_hour in slots:
            # 가능한 시작 시간은 '종료 시간 - 최소 지속 시간' 이하입니다. (S <= E - min_duration)
            max_start_hour = end_hour - min_duration
            
            # 시작 시간은 정수 시간 (1시간 단위)으로만 계산합니다.
            start_i = int(start_hour)
            end_i = int(max_start_hour) 
            
            # 시작 시간 (start_hour)이 0.5단위일 경우, 다음 정수 시간부터 시작합니다. (예: 10.5 -> 11시부터)
            # 1e-6은 부동 소수점 오차를 처리하기 위한 값입니다.
            if start_hour > start_i + 1e-6:
                start_i += 1

            for hour in range(start_i, end_i + 1):
                # 키 형식: YYYY-MM-DD-HH
                key = f"{date_str}-{hour:02d}"
                vector = date_time_to_vector(date_str, hour)
                schedule_arm_vectors[key] = vector
                
    return schedule_arm_vectors

def generate_formatted_common_slots_output(common_availability):
    """교집합 결과를 사용자 예시 형식으로 포맷합니다."""
    output_list = []
    
    for date_str, slots in common_availability.items():
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = day_map_weekday[d.weekday()]
            
            # 시간 포맷 (예: 9.0 -> 9, 10.5 -> 10.5)
            slot_strs = [f"[{s[0]:.1f}, {s[1]:.1f}]".replace(".0", "") for s in slots]
            time_str = ", ".join(slot_strs)
            
            formatted_date = d.strftime("%Y.%m.%d.") + day_name
            output_list.append(f"{formatted_date}: {time_str}")
        except ValueError:
            pass

    return output_list

def generate_formatted_start_time_output(common_slots, min_duration):
    """
    최종 교집합 시간대에서 최소 지속 시간 이상의 약속을 시작할 수 있는 
    모든 시작 시간을 리스트로 생성하여 사용자 예시 형식으로 포맷합니다.
    """
    start_time_list = []
    
    sorted_dates = sorted(common_slots.keys())

    for date_str in sorted_dates:
        slots = common_slots[date_str]
        
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = day_map_weekday[d.weekday()]
            formatted_date_prefix = d.strftime("%Y.%m.%d.") + day_name
        except ValueError:
            continue

        for start_hour, end_hour in slots:
            max_start_hour = end_hour - min_duration
            
            start_i = int(start_hour)
            end_i = int(max_start_hour) 
            
            # 시작 시간이 0.5단위일 경우 반올림하여 처리
            if start_hour > start_i + 1e-6:
                start_i += 1

            for hour in range(start_i, end_i + 1):
                start_time_list.append(f"{formatted_date_prefix} {hour}시")
                
    return start_time_list

# --- 메인 실행 로직 ---

def main():
    
    # 1. 모든 JSON 데이터 로드
    user_base_data = []
    for i in USER_IDX:
        file_name = BASE_INFO_TEMPLATE.format(i=i)
        user_base_data.append(load_json_data(file_name))
        
    general_data = load_json_data(GENERAL_INFO_FILE)
    
    global MIN_DURATION_HOURS
    MIN_DURATION_HOURS = general_data['min_meeting_duration_hours']

    # 2. 프롬프트 생성
    schedule_prompt, location_prompt = generate_prompts(user_base_data, general_data)

    # 3. Schedule Arm 계산을 위한 스케줄 정보 로드
    loaded_schedules = []
    for i in USER_IDX:
        file_name = FILE_NAME_TEMPLATE.format(i=i)
        # 스케줄 정보 파일은 로드 실패 시에도 진행해야 하므로 별도의 로직을 사용
        try:
            schedule = load_json_data(file_name)
            loaded_schedules.append(schedule)
        except SystemExit:
            # load_json_data에서 sys.exit(1)이 호출되면 프로그램이 종료됩니다.
            # 이 코드가 독립적으로 실행될 때는 해당 로직을 따릅니다.
            return 
    
    # 4. Schedule Arm 벡터 생성
    if len(loaded_schedules) == len(USER_IDX):
        final_common_slots = find_all_schedules_intersection(loaded_schedules, MIN_DURATION_HOURS)
        schedule_arm_vectors = generate_schedule_arm_vector(final_common_slots, MIN_DURATION_HOURS)
    else:
        print("\n⚠️ 모든 스케줄 파일을 로드하지 못하여 Schedule Arm을 생성할 수 없습니다.")
        final_common_slots = {}
        schedule_arm_vectors = {}
    
    # --- 5. 파일 저장 (사용자 요청 추가 기능) ---
    save_output_to_file(schedule_prompt, "schedule_prompt.txt")
    save_output_to_file(location_prompt, "location_prompt.txt")
    save_json_output(schedule_arm_vectors, "schedule_arm_vectors.json")

    # 6. 결과 출력 (Console)
    
    # --- Schedule prompt (Console Output) ---
    print("\n--- Schedule prompt (Console Output) ---")
    print(schedule_prompt)

    # --- Location prompt (Console Output) ---
    print("\n--- Location prompt (Console Output) ---")
    print(location_prompt)
    
    # --- 중간 결과 출력 (사용자 요청 예시 형식) ---
    formatted_common_slots = generate_formatted_common_slots_output(final_common_slots)
    formatted_start_times = generate_formatted_start_time_output(final_common_slots, MIN_DURATION_HOURS)
    
    print(f"\n--- 사용자 일정의 공통 가용 시간대 (최소 {MIN_DURATION_HOURS}시간 이상) ---")
    if formatted_common_slots:
        print("\n".join(formatted_common_slots))
    else:
        print("사용자가 모두 겹치는 가용 시간대는 없습니다.")

    print("\n--- Arm 변환 결과 (포맷된 시작 시간) ---")
    if formatted_start_times:
        print("\n".join(formatted_start_times))
    else:
        print("생성된 Schedule Arm이 없습니다.")

    # --- Schedule Arm (JSON Vector - Console Output) ---
    print("\n--- Schedule Arm (JSON Vector - Console Output) ---")
    
    # JSON 형식으로 최종 벡터 출력
    schedule_arm_json_output = json.dumps(schedule_arm_vectors, indent=4, ensure_ascii=False)
    # print(schedule_arm_json_output)


if __name__ == "__main__":
    main()