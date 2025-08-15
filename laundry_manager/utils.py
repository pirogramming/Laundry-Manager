import os
import uuid
import time
import json
import re
import requests
from decouple import config
from django.conf import settings
from typing import List

# ======================
# 세탁 기호 정의 로드
# ======================
def load_washing_definitions():
    default_path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'washing_symbol.json')
    env_path = config("WASHING_SYMBOL_PATH", default="")  # .env 우선, 실패 시 폴백

    candidates = []
    if env_path:
        candidates.append(env_path)
        if not os.path.isabs(env_path):
            candidates.append(os.path.join(settings.BASE_DIR, env_path))
    candidates.append(default_path)

    for p in candidates:
        try:
            if p and os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    print(f"세탁 기호 정의 로드: {p}")
                    return json.load(f)
        except Exception as e:
            print(f"세탁 기호 정의 로드 오류({p}): {e}")

    print("세탁 기호 정의 파일을 찾지 못했습니다. 빈 정의로 계속합니다.")
    return {}

# ======================
# 세탁 기호 → 가이드 변환
# ======================
def symbols_to_guides(labels, definitions):
    guides = []

    if isinstance(definitions, dict):
        for lab in labels or []:
            meta = definitions.get(lab, {})
            name = meta.get("name") or lab
            desc = meta.get("description") or ""
            guides.append({"label": lab, "name": name, "description": desc})

    elif isinstance(definitions, list):
        by_label = {}
        for item in definitions or []:
            key = item.get("label") or item.get("id")
            if key:
                by_label[key] = item

        for lab in labels or []:
            meta = by_label.get(lab, {})
            name = meta.get("name") or lab
            desc = meta.get("description") or ""
            guides.append({"label": lab, "name": name, "description": desc})

    else:
        for lab in labels or []:
            guides.append({"label": lab, "name": lab, "description": ""})

    return guides

# ======================
# OCR 수행
# ======================
def perform_ocr(image_path):
    secret_key = os.getenv("SECRET_KEY_OCR")
    apigw_url = config("APIGW_URL")
    ext = os.path.splitext(image_path)[1][1:].lower()

    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        req_data = {
            'images': [{'format': ext, 'name': os.path.basename(image_path)}],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        headers = {'X-OCR-SECRET': secret_key}
        files = [('file', image_bytes)]
        payload = {'message': json.dumps(req_data).encode('UTF-8')}

        res = requests.post(apigw_url, headers=headers, data=payload, files=files)
        res.raise_for_status()
        return res.json()

    except Exception as e:
        return {"error": True, "message": f"OCR 오류: {e}"}

# ======================
# OCR 결과 → 기호 정의 매칭
# ======================
def get_washing_symbol_definition(ocr_result, definitions):
    full_text = ""
    extracted = []

    fields = ocr_result.get('images', [{}])[0].get('fields', [])
    for field in fields:
        text = field.get('inferText', '')
        full_text += text + " "
        extracted.append(text)

    if not full_text:
        return "텍스트 인식 실패", extracted

    lower_text = full_text.lower()

    for definition in definitions:
        for keyword in definition.get("keywords", []):
            key_lower = keyword.lower()
            if re.match(r'^\d+\s?°?C$', key_lower):
                if re.search(r'(\d+)\s?°?C', lower_text):
                    return definition["description"], extracted
            elif key_lower in lower_text:
                return definition["description"], extracted

    return "인식된 기호 설명 없음", extracted

# ======================
# Roboflow 분류
# ======================
def classify_laundry_symbol(image_path):
    try:
        api_key = config("ROBOFLOW_API_KEY")
        url = f"https://classify.roboflow.com/laundry-symbols-o1ui8/3?api_key={api_key}"
        with open(image_path, "rb") as f:
            res = requests.post(url, files={"file": f})
        result = res.json()
        pred = result["predictions"][0]
        return pred["class"], pred["confidence"]
    except Exception:
        return "분류 실패", 0

# ======================
# 결과 저장 - 분류 JSON
# ======================
def save_classification_result_json(image_path, classification_result):
    folder = config("OUTPUT_RESULTS_FOLDER", default="output/")
    os.makedirs(folder, exist_ok=True)

    output_data = {
        "filename": os.path.basename(image_path),
        "classification_result": {
            "prediction": classification_result[0],
            "confidence": classification_result[1]
        }
    }

    filename = os.path.join(folder, f"{os.path.splitext(os.path.basename(image_path))[0]}_classify.json")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"분류 결과 저장 완료: {filename}")
    except Exception as e:
        print(f"분류 결과 저장 오류: {e}")

# ======================
# 결과 저장 - OCR + 분류 JSON
# ======================
def save_result_json(image_path, texts, definition, ocr_raw,
                     rf_detect_raw=None, rf_class_raw=None, fused_scores=None):
    folder = config("OUTPUT_RESULTS_FOLDER", default="output/")
    os.makedirs(folder, exist_ok=True)

    output_data = {
        "filename": os.path.basename(image_path),
        "recognized_texts": texts,
        "symbol_definition": definition,
        "ocr_raw_response": ocr_raw,
        "roboflow_detect_raw": rf_detect_raw,
        "roboflow_classify_raw": rf_class_raw,
        "fused_scores": fused_scores,
    }

    filename = os.path.join(
        folder, f"{os.path.splitext(os.path.basename(image_path))[0]}_result.json"
    )
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"결과 저장 완료: {filename}")
    except Exception as e:
        print(f"결과 저장 오류: {e}")

# ======================
# CLOVA 요약 유틸
# ======================
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.!?]|다|요)\s+(?=[A-Z가-힣0-9])")

def _collapse_to_one_sentence(text: str, max_chars: int = 180) -> str:
    if not text:
        return ""
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(text.strip()) if p.strip()]
    one = ", ".join(parts) if len(parts) > 1 else (parts[0] if parts else text.strip())
    return (one[:max_chars].rstrip() + "…") if len(one) > max_chars else one

def summarize_steps_one_line(washing_steps: List[str]) -> str:
    api_key = settings.CLOVA_API_KEY
    url = settings.CLOVA_SUMMARY_URL
    if not api_key or not url:
        raise RuntimeError("CLOVA_API_KEY 또는 CLOVA_SUMMARY_URL이 설정되지 않았습니다.")

    steps_text = "\n".join(f"• {s.strip()}" for s in washing_steps if s and s.strip())
    if len(steps_text) > 34000:
        steps_text = steps_text[:34000]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": uuid.uuid4().hex,
    }
    payload = {
        "texts": [steps_text],
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1200,
        "segMinSize": 300,
        "includeAiFilters": False,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    raw_summary = (data.get("result") or {}).get("text", "").strip()

    return _collapse_to_one_sentence(raw_summary, max_chars=180)
