# import re
# from typing import Dict, Optional
# from .model import EntitiesResult
# import spacy

# # Try to load spaCy but be permissive if not present at runtime
# try:
#     nlp = spacy.load("en_core_web_sm")
# except Exception:
#     nlp = None
#     print("[ENTITY] WARNING: spaCy not loaded/available.") # Debug

# _CANONICAL_DEPARTMENTS = {
#     "dentist": "Dentistry",
#     "dental": "Dentistry",
#     "cardio": "Cardiology",
#     "cardiologist": "Cardiology",
#     "eye": "Ophthalmology",
#     "optometrist": "Ophthalmology",
# }

# TIME_RE = re.compile(r"(?P<time>\b\d{1,2}(:\d{2})?\s*(am|pm)?\b|\bnoon\b|\bmorning\b|\bevening\b)", re.I)

# # Prioritize common relative phrases for the fallback
# DATE_HINTS = [
#     r"this\s+\w+",
#     r"next\s+\w+",
#     r"today", r"tomorrow",
#     r"friday|monday|tuesday|wednesday|thursday|saturday|sunday",
#     r"\d{1,2}(st|nd|rd|th)?\s+\w+",
#     r"\w+\s+\d{1,2}(st|nd|rd|th)?"
# ]

# def _extract_department(text: str) -> Optional[str]:
#     low = text.lower()
#     for k in _CANONICAL_DEPARTMENTS.keys():
#         if k in low:
#             return k
#     return None

# def _extract_time(text: str) -> Optional[str]:
#     m = TIME_RE.search(text)
#     if m:
#         return m.group("time")
#     return None

# def _extract_date_phrase(text: str) -> Optional[str]:
#     low = text.lower()
#     for pattern in DATE_HINTS:
#         m = re.search(pattern, low)
#         if m:
#             return m.group(0)
#     return None


# def extract_entities(text: str) -> EntitiesResult:
#     print(f"[ENTITY] Starting extraction for text: '{text}'") # Debug
    
#     entities = {"date_phrase": None, "time_phrase": None, "department": None}
#     confidence = 0.5

#     if not text:
#         return EntitiesResult(entities=entities, entities_confidence=0.0)

#     # 1. Use spaCy for NER
#     if nlp:
#         doc = nlp(text)
#         for ent in doc.ents:
#             if ent.label_ in {"DATE"} and not entities["date_phrase"]:
#                 entities["date_phrase"] = ent.text
#                 print(f"[ENTITY] SpaCy found DATE: {ent.text}") # Debug
#             if ent.label_ in {"TIME"} and not entities["time_phrase"]:
#                 entities["time_phrase"] = ent.text
#                 print(f"[ENTITY] SpaCy found TIME: {ent.text}") # Debug

#     # 2. Fallback regex
#     if not entities["time_phrase"]:
#         t = _extract_time(text)
#         if t:
#             entities["time_phrase"] = t
#             print(f"[ENTITY] Regex found TIME: {t}") # Debug
    
#     if not entities["date_phrase"]:
#         d = _extract_date_phrase(text)
#         if d:
#             entities["date_phrase"] = d
#             print(f"[ENTITY] Regex found DATE: {d}") # Debug

#     # 3. Department
#     dep = _extract_department(text)
#     entities["department"] = dep
#     if dep:
#         print(f"[ENTITY] Found Department: {dep}") # Debug


#     # Heuristic confidence calculation remains the same...
#     if entities["date_phrase"]:
#         confidence += 0.2
#     if entities["time_phrase"]:
#         confidence += 0.2
#     if entities["department"]:
#         confidence += 0.1

#     print(f"[ENTITY] Final Entities: {entities} | Conf: {confidence}") # Debug
#     return EntitiesResult(entities=entities, entities_confidence=round(min(confidence, 0.99), 2))
import re
from typing import Dict, Optional
from .model import EntitiesResult
import spacy

# Try to load spaCy but be permissive if not present at runtime
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None
    print("[ENTITY] WARNING: spaCy not loaded/available.") 

_CANONICAL_DEPARTMENTS = {
    "dentist": "Dentistry",
    "dental": "Dentistry",
    "cardio": "Cardiology",
    "cardiologist": "Cardiology",
    "eye": "Ophthalmology",
    "general": "General Medicine",
    "gynac": "Gynaecology",
    "gynaecologist": "Gynaecology",
    "optometrist": "Ophthalmology",
}
_RAW_DEPARTMENT_TRIGGERS = re.compile(
    r"(?:book|for|to see)\s+(a\s+)?(?P<raw_dep>\w+)\b", 
    re.I
)

TIME_RE = re.compile(r"(?P<time>\b\d{1,2}(:\d{2})?\s*(am|pm)?\b|\bnoon\b|\bmorning\b|\bevening\b)", re.I)
DATE_HINTS = [
    r"this\s+\w+",
    r"next\s+\w+",
    r"today", r"tomorrow",
    r"friday|monday|tuesday|wednesday|thursday|saturday|sunday",
    r"\d{1,2}(st|nd|rd|th)?\s+\w+",
    r"\w+\s+\d{1,2}(st|nd|rd|th)?"
]

def _extract_department(text: str) -> Optional[str]:
    low = text.lower()
    
    # 1. Check for CANONICAL keywords first (e.g., 'dentist', 'gynac')
    for k in _CANONICAL_DEPARTMENTS.keys():
        if k in low:
            return k # Returns 'dentist' or 'gynac'
    
    # 2. If no canonical keyword found, attempt to extract the RAW word
    m = _RAW_DEPARTMENT_TRIGGERS.search(low)
    if m:
        raw_dep = m.group("raw_dep")
        # Simple check to avoid capturing generic, non-department words
        if raw_dep not in {"the", "an", "appointment", "time", "date", "dr"}:
            return raw_dep.strip() # Returns 'pediatrician' or 'surgery'

    return None

def _extract_time(text: str) -> Optional[str]:
    m = TIME_RE.search(text)
    if m:
        return m.group("time")
    return None

def _extract_date_phrase(text: str) -> Optional[str]:
    low = text.lower()
    for pattern in DATE_HINTS:
        m = re.search(pattern, low)
        if m:
            return m.group(0)
    return None

# Function to clean date phrases to stabilize dateparser
def _clean_date_phrase(phrase: Optional[str]) -> Optional[str]:
    if not phrase:
        return None
    
    # Normalize internal and external whitespace
    low_phrase = " ".join(phrase.lower().split()) 
    
    # FIX 1: Convert 'next day' to 'tomorrow' 
    if 'next day' == low_phrase:
        return 'tomorrow'

    # FIX 2 (CRITICAL for stability): Convert 'next [weekday]' to '[weekday]'
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    for day in weekdays:
        if low_phrase == f"next {day}": 
            print(f"[ENTITY-CLEAN] Converting 'next {day}' to '{day}' for stability.")
            return day
    
    return phrase

def extract_entities(text: str) -> EntitiesResult:
    print(f"[ENTITY] Starting extraction for text: '{text}'") 
    
    entities = {"date_phrase": None, "time_phrase": None, "department": None}
    confidence = 0.5

    if not text:
        return EntitiesResult(entities=entities, entities_confidence=0.0)

    # 1. Use spaCy for NER
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in {"DATE"} and not entities["date_phrase"]:
                entities["date_phrase"] = ent.text
                print(f"[ENTITY] SpaCy found DATE: {ent.text}") 
            if ent.label_ in {"TIME"} and not entities["time_phrase"]:
                entities["time_phrase"] = ent.text
                print(f"[ENTITY] SpaCy found TIME: {ent.text}") 

    # 2. Fallback regex
    if not entities["time_phrase"]:
        t = _extract_time(text)
        if t:
            entities["time_phrase"] = t
            print(f"[ENTITY] Regex found TIME: {t}") 
    
    if not entities["date_phrase"]:
        d = _extract_date_phrase(text)
        if d:
            entities["date_phrase"] = d
            print(f"[ENTITY] Regex found DATE: {d}") 

    # 3. Department
    dep = _extract_department(text)
    entities["department"] = dep
    if dep:
        print(f"[ENTITY] Found Department: {dep}") 
    
    # --- APPLY CLEANING FIX HERE ---
    original_date_phrase = entities["date_phrase"]
    entities["date_phrase"] = _clean_date_phrase(entities["date_phrase"])
    if entities["date_phrase"] != original_date_phrase:
         pass 

    # Heuristic confidence calculation remains the same...
    if entities["date_phrase"]:
        confidence += 0.2
    if entities["time_phrase"]:
        confidence += 0.2
    if entities["department"]:
        confidence += 0.1

    print(f"[ENTITY] Final Entities: {entities} | Conf: {confidence}")
    return EntitiesResult(entities=entities, entities_confidence=round(min(confidence, 0.99), 2))