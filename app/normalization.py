# from datetime import datetime
# import pytz
# import dateparser

# def normalize_datetime(date_phrase: str, time_phrase: str, locale: str = "Asia/Kolkata"):
#     tz = pytz.timezone(locale)
    
#     print(f"[NORM] Input Date: '{date_phrase}', Input Time: '{time_phrase}', Locale: {locale}") # Debug

#     if not date_phrase and not time_phrase:
#         print("[NORM] WARNING: No date or time phrase provided. Returning None.") # Debug
#         return None, 0.0

#     # 1. Combine the extracted date and time phrases
#     combined_text = ""
#     if date_phrase:
#         combined_text += date_phrase
#     if time_phrase:
#         combined_text += " " + time_phrase
    
#     combined_text = combined_text.strip()
    
#     if not combined_text:
#         print("[NORM] WARNING: Combined text is empty. Returning None.") # Debug
#         return None, 0.0

#     print(f"[NORM] Combined Text for dateparser: '{combined_text}'") # Debug
    
#     # 2. Use dateparser with robust settings
#     dt = dateparser.parse(combined_text, settings={
#         "TIMEZONE": locale,
#         "RETURN_AS_TIMEZONE_AWARE": True,
#         "RELATIVE_BASE": datetime.now(tz),
#         "PREFER_DATES_FROM": "future"
#     })

#     if not dt:
#         print("[NORM] FAILED: dateparser returned None.") # Debug
#         return None, 0.0

#     # 3. Ensure localization and formatting
#     dt = dt.astimezone(tz)
    
#     normalized = {
#         "date": dt.strftime("%Y-%m-%d"),
#         "time": dt.strftime("%H:%M"),
#         "tz": locale
#     }
    
#     print(f"[NORM] SUCCESS | Normalized: {normalized}") # Debug

#     # High confidence if dateparser succeeded.
#     return normalized, 0.95
# Updated normalization.py
# from datetime import datetime
# import pytz
# import dateparser
# from typing import Optional, Dict

# def normalize_datetime(date_phrase: str, time_phrase: str, locale: str = "Asia/Kolkata"):
#     tz = pytz.timezone(locale)
#     now = datetime.now(tz)
    
#     # --- DEBUGGING START ---
#     print(f"[NORM] Input Date: '{date_phrase}', Input Time: '{time_phrase}', Locale: {locale}")
#     # --- DEBUGGING END ---

#     if not date_phrase and not time_phrase:
#         print("[NORM] WARNING: No date or time phrase provided. Returning None.")
#         return None, 0.0

#     # 1. Configuration for robust parsing
#     # Use midnight as RELATIVE_BASE to ensure 'next/this' refers to the date, not the current hour.
#     relative_base_at_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
#     settings = {
#         "TIMEZONE": locale,
#         "RETURN_AS_TIMEZONE_AWARE": True,
#         "RELATIVE_BASE": relative_base_at_midnight,
#         "PREFER_DATES_FROM": "future"
#     }
    
#     parsed_dt: Optional[datetime] = None
    
#     # 2. Parse the DATE phrase first (e.g., "this wednesday" or now "tomorrow")
#     if date_phrase:
#         print(f"[NORM] Attempting to parse Date Phrase: '{date_phrase}'")
#         parsed_dt = dateparser.parse(date_phrase, settings=settings)
        
#     # If date parsing failed, try combining both as a last resort (or if only time was provided)
#     if not parsed_dt and (date_phrase or time_phrase):
#         combined_text = f"{date_phrase} {time_phrase}".strip()
#         print(f"[NORM] Date parsing failed. Trying Combined Text: '{combined_text}'")
#         parsed_dt = dateparser.parse(combined_text, settings=settings)

#     if not parsed_dt:
#         print("[NORM] FAILED: dateparser could not parse date/combined phrase.")
#         return None, 0.0

#     # 3. Parse the TIME phrase separately and apply it to the parsed date
#     if time_phrase:
#         print(f"[NORM] Attempting to parse Time Phrase: '{time_phrase}'")
#         # Parse time relative to the current day's date
#         time_settings = settings.copy()
#         # Set the relative base for time parsing to the parsed date's time
#         time_settings['RELATIVE_BASE'] = parsed_dt.replace(hour=now.hour, minute=now.minute) 
        
#         parsed_time_dt = dateparser.parse(time_phrase, settings=time_settings)
        
#         if parsed_time_dt:
#             # Transfer the hour and minute from the parsed time onto the final date
#             parsed_dt = parsed_dt.replace(
#                 hour=parsed_time_dt.hour, 
#                 minute=parsed_time_dt.minute, 
#                 second=0, 
#                 microsecond=0
#             )
#             print(f"[NORM] Successfully merged time: {parsed_time_dt.strftime('%H:%M')}")
#         else:
#             print("[NORM] WARNING: Could not parse time phrase, defaulting to midnight or dateparser's default time.")
    
#     # 4. Final Localization and Formatting
#     parsed_dt = parsed_dt.astimezone(tz)
    
#     normalized = {
#         "date": parsed_dt.strftime("%Y-%m-%d"),
#         "time": parsed_dt.strftime("%H:%M"),
#         "tz": locale
#     }
    
#     print(f"[NORM] SUCCESS | Normalized: {normalized}")

#     # Return high confidence upon successful normalization
#     return normalized, 0.95

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