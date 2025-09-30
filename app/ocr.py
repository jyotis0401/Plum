import pytesseract
from PIL import Image, ImageFilter, ImageOps
import io
from .model import OCRResult


def _preprocess_image_bytes(image_bytes: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # basic preprocessing: grayscale, resize if too large, and sharpen
    gray = ImageOps.grayscale(image)
    w, h = gray.size
    max_dim = 1600
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        gray = gray.resize((int(w * scale), int(h * scale)))
    gray = gray.filter(ImageFilter.SHARPEN)
    return gray


def ocr_from_image(image_bytes: bytes) -> OCRResult:
    print("[OCR] Starting image processing and Tesseract call.") 
    try:
        img = _preprocess_image_bytes(image_bytes)
        # Use Tesseract to extract text
        text = pytesseract.image_to_string(img)
        # Tesseract can give word confidences with image_to_data; compute mean if available
        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confs = [int(c) for c in data.get('conf', []) if c and c != '-1']
            if confs:
                conf = sum(confs) / (100.0 * len(confs))
            else:
                conf = 0.8
        except Exception:
            conf = 0.8
        print(f"[OCR] Tesseract finished. Extracted text length: {len(text.strip())}")
        return OCRResult(raw_text=text.strip(), confidence=round(conf, 2))
    except Exception as e:
        print(f"[OCR] ERROR during Tesseract/Image processing: {e}")
        return OCRResult(raw_text="", confidence=0.0)
# from PIL import Image, ImageFilter, ImageOps, ImageEnhance
# import io
# import numpy as np
# import cv2
# from .model import OCRResult
# import pytesseract

# def _preprocess_image_bytes(image_bytes: bytes) -> Image.Image:
#     # Load with OpenCV for stronger ops
#     np_img = np.frombuffer(image_bytes, np.uint8)
#     cv_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

#     # Convert to grayscale
#     gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

#     # Increase contrast with adaptive threshold
#     # (turns red/grey into clear black/white)
#     gray = cv2.adaptiveThreshold(
#         gray, 255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         35, 15
#     )

#     # Enlarge a bit for better OCR
#     scale = 2
#     gray = cv2.resize(gray, (cv_img.shape[1]*scale, cv_img.shape[0]*scale),
#                       interpolation=cv2.INTER_CUBIC)

#     # Convert back to PIL for Tesseract
#     pil_img = Image.fromarray(gray)
#     return pil_img

# def ocr_from_image(image_bytes: bytes) -> OCRResult:
#     print("[OCR] Starting image processing and Tesseract call.")
#     try:
#         img = _preprocess_image_bytes(image_bytes)
#         text = pytesseract.image_to_string(img, lang="eng")

#         # confidence estimation
#         try:
#             data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
#             confs = [int(c) for c in data.get('conf', []) if c and c != '-1']
#             conf = sum(confs) / (100.0 * len(confs)) if confs else 0.8
#         except Exception:
#             conf = 0.8

#         print(f"[OCR] Tesseract finished. Extracted text length: {len(text.strip())}")
#         return OCRResult(raw_text=text.strip(), confidence=round(conf, 2))
#     except Exception as e:
#         print(f"[OCR] ERROR during Tesseract/Image processing: {e}")
#         return OCRResult(raw_text="", confidence=0.0)
