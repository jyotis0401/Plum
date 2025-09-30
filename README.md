**AI-Powered Appointment Scheduler Assistant**

**Problem Statement:**

Build a backend service that parses natural language or document-based appointment requests and converts them into structured scheduling data. The system should handle both typed text and noisy image inputs (e.g., scanned notes, emails). Interns must design a pipeline with OCR, entity extraction, normalization, and final structured JSON output with guardrails for ambiguity.

**Project Goal:**

This FastAPI backend service parses natural language appointment requests (e.g., "Book gynac next Tuesday at 2am") and converts them into structured scheduling data, applying normalization to ISO 8601 format and implementing confidence-based guardrails.

**Pipeline:**
**OCR/Text Extraction (ocr.py):** Extracts raw text and confidence score from image or text input.
Input (text):
Book dentist next Friday at 3pm

**Entity Extraction (entity_extraction.py)**: Uses spaCy and Regex to extract raw phrases (date_phrase, time_phrase, department).

**Normalisation (normalization.py):** Converts raw phrases to final ISO format (YYYY-MM-DD and HH:MM).

**Guardrails (guardrails.py):** Checks entity extraction and normalisation confidence. Fails if scores are too low.

**Final Output (main.py):** Canonicalises departments (e.g., 'gynac' → 'Gynaecology') and returns the final JSON structure.
Expected Output (JSON):
{
  "appointment": {
    "department": "Dentistry",
   "date": "2025-09-26",
  "time": "15:00",
  "tz": "Asia/Kolkata"
 },
 "status":"ok"
}
**RUN:**
**Docker Commands:**
**Build the Image:**
docker build -t appointment-scheduler .

**Run the Container (Exposing Port 8000):**
docker run -p 8000:8000 appointment-scheduler
              OR
**Local Setup:**
**Install System Dependencies:**
Please make sure you have Tesseract OCR installed on your system (e.g., brew install tesseract on macOS or sudo apt install tesseract-ocr on Linux).

**Activate Environment and Install Python Packages:**
source venv/bin/activate #virtual environment
pip install -r requirements.txt
python -m spacy download en_core_web_sm

**Run Server:**
uvicorn app.main:app --reload 


**API Usage Examples:**

Example 1 

  **Request**: Book gynac next day at 2am.
  
curl -X POST http://localhost:8000/parse \
  -F "input_type=text" \
  -F "text=Book gynac next day at 2am" \
  -F "locale=Asia/Kolkata"
  
  **Expected Response**: {"appointment":{"department":"Gynaecology","date":"2025-10-01","time":"02:00","tz":"Asia/Kolkata"},"status":"ok"} (date may change depending on next day)

Example 2: Guardrail Failure

  **Request**: Book eye doctor.
  
  curl -X POST http://localhost:8000/parse \
  -F "input_type=text" \
  -F "text=Book eye doctor" \
  -F "locale=Asia/Kolkata"
  
  **Expected Response**: {"status":"needs_clarification","message":"Missing critical information: Date Phrase. Please provide a date/time and department.","suggestions":null}
