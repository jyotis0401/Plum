from .model import OCRResult, EntitiesResult, NormalizedResult, GuardrailResponse

# thresholds - tweakable
OCR_THRESHOLD = 0.5
ENTITIES_THRESHOLD = 0.7
NORMALIZATION_THRESHOLD = 0.7


def evaluate_guardrails(ocr: OCRResult, entities: EntitiesResult, normalized: NormalizedResult) -> GuardrailResponse:
    # If OCR confidence too low
    if ocr.confidence < OCR_THRESHOLD:
        return GuardrailResponse(status="needs_clarification", message="Image/text unreadable - please re-upload or type the text.")

    # If critical entities missing or low confidence
    if entities.entities_confidence < ENTITIES_THRESHOLD:
        missing = []
        for k, v in entities.entities.items():
            if not v:
                missing.append(k)
        msg = "Entities missing or ambiguous."
        if missing:
            msg = f"Missing entities: {', '.join(missing)}"
        return GuardrailResponse(status="needs_clarification", message=msg)

    # If normalization poor
    if normalized.normalization_confidence < NORMALIZATION_THRESHOLD:
        return GuardrailResponse(status="needs_clarification", message="Could not normalize date/time confidently. Please specify a clearer date or exact time.")

    # All good
    return GuardrailResponse(status="ok", message="All checks passed.")
