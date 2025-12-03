# embedding/text_encoder.py

def format_time(hour):
    """Convert decimal hour (e.g., 10.5) to '10:30' style string."""
    hours = int(hour)
    minutes = int((hour - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"


def profile_to_text(profile_data):
    """
    Convert user JSON profile into a natural-language text description.
    Used by both learn mode and inference mode.
    """
    # --- CASE 1: Raw text input (test stage) ---
    if isinstance(profile_data, str):
        return profile_data.strip()
    
    # --- CASE 2: Must be dict(JSON) ---
    if not isinstance(profile_data, dict):
        raise ValueError(
            f"profile_to_text: Expected dict or str, but got {type(profile_data)}"
        )
    text_parts = []
    
    text_parts.append(f"Profile: {profile_data.get('profile_name', 'Unknown')}")

    if 'current_residence' in profile_data:
        lat, lon = profile_data['current_residence']
        text_parts.append(f"Current residence: latitude {lat:.3f}, longitude {lon:.3f}")

    if 'frequently_visited_area' in profile_data:
        areas = profile_data['frequently_visited_area']
        text_parts.append(f"Frequently visits {len(areas)} areas:")
        for i, area in enumerate(areas, 1):
            lat, lon = area
            text_parts.append(f"  Area {i}: ({lat:.3f}, {lon:.3f})")

    if 'preferred_areas' in profile_data:
        areas = profile_data['preferred_areas']
        text_parts.append(f"Preferred areas for meetings ({len(areas)} locations):")
        for i, area in enumerate(areas, 1):
            lat, lon = area
            text_parts.append(f"  Preferred {i}: ({lat:.3f}, {lon:.3f})")

    if 'work_schedule' in profile_data:
        text_parts.append("Work schedule:")
        for day, times in profile_data['work_schedule'].items():
            for time_range in times:
                start = format_time(time_range[0])
                end = format_time(time_range[1])
                text_parts.append(f"  {day}: {start} - {end}")

    if 'preferred_meeting_schedule' in profile_data:
        text_parts.append("Preferred meeting times:")
        for day, times in profile_data['preferred_meeting_schedule'].items():
            for time_range in times:
                start = format_time(time_range[0])
                end = format_time(time_range[1])
                text_parts.append(f"  {day}: {start} - {end}")

    return "\n".join(text_parts)
