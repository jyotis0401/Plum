from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class OCRResult(BaseModel):
    raw_text: str
    confidence: float


class EntitiesResult(BaseModel):
    entities: Dict[str, Optional[str]]
    entities_confidence: float


class NormalizedResult(BaseModel):
    normalized: Dict[str, Optional[str]]
    normalization_confidence: float


class FinalAppointment(BaseModel):
    appointment: Dict[str, Optional[str]]
    status: str


class GuardrailResponse(BaseModel):
    status: str
    message: str
    suggestions: Optional[List[str]] = None


class ParseRequest(BaseModel):
    input_type: str
    text: Optional[str] = None
    locale: Optional[str] = "Asia/Kolkata"
