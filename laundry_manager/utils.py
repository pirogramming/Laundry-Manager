import os
import uuid
import time
import json
import re
import requests
from decouple import config
from django.conf import settings

#세탁 기호 정의 json 로드
def load_washing_definitions():
    default_path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'washing_symbol.json')
    path = config("WASHING_SYMBOL_PATH", default=default_path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print("세탁 기호 정의 파일 로드 완료.")
            return json.load(f)
    except Exception as e:
        print(f"세탁 기호 정의 로드 오류({path}): {e}")
        return {}

#ocr 호출하기
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

        res = requests.post(apigw_url, headers=headers, data=payload, files=files, timeout=20)
        res.raise_for_status()
        return res.json()

    except Exception as e:
        return {"error": True, "message": f"OCR 오류: {e}"}

#ocr 결과 (세탁 기호 설명 추출)
def get_washing_symbol_definition(ocr_result, definitions):
    full_text = ""
    extracted = []

    fields = ocr_result.get('images', [{}])[0].get('fields', [])
    for field in fields:
        text = field.get('inferText', '')
        full_text += text + " "
        extracted.append(text)

    if not full_text.strip():
        return "텍스트 인식 실패", extracted

    lower_text = full_text.lower()

    if isinstance(definitions, list):
        for definition in definitions:
            for keyword in definition.get("keywords", []):
                key_lower = keyword.lower()
                if re.match(r'^\d+\s?°?c$', key_lower):
                    if re.search(r'(\d+)\s?°?c', lower_text):
                        return definition.get("description", ""), extracted
                elif key_lower in lower_text:
                    return definition.get("description", ""), extracted

    elif isinstance(definitions, dict):
        for _, entry in definitions.items():
            keywords = (entry or {}).get("keywords", [])
            for keyword in keywords:
                if keyword and keyword.lower() in lower_text:
                    return (entry or {}).get("description", ""), extracted
    
    return "인식된 기호 설명 없음", extracted

#Roboflow 단일 분류
def classify_laundry_symbol(image_path, model_slug=None, version=None):
    try:
        model = model_slug or config("RF_CLASSIFY_MODEL")
        ver = version or config("RF_CLASSIFY_VERSION")
        api_key = config("ROBOFLOW_API_KEY")
        url = f"https://classify.roboflow.com/{model}/{ver}?api_key={api_key}"
        with open(image_path, "rb") as f:
            res = requests.post(url, files={"file": f}, timeout=20)
        res.raise_for_status()
        result = res.json()
        pred = (result.get("predictions") or [{}])[0]
        return pred.get("class", "unknown"), float(pred.get("confidence", 0) or 0)
    except Exception as e:
        print(f"Roboflow classify 오류: {e}")
        return "분류 실패", 0.0

#Roboflow 여러 개 분류
def classify_symbols_via_roboflow(image_path, model_slug=None, version=None):
    try:
        api_key = config("ROBOFLOW_API_KEY")
        model = model_slug or config("RF_CLASSIFY_MODEL")
        ver = version or config("RF_CLASSIFY_VERSION")
        url = f"https://classify.roboflow.com/{model}/{ver}?api_key={api_key}"
        with open(image_path, "rb") as f:
            res = requests.post(url, files={"file": f}, timeout=20)
        res.raise_for_status()
        return res.json().get("predictions", [])
    except Exception as e:
        print("Roboflow classify 오류:", e)
        return []

#Roboflow 감지
def detect_symbols_via_roboflow(image_path, model_slug=None, version=None, confidence=0.35, overlap=0.5):
    try:
        api_key = config("ROBOFLOW_API_KEY")
        model = model_slug or config("RF_DETECT_MODEL")
        ver = version or config("RF_DETECT_VERSION")
        url = f"https://detect.roboflow.com/{model}/{ver}"
        params = {"api_key" : api_key, "confidence" : confidence, "overlap" : overlap}
        with open(image_path, "rb") as f:
            res = requests.post(url, params=params, files={"file" : f}, timeout=20)
        res.raise_for_status()
        data = res.json()
        return [
            {
                'label' : p.get("class"),
                "confidence" : float(p.get("confidence", 0)or 0),
                "bbox" : [p.get('x'), p.get("y"), p.get("width"), p.get("height")]
            }
            for p in (data.get("predictions") or [])
        ]
    except Exception as e:
        print("Roboflow detect 오류:", e)
        return []

#라벨 정규화
LABEL_CANON = {
    "do_not_bleach": {
        "aliases": ["no bleach", "do not bleach", "표백 금지", "표백제 금지", "염소표백 금지", "표백금지"]
    },
    "do_not_chlorine_bleach": {
        "aliases": ["no chlorine bleach", "do not chlorine bleach", "염소계 표백제 사용 금지", "염소표백제 금지"]
    },
    "do_not_dry_clean": {
        "aliases": ["no dry clean", "dry clean not allowed", "드라이클리닝 금지", "드라이 금지", "드라이 금지."]
    },
    "do_not_iron": {
        "aliases": ["no iron", "do not iron", "다림질 금지", "다림질금지"]
    },
    "do_not_machine_dry": {
        "aliases": ["do not tumble dry", "no tumble dry", "기계건조 금지", "건조기 금지", "건조 금지"]
    },
    "do_not_oxygen_bleach": {
        "aliases": ["no oxygen bleach", "산소계 표백제 금지", "산소표백 금지", "산소표백제 금지"]
    },
    "do_not_spin": {
        "aliases": ["no spin", "탈수 금지", "탈수금지"]
    },
    "do_not_wash": {
        "aliases": ["no wash", "세탁 금지", "물세탁 금지", "세탁금지", "물세탁금지"]
    },
    "do_not_wet_clean": {
        "aliases": ["no wet clean", "wet clean not allowed", "습식세탁 금지", "웻클리닝 금지", "웻 클리닝 금지"]
    },
}

CONFLICT_SETS = [

]

RF_TARGET_LABELS = {
    "do_not_bleach",
    "do_not_chlorine_bleach",
    "do_not_dry_clean",
    "do_not_iron",
    "do_not_machine_dry",
    "do_not_oxygen_bleach",
    "do_not_spin",
    "do_not_wash",
    "do_not_wet_clean",
}

#ocr 응답에서 텍스트만 추출하기 
def extract_ocr_texts(ocr_result):
    texts = []
    fields = (ocr_result.get('images') or [{}])[0].get('fields', []) or []
    for f in fields:
        t = (f.get('inferText') or "").strip()
        if t:
            texts.append(t)
    return texts

# ocr 텍스트에서 
def parse_symbols_from_texts(texts):
    labels = []
    for t in texts:
        canon = normalize_to_canon(t)
        if canon:
            labels.append(canon)
    seen, uniq = set(), []
    for x in labels:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

#9개 타깃을 제외
def filter_non_rf_symbols(labels):
    return [lab for lab in labels if lab not in RF_TARGET_LABELS]

#RF 호출 ON/OFF
def should_call_roboflow():
    return config("RF_ENABLED", default="true").lower() == 'true'


def rf_threshold():
    try:
        return float(config("RF_CLASSIFY_THRESHOLD", default="0.30"))
    except:
        return 0.30

#roboflow 분류 (9개 기호만)
def pick_rf_symbols_for_targets(image_path, threshold=None, model_slug=None, version=None):
    if threshold is None:
        threshold = rf_threshold()    
    preds = classify_symbols_via_roboflow(image_path, model_slug=model_slug, version=version)
    picked = []
    for p in preds:
        lab = (p.get("class") or "").strip()
        conf = float(p.get("confidence", 0) or 0)
        canon = normalize_to_canon(lab)
        if canon in RF_TARGET_LABELS and conf >= threshold:
            picked.append((canon, conf))
    picked.sort(key=lambda x:x[1], reverse=True)
    return [lab for lab, _ in picked]


# 소재 키워드 매핑
MATERIAL_ALIASES = {
    "cotton":     ["cotton", "면", "100% 면", "면100", "면 100", "cot"],
    "linen":      ["linen", "마", "린넨"],
    "wool":       ["wool", "울", "모", "모 100", "모100"],
    "silk":       ["silk", "실크"],
    "polyester":  ["polyester", "폴리에스터", "폴리"],
    "rayon":      ["rayon", "레이온"],
    "nylon":      ["nylon", "나일론"],
    "acrylic":    ["acrylic", "아크릴"],
}

#ocr 텍스트 배열에서 소재명 추정해서 반환
def parse_material_from_texts(texts):
    joined = " ".join(texts).lower()
    for canon, aliases in MATERIAL_ALIASES.items():
        for a in aliases:
            if a.lower() in joined:
                display = next((x for x in aliases if re.search(r"[가-힣]", x)), canon)
                return canon, display
    return None, None

# 라벨에서 화면에 띄울 이름,설명
def symbols_to_guides(labels, definitions):
    guides = []
    if isinstance(definitions, dict):
        for lab in labels:
            meta = (definitions.get(lab) or {})
            name = meta.get("name") or lab
            desc = meta.get("description") or ""
            guides.append({"label": lab, "name": name, "description":desc})
    elif isinstance(definitions, list):
        by_label = {}
        for item in definitions:
            key = (item or {}).get("label") or (item or {}).get("id")
            if key:
                by_label[key] = item
        for lab in labels:
            meta = (by_label.get(lab) or {})
            name = meta.get("name") or lab
            desc = meta.get("description") or ""
            guides.append({"label":lab, "name":name, "description":desc})
    else:
        for lab in labels:
            guides.append({"label": lab, "name": lab, "description" : ""})
    return guides
    

# 문자열을 소문자로 바꾸고 앞뒤 공백 제거, 연속 공백은 하나로 축소
def _normalize_token(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def normalize_to_canon(label_or_text):
    s = _normalize_token(label_or_text).replace("°", "")
    for canon, meta in LABEL_CANON.items():
        if s == canon:
            return canon
        aliases = meta.get("aliases", [])
        for alias in aliases:
            if _normalize_token(alias).replace("°", "") in s:
                return canon
    return None


def _post_conflict_resolution(scored):
    result = dict(scored)
    for group in CONFLICT_SETS:
        present = [label for label in group if label in result]
        if len(present) >= 2:
            best_label = present[0]
            for label in present[1:]:
                if result[label] > result[best_label]:
                    best_label = label
            
            for label in present:
                if label != best_label:
                    result.pop(label, None)
    return result

def _output_folder():
    return config("OUTPUT_RESULTS_FOLDER", default="output/")

# 분류 이미지를 json 파일로 저장
def save_classification_result_json(image_path, classification_result):
    folder = _output_folder()
    os.makedirs(folder, exist_ok=True)

    output_data = {
        "filename": os.path.basename(image_path),
        "classification_result": {
            "prediction": classification_result[0],
            "confidence": float(classification_result[1])
        }
    }

    filename = os.path.join(folder, f"{os.path.splitext(os.path.basename(image_path))[0]}_classify.json")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"분류 결과 저장 완료: {filename}")
    except Exception as e:
        print(f"분류 결과 저장 오류: {e}")


def save_result_json(image_path, texts, definition, ocr_raw, rf_detect_raw=None, rf_class_raw=None, fused_scores=None):
    folder = _output_folder()
    os.makedirs(folder, exist_ok=True)

    output_data = {
        "filename": os.path.basename(image_path),
        "recognized_texts": texts,
        "symbol_definition": definition,
        "ocr_raw_response": ocr_raw,
        "roboflow_detect_raw": rf_detect_raw,
        "roboflow_classify_raw": rf_class_raw,
        "fused_scores": fused_scores
    }

    filename = os.path.join(folder, f"{os.path.splitext(os.path.basename(image_path))[0]}_result.json")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"결과 저장 완료: {filename}")
    except Exception as e:
        print(f"결과 저장 오류: {e}")
