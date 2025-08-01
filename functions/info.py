import json
import re
import os

# 추가
VALID_MATERIALS = {"울", "면", "폴리", "레이온", "실크", "합성섬유"}
VALID_SYMBOLS = {"handwash", "30degrees", "no_dryer", "no_bleach", "dryclean"}
VALID_STAINS = {"기름", "색소", "단백질", "복합", "땀/냄새", "흙/먼지", "혈흔"}


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# 1차 함수: OCR + 사용자 입력 기반 분석
def laundry_info(ocr_path: str, user_path: str) -> dict:
    user_data = load_json(user_path)
    user_input = user_data.get("tags", [])

    if os.path.exists(ocr_path):
        ocr_data = load_json(ocr_path)
        ocr_text = ocr_data.get("ocr_text", "").lower()
        symbols = ocr_data.get("symbols", [])
        ocr_words = set(re.findall(r'[가-힣a-zA-Z0-9]+', ocr_text))
    else:
        ocr_words = set()
        symbols = []

    materials = list(VALID_MATERIALS & ocr_words)
    if not materials:
        materials = [kw for kw in VALID_MATERIALS if kw in user_input]

    parsed_symbols = [s for s in symbols if s in VALID_SYMBOLS]
    if not parsed_symbols:
        parsed_symbols = [kw for kw in VALID_SYMBOLS if kw in user_input]

    stains = [kw for kw in VALID_STAINS if kw in user_input]

    return {
        "material": materials,
        "symbols": parsed_symbols,
        "stains": stains,
    }


# 2차 함수: 수정된 정보가 있다면 반영, 없으면 1차 결과 유지
def apply_user_correction(ocr_path: str, user_path: str, corrected_path: str) -> dict:


    # 1차 결과 받아옴
    original = laundry_info(ocr_path, user_path)

    # 2차 사용자 수정데이터 받아옴
    with open(corrected_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 유효한 값만 필터링
    materials = [m for m in data.get("material", []) if m in VALID_MATERIALS]
    symbols = [s for s in data.get("symbols", []) if s in VALID_SYMBOLS]
    stains = [s for s in data.get("stains", []) if s in VALID_STAINS]

    # 수정된 값이 있으면 반영, 없으면 1차 값 유지
    result = {
        "material": materials if materials else original["material"],
        "symbols": symbols if symbols else original["symbols"],
        "stains": stains if stains else original["stains"],
    }

    return result
