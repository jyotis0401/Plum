from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

# Using the corrected imports from the previous step
from app.model import (
    OCRResult, EntitiesResult, NormalizedResult, FinalAppointment, GuardrailResponse
)
from app.ocr import ocr_from_image
from app.entity_extraction import extract_entities
from app.normalization import normalize_datetime
from app.guardrails import evaluate_guardrails

# Imports for CORS middleware (assuming it's still needed, keeping it minimal for debug)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Appointment Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Department canonicalization map
_CANONICAL_DEPARTMENTS = {
    "dentist": "Dentistry",
    "dental": "Dentistry",
    "cardio": "Cardiology",
    "cardiologist": "Cardiology",
    "eye": "Ophthalmology",
    "optometrist": "Ophthalmology",
    "general": "General Medicine",
    "gynac": "Gynaecology",
    "gynaecologist": "Gynaecology",
}


@app.post("/parse", response_model=Optional[FinalAppointment])
async def parse(
    input_type: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    locale: str = Form("Asia/Kolkata")
):
    print("\n--- [MAIN] STARTING PARSE REQUEST ---")
    print(f"[MAIN] Input Type: {input_type}, Locale: {locale}")

    # ---------------------------
    # Step 1: OCR / Text extraction
    # ---------------------------
    if input_type == "text":
        if not text:
            raise HTTPException(status_code=400, detail="text is required when input_type=text")
        ocr_res = OCRResult(raw_text=text.strip(), confidence=0.99)
    else:
        if not file:
            raise HTTPException(status_code=400, detail="file is required when input_type=image")
        content = await file.read()
        ocr_res = ocr_from_image(content)

    print(f"[MAIN] Step 1 (OCR) | Raw Text: '{ocr_res.raw_text}' | Conf: {ocr_res.confidence}")

    # ---------------------------
    # Step 2: Entity extraction
    # ---------------------------
    entities_res = extract_entities(ocr_res.raw_text)

    print(f"[MAIN] Step 2 (Entities) | Entities: {entities_res.entities} | Conf: {entities_res.entities_confidence}")

    # ---------------------------
    # Step 3: Normalization
    # ---------------------------
    date_phrase = entities_res.entities.get("date_phrase", "")
    time_phrase = entities_res.entities.get("time_phrase", "")
    
    normalized_dict, norm_confidence = normalize_datetime(
        date_phrase=date_phrase,
        time_phrase=time_phrase,
        locale=locale
    )

    print(f"[MAIN] Step 3 (Normalization) | Normalized Dict: {normalized_dict} | Conf: {norm_confidence}")
    
    # If normalization fails, trigger guardrail
    if not normalized_dict:
        print("[MAIN] GUARDRAIL TRIGGERED: Normalization Failed (Returns None)")
        guardrail = GuardrailResponse(
            status="needs_clarification",
            message="Could not normalize date/time confidently. Please specify a clearer date or exact time.",
            suggestions=None
        )
        return JSONResponse(status_code=200, content=guardrail.dict())

    normalized_res = NormalizedResult(
        normalized=normalized_dict,
        normalization_confidence=norm_confidence
    )

    # ---------------------------
    # Step 4: Guardrails / Decision
    # ---------------------------
    guardrail = evaluate_guardrails(ocr_res, entities_res, normalized_res)
    
    print(f"[MAIN] Step 4 (Guardrails) | Status: {guardrail.status} | Message: {guardrail.message}")

    if guardrail.status == "needs_clarification":
        print("[MAIN] GUARDRAIL TRIGGERED: Low Confidence/Missing Info")
        return JSONResponse(status_code=200, content=guardrail.dict())

    # ---------------------------
    # Step 5: Final Appointment
    # ---------------------------
    raw_department = entities_res.entities.get("department", "")
    # canonical_department = _CANONICAL_DEPARTMENTS.get(raw_department.lower(), raw_department)
    department_key = raw_department if raw_department is not None else ""
    canonical_department = _CANONICAL_DEPARTMENTS.get(
        department_key.lower(), 
        department_key
    )
    appointment = {
        "department": canonical_department,
        "date": normalized_res.normalized.get("date"),
        "time": normalized_res.normalized.get("time"),
        "tz": normalized_res.normalized.get("tz"),
    }

    final = FinalAppointment(appointment=appointment, status="ok")
    
    print(f"[MAIN] SUCCESS | Final Appointment: {final.appointment}")
    return final


# Healthcheck
@app.get("/health")
async def health():
    return {"status": "ok"}