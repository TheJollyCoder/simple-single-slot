import re
import cv2
import numpy as np
import pytesseract
from utils.logger import get_logger

log = get_logger("ocr_helpers")

def normalize_stat_text(text: str) -> str:
    txt = text.strip().replace("l","1").replace("|","1").replace("I","1").replace("i","1")
    return re.sub(r"(?<=\d)[lI|i]", "1", txt)

def baseline_up(img: np.ndarray) -> np.ndarray:
    h,w = img.shape[:2]
    up = cv2.resize(img, (w*3, h*3), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)

def enhance_and_ocr(image: np.ndarray, runs: int = 3) -> list[str]:
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    results = []
    for _ in range(runs):
        up    = cv2.resize(image, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        gray  = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        sharp = cv2.filter2D(gray, -1, kernel)
        _, otsu = cv2.threshold(sharp,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(otsu,255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                         cv2.THRESH_BINARY,11,2)
        try:
            raw = pytesseract.image_to_string(adaptive,
                config="--psm 7 -c tessedit_char_whitelist=0123456789()l|"
            ).strip()
            results.append(normalize_stat_text(raw))
        except Exception:
            log.error("OCR fallback error", exc_info=True)
    return results
