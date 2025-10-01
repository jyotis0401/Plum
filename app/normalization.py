from datetime import datetime
import pytz
import dateparser
import re
from typing import Optional, Dict

# Helper function to parse simple time formats (e.g., 2am, 3pm, 10:30) without dateparser
def _parse_simple_time(time_phrase: str) -> Optional[tuple[int, int]]:
    """Converts a time phrase (e.g., '2am', '10:30pm') into (hour, minute)."""
    
    # Normalize and clean the phrase
    low = time_phrase.lower().strip().replace(" ", "")

    # Pattern: Digit(s) (optional colon and digits) (am|pm)
    m = re.match(r"(\d{1,2})(:(\d{2}))?(am|pm)", low)
    if not m:
        # Try military time/simple hour (e.g., '14:00', '14')
        try:
            dt = datetime.strptime(low, "%H:%M")
            return dt.hour, dt.minute
        except ValueError:
            try:
                dt = datetime.strptime(low, "%H")
                return dt.hour, 0
            except ValueError:
                return None

    hour_str, _, minute_str, ampm = m.groups()
    hour = int(hour_str)
    minute = int(minute_str) if minute_str else 0

    if ampm == 'pm' and hour < 12:
        hour += 12
    elif ampm == 'am' and hour == 12: # Midnight
        hour = 0
    
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    
    return None

def normalize_datetime(date_phrase: str, time_phrase: str, locale: str = "Asia/Kolkata"):
    tz = pytz.timezone(locale)
    now = datetime.now(tz)
    
    print(f"[NORM] Input Date: '{date_phrase}', Input Time: '{time_phrase}', Locale: {locale}")

    if not date_phrase and not time_phrase:
        print("[NORM] WARNING: No date or time phrase provided. Returning None.")
        return None, 0.0

    # Configuration for date parsing (Base set to midnight)
    relative_base_at_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    settings = {
        "TIMEZONE": locale,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "RELATIVE_BASE": relative_base_at_midnight,
        "PREFER_DATES_FROM": "future"
    }
    
    parsed_dt: Optional[datetime] = None
    
    # 1. --- STABILIZATION STEP 1: PARSE DATE ONLY (Receives 'tuesday') ---
    if date_phrase:
        print(f"[NORM] Attempting to parse Date Phrase: '{date_phrase}'")
        parsed_dt = dateparser.parse(date_phrase, settings=settings)
        
    # If date is not found, try combined as a last resort.
    if not parsed_dt and (date_phrase or time_phrase):
        combined_text = f"{date_phrase} {time_phrase}".strip()
        print(f"[NORM] Date parsing failed. Trying Combined Text: '{combined_text}'")
        parsed_dt = dateparser.parse(combined_text, settings=settings)

    if not parsed_dt:
        print("[NORM] FAILED: dateparser could not resolve a date.")
        return None, 0.0

    # 2. --- FIX: PARSE TIME USING CUSTOM HELPER ---
    target_hour, target_minute = 0, 0 # Default time is 00:00
    
    if time_phrase:
        print(f"[NORM] Attempting custom time parse for: '{time_phrase}'")
        time_result = _parse_simple_time(time_phrase)
        
        if time_result:
            target_hour, target_minute = time_result
            print(f"[NORM] Successfully parsed time: {target_hour:02d}:{target_minute:02d}")
        else:
            print("[NORM] WARNING: Custom time parser failed, using default time 00:00.")
    
    # 3. --- COMBINE RESULTS ---
    
    final_dt = parsed_dt.replace(
        hour=target_hour, 
        minute=target_minute, 
        second=0, 
        microsecond=0
    ).astimezone(tz)
    
    normalized = {
        "date": final_dt.strftime("%Y-%m-%d"),
        "time": final_dt.strftime("%H:%M"),
        "tz": locale
    }
    
    print(f"[NORM] SUCCESS | Final Normalized DT: {final_dt}")
    print(f"[NORM] SUCCESS | Normalized: {normalized}")

    return normalized, 0.95
