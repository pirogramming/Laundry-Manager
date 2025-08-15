# laundry_manager/services/text_rules.py

from typing import List, Dict, Any, Tuple, Optional
import os, re, json, unicodedata
from dataclasses import dataclass
from django.conf import settings

# --- DEBUG: 규칙 로딩 상태 스냅샷 ---
def rules_debug_snapshot() -> Dict[str, Any]:
    from django.conf import settings
    exists = []
    for p in CANDIDATE_JSON_PATHS:
        exists.append({"path": p, "exists": os.path.isfile(p)})
    return {
        "BASE_DIR": str(settings.BASE_DIR),
        "candidates": exists,
        "loaded_count": len(_COMPILED_RULES),
        "some_ids": [getattr(r, "id", "") for r in _COMPILED_RULES[:5]],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 경로/상수
# ─────────────────────────────────────────────────────────────────────────────
CANDIDATE_JSON_PATHS = [
    os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "washing_symbol.json"),
    os.path.join(settings.BASE_DIR, "json_data", "washing_symbol.json"),
    os.path.join(settings.BASE_DIR, "washing_symbol.json"),
]
DEFAULT_NEGATION_WINDOW = 15  # (현재 do_not_* 네이밍으로 deny 처리하므로 미사용)




# 파일 상단 util 근처에 추가
_QUAL_PATS = {
    "hand": re.compile(r"(손세탁|손\b)"),
    "machine": re.compile(r"(세탁기|물세탁)"),
    "very": re.compile(r"(매우\s*약)"),
    "gentle": re.compile(r"(약(하게)?|약\s*하게)"),
    "neutral": re.compile(r"(중성\s*세제|중성세제|중성)"),
    "steam": re.compile(r"(스팀)"),
    "no_steam": re.compile(r"(스팀\s*금지|스팀\s*없이|스팀없이)"),
}

def _specificity_score(rule_id: str, text: str) -> int:
    """
    규칙이 얼마나 '구체적으로' 맞는지 점수화.
    더 구체적인 규칙이 같은 카테고리에서 이기도록 함.
    """
    score = 0
    rid = rule_id.lower()

    # 온도 숫자 존재 여부 (30/40/50/60/70/95)
    m = re.search(r"\b(30|40|50|60|70|95)\b", text)
    if m and m.group(1) in rid:
        score += 2

    # 손/세탁기 판별
    if _QUAL_PATS["hand"].search(text) and rid.startswith("hand_wash"):
        score += 3
    if _QUAL_PATS["machine"].search(text) and rid.startswith("wash_"):
        score += 2

    # 강도
    if _QUAL_PATS["very"].search(text) and "very_gentle" in rid:
        score += 3
    elif _QUAL_PATS["gentle"].search(text) and "gentle" in rid and "very_gentle" not in rid:
        score += 2
    elif "normal" in rid:
        score += 1

    # 중성세제
    if _QUAL_PATS["neutral"].search(text) and "neutral_detergent" in rid:
        score += 2

    # 다림질 스팀
    if _QUAL_PATS["steam"].search(text) and "_steam" in rid:
        score += 2
    if _QUAL_PATS["no_steam"].search(text) and "no_steam" in rid:
        score += 2

    # 금지 규칙은 메시지 노이즈가 많을 때 우선 보여주도록 약간 가산
    if rid.startswith("do_not_"):
        score += 1

    return score



# ─────────────────────────────────────────────────────────────────────────────
# 데이터 모델
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class JsonRule:
    id: str
    keywords: List[str]
    description: str
    category: str  # 코드에서 id로 자동 추론 (JSON에 없어도 됨)

@dataclass
class CompiledRule:
    id: str
    description: str
    category: str
    deny: bool
    kw_patterns: List[re.Pattern]
    ctx_patterns: List[re.Pattern]  # 카테고리/사용자 정의 맥락 단서

# ─────────────────────────────────────────────────────────────────────────────
# 전처리 유틸
# ─────────────────────────────────────────────────────────────────────────────
def _normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _join_and_normalize(texts: List[str]) -> str:
    return _normalize_text(" ".join(t or "" for t in texts))

def _infer_category(rule_id: str) -> str:
    rid = (rule_id or "").lower()
    if rid.startswith(("wash_", "hand_wash_")): return "washing"
    if rid.startswith(("bleach_", "do_not_bleach", "do_not_chlorine_bleach", "do_not_oxygen_bleach")): return "bleach"
    if rid.startswith(("iron_", "do_not_iron")): return "iron"
    if rid.startswith(("dry_clean_", "do_not_dry_clean")): return "dry_clean"
    if rid.startswith(("wet_clean_", "do_not_wet_clean")): return "wet_clean"
    if rid.startswith(("natural_dry_",)): return "dry"
    if rid.startswith(("machine_dry_", "do_not_machine_dry")): return "dry"
    if rid.startswith(("spin_", "do_not_spin")): return "dry"
    return "other"

# 카테고리별 기본 컨텍스트(숫자 30/40/60 충돌 방지)
_CATEGORY_CONTEXT: Dict[str, List[str]] = {
    "washing":    [r"(세탁기|물세탁|세탁|손세탁)"],
    "bleach":     [r"(표백)"],
    "iron":       [r"(다리미|다림질|스팀)"],
    "dry_clean":  [r"(드라이\s*클리닝|드라이|클리닝)"],
    "wet_clean":  [r"(습식|웨트|웨트클리닝)"],
    "dry":        [r"(건조|자연건조|그늘|햇볕|뉘어|옷걸이|건조기|텀블)"],
    "other":      [],
}

def _token_to_pattern(token: str) -> re.Pattern:
    """
    JSON keywords의 토큰을 정규식으로 컴파일.
    - '30°C', '30 C' 등은 공백/기호 허용
    - 숫자 단독은 단어경계 사용
    - 일반 텍스트는 부분일치 허용
    """
    t = (token or "").strip()
    # 온도 표현(예: 40°C, 40 C)
    m = re.fullmatch(r"(\d{1,3})\s*°?\s*C", t, flags=re.IGNORECASE)
    if m:
        n = m.group(1)
        pat = rf"{n}\s*°?\s*C"
        return re.compile(pat, re.IGNORECASE)
    # 순수 숫자
    if re.fullmatch(r"\d{1,3}", t):
        return re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)
    # 일반 텍스트
    return re.compile(re.escape(t), re.IGNORECASE)

def _compile_context_patterns(category: str, rule_id: str) -> List[re.Pattern]:
    ctx = list(_CATEGORY_CONTEXT.get(category, []))
    # 세부 보정: machine_dry / natural_dry / spin
    if rule_id.startswith("machine_dry_"):
        ctx.insert(0, r"(기계\s*건조|건조기|텀블)")
    if rule_id.startswith("natural_dry_"):
        ctx.insert(0, r"(자연건조|그늘|햇볕|뉘어|옷걸이)")
    if rule_id.startswith(("spin_", "do_not_spin")):
        ctx = [r"(탈수|짜다|원심)"]
    return [re.compile(p, re.IGNORECASE) for p in ctx]

# ─────────────────────────────────────────────────────────────────────────────
# JSON 로딩(다중 경로 + 로깅 + 재로딩 지원)
# ─────────────────────────────────────────────────────────────────────────────
_JSON_LOAD_LOGGED = False  # 동일 메시지 중복 방지
def _load_json_rules_from_candidates() -> List[CompiledRule]:
    """
    후보 경로들을 순회하여 첫 번째로 존재하는 JSON을 읽어 규칙 컴파일.
    JSON 항목이 'requires'를 포함하면 이를 컨텍스트로 사용.
    """
    global _JSON_LOAD_LOGGED
    loaded: List[CompiledRule] = []
    picked_path: Optional[str] = None

    for path in CANDIDATE_JSON_PATHS:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            compiled: List[CompiledRule] = []
            seen_ids = set()

            for item in raw:
                rid = (item.get("id") or "").strip()
                if not rid or rid in seen_ids:
                    continue
                seen_ids.add(rid)

                keywords = item.get("keywords") or []
                description = item.get("description") or rid
                category = (item.get("category") or _infer_category(rid)).strip()
                deny = rid.startswith("do_not_")

                kw_pats = [_token_to_pattern(tok) for tok in keywords if (tok or "").strip()]

                # requires가 있으면 이를 컨텍스트로, 없으면 카테고리 기본 컨텍스트 사용
                req_words = item.get("requires") or []
                if req_words:
                    ctx_pats = [re.compile(re.escape(w), re.IGNORECASE) for w in req_words if (w or "").strip()]
                else:
                    ctx_pats = _compile_context_patterns(category, rid)

                compiled.append(CompiledRule(
                    id=rid,
                    description=description,
                    category=category,
                    deny=deny,
                    kw_patterns=kw_pats,
                    ctx_patterns=ctx_pats,
                ))
            loaded = compiled
            picked_path = path
            break
        except Exception:
            # 다음 후보 계속 시도
            continue

    # 최초 1회 로딩 로그
    if not _JSON_LOAD_LOGGED:
        _JSON_LOAD_LOGGED = True
        if picked_path:
            print(f"[text_rules] Loaded {len(loaded)} rules from: {picked_path}")
        else:
            print("[text_rules] No rules loaded. Checked paths:", CANDIDATE_JSON_PATHS)
    return loaded

# 초기 로드
_COMPILED_RULES: List[CompiledRule] = _load_json_rules_from_candidates()

def rules_loaded_count() -> int:
    return len(_COMPILED_RULES)

def reload_rules() -> int:
    """외부에서 강제 재로드할 때 사용(테스트/관리자 명령 등)."""
    global _COMPILED_RULES
    _COMPILED_RULES = _load_json_rules_from_candidates()
    return len(_COMPILED_RULES)

# ─────────────────────────────────────────────────────────────────────────────
# 매칭 유틸
# ─────────────────────────────────────────────────────────────────────────────
def _find_spans(pattern: re.Pattern, text: str) -> List[Tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in pattern.finditer(text)]

def _context_present(rule: CompiledRule, text: str) -> Tuple[bool, Optional[str]]:
    # 컨텍스트 패턴이 하나도 없으면 컨텍스트 요구하지 않음
    if not rule.ctx_patterns:
        return True, None
    for p in rule.ctx_patterns:
        m = p.search(text)
        if m:
            return True, m.group(0)
    return False, None

# ─────────────────────────────────────────────────────────────────────────────
# 공개 API (시그니처 유지)
# ─────────────────────────────────────────────────────────────────────────────
def analyze_texts(recognized_texts: List[str]) -> List[Dict[str, Any]]:
    global _COMPILED_RULES
    if not _COMPILED_RULES:
        _COMPILED_RULES = _load_json_rules_from_candidates()
    if not _COMPILED_RULES:
        return []

    text = _join_and_normalize(recognized_texts)

    # 1) 모든 후보 수집(점수 포함)
    candidates: List[Tuple[int, Dict[str, Any]]] = []
    for rule in _COMPILED_RULES:
        ctx_ok, ctx_frag = _context_present(rule, text)
        if not ctx_ok:
            continue

        kw_hits = []
        for p in rule.kw_patterns:
            kw_hits.extend(_find_spans(p, text))
        if not kw_hits:
            continue

        matched = [frag for (_, _, frag) in kw_hits]
        if ctx_frag:
            matched.append(ctx_frag)

        result = {
            "code": rule.id,
            "state": "deny" if rule.deny else "allow",
            "message": rule.description,
            "matched": list(dict.fromkeys(matched)),
            "category": rule.category,
        }
        score = _specificity_score(rule.id, text)
        candidates.append((score, result))

    if not candidates:
        return []

    # 2) 카테고리별 최고 점수 1개만 선택
    best_by_cat: Dict[str, Tuple[int, Dict[str, Any]]] = {}
    for score, res in candidates:
        cat = res["category"]
        cur = best_by_cat.get(cat)
        if (cur is None) or (score > cur[0]):
            best_by_cat[cat] = (score, res)

    # 3) 보기 좋은 정렬: deny 먼저, 그다음 점수/카테고리명
    final = [v[1] for v in best_by_cat.values()]
    final.sort(key=lambda r: (0 if r["state"] == "deny" else 1, -_specificity_score(r["code"], text), r["category"]))
    return final


def extract_rule_keywords(recognized_texts: List[str]) -> List[str]:
    """
    OCR 텍스트에서 실제 매칭된 규칙들의 '설명(description)' 라벨만 리스트로 반환.
    (중복 제거 및 입력 순서 유지)
    """
    hits = analyze_texts(recognized_texts)
    labels = [h["message"] for h in hits]
    seen = set()
    out: List[str] = []
    for label in labels:
        if label in seen:
            continue
        seen.add(label)
        out.append(label)
    return out

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
        texts = data.get("recognized_texts")
        return texts if isinstance(texts, list) else []
    except Exception:
        return []
