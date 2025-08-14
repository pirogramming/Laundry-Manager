# laundry_manager/services/text_rules.py

from typing import List, Dict, Any
import os, re, json
from django.conf import settings

# 기존 RULES에 display(표시 라벨)만 추가
RULES = [
    {
        "code": "hand_wash",
        "display": "손세탁",
        "keywords": [r"손세탁", r"손\s*세탁", r"손\s*빨래"],
        "negations": [r"금지", r"불가", r"하지\s*마세요", r"하지\s*말것"],
        "positive_msg": "손세탁을 하세요.",
        "negative_msg": "손세탁을 하지 마세요.",
        "category": "washing",
    },
    {
        "code": "machine_wash",
        "display": "물세탁/세탁기",
        "keywords": [r"물세탁", r"세탁기", r"세탁\s*하"],
        "negations": [r"금지", r"불가", r"하지\s*마세요", r"하지\s*말것"],
        "positive_msg": "세탁기로 물세탁이 가능합니다.",
        "negative_msg": "세탁기 물세탁을 하지 마세요.",
        "category": "washing",
    },
    {
        "code": "dry_clean",
        "display": "드라이클리닝",
        "keywords": [r"드라이\s*클리닝", r"드라이클리닝"],
        "negations": [r"금지", r"불가"],
        "positive_msg": "드라이클리닝 하세요.",
        "negative_msg": "드라이클리닝을 하지 마세요.",
        "category": "dry",
    },
    {
        "code": "iron",
        "display": "다림질",
        "keywords": [r"다림질", r"다리미"],
        "negations": [r"금지", r"불가"],
        "positive_msg": "다림질이 가능합니다.",
        "negative_msg": "다림질을 하지 마세요.",
        "category": "iron",
    },
    {
        "code": "tumble_dry",
        "display": "건조기",
        "keywords": [r"건조기", r"텀블\s*건조", r"회전식\s*건조"],
        "negations": [r"금지", r"불가"],
        "positive_msg": "건조기 사용이 가능합니다.",
        "negative_msg": "건조기 사용을 하지 마세요.",
        "category": "dry",
    },
    {
        "code": "bleach_chlorine",
        "display": "염소계 표백",
        "keywords": [r"염소계\s*표백", r"표백제"],
        "negations": [r"금지", r"불가"],
        "positive_msg": "염소계 표백제가 가능합니다.",
        "negative_msg": "염소계 표백제를 사용하지 마세요.",
        "category": "bleach",
    },
]

def _normalize_texts(texts: List[str]) -> str:
    import re
    joined = " ".join([t or "" for t in texts])
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined

def _normalize(texts: List[str]) -> str:
    s = " ".join([t or "" for t in texts])
    return re.sub(r"\s+", " ", s).strip()

def analyze_texts(recognized_texts: List[str]) -> List[Dict[str, Any]]:
    text = _normalize(recognized_texts)
    results: List[Dict[str, Any]] = []
    for rule in RULES:
        has_kw = any(re.search(kw, text, re.IGNORECASE) for kw in rule["keywords"])
        if not has_kw:
            continue
        has_neg = any(re.search(ng, text, re.IGNORECASE) for ng in rule["negations"])
        results.append({
            "code": rule["code"],
            "state": "deny" if has_neg else "allow",
            "message": rule["negative_msg"] if has_neg else rule["positive_msg"],
            "matched": rule["keywords"] + (rule["negations"] if has_neg else []),
            "category": rule["category"],
        })
    return results

def extract_rule_keywords(recognized_texts: List[str]) -> List[str]:
    """
    OCR 텍스트에서 RULES.keyword 정규식이 실제로 매치된 항목만
    RULES.display 라벨로 모아 반환(중복 제거, 원문과 무관).
    """
    text = _normalize_texts(recognized_texts)
    hits: List[str] = []
    for rule in RULES:
        if any(re.search(pat, text, re.IGNORECASE) for pat in rule["keywords"]):
            hits.append(rule.get("display", rule["code"]))
    # 중복 제거(라벨 기준) + 원래 순서 유지
    seen = set()
    deduped = []
    for h in hits:
        if h in seen: 
            continue
        seen.add(h)
        deduped.append(h)
    return deduped


# output 폴더에서 최신 *_result.json의 recognized_texts 복구 (세션 없을 때 대비)
def load_latest_recognized_texts_from_output() -> List[str]:
    output_dir = os.path.join(settings.BASE_DIR, "output")
    if not os.path.isdir(output_dir):
        return []
    cands = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith("_result.json")]
    if not cands:
        return []
    latest = max(cands, key=os.path.getmtime)
    try:
        with open(latest, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("recognized_texts", []) or []
    except Exception:
        return []