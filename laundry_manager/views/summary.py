# laundry_manager/views/summary.py
import uuid
import re
import requests
from typing import List, Dict, Tuple
from django.conf import settings
from django.core.cache import cache

# ---------- 공통 정규식 ----------
_WS_RE = re.compile(r"\s+")
_SENT_SPLIT = re.compile(r"(?<=[\.!?]|다|요)\s+(?=[A-Z가-힣0-9])")
_BULLET_PREFIX_RE = re.compile(r"^\s*([\-–—•·]+|\d+\s*[\.\)]\s*)")

# ---------- 전처리 ----------
def _clean_source(text: str) -> str:
    """모델 입력 전, 원문에 섞인 불릿/번호/중복 공백을 정리"""
    if not text:
        return ""
    lines = []
    for raw in re.split(r"[\r\n]+", text):
        line = _BULLET_PREFIX_RE.sub("", raw).strip()
        if line:
            lines.append(line)
    s = "\n".join(lines)
    s = _WS_RE.sub(" ", s)
    return s.strip()

# ---------- 후처리(키워드 라인 생성) ----------
_NEG_WORDS = ("주의", "위험", "금지", "피해", "피할", "불가", "손상", "주의하세요", "하지 마세요", "금하세요", "고온")
_POS_HINTS = ("가능", "권장", "사용", "허용", "추천", "적합", "세탁", "건조", "드라이클리닝", "다림질")

def _compact_phrase(s: str) -> str:
    """한 줄 키워드 압축: 군더더기 제거, 콜론/세미콜론/대시는 쉼표로 정리"""
    s = s.strip()
    s = re.sub(r"\s*[:;]\s*", ", ", s)
    s = re.sub(r"\s*[-–—]\s*", ", ", s)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    s = re.sub(r"\s*,\s*,\s*", ", ", s)
    s = _WS_RE.sub(" ", s).strip(" ,")
    return s.rstrip(".!?:;、，")

def _classify_icon(s: str) -> str:
    """권장/가능(✅) vs 주의/금지(⚠️) 간단 분류"""
    if any(w in s for w in _NEG_WORDS):
        return "⚠️"
    if any(h in s for h in _POS_HINTS):
        return "✅"
    if re.search(r"\d", s):
        return "✅"
    return "✅"

def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items:
        k = it.lower()
        if k not in seen:
            seen.add(k); out.append(it)
    return out

# --- 절 종결 보정 + 길이 제한 ---
def _tidy_tail(s: str) -> str:
    """잘린 끝의 어색한 꼬리(조사/접속/형용사 어미 등) 정리"""
    s = s.rstrip(" ,)")
    # 일반 조사/접속어 제거
    s = re.sub(r"(은|는|이|가|을|를|에|로|으로|과|와|랑|및|도|만|까지|부터)$", "", s)
    # dangling '한' → 형용사 어미로 추정되어 제거 (예: '미지근한' → '미지근')
    if s.endswith("한") and len(s) >= 2:
        s = s[:-1]
    return s.strip()

def _enforce_clause_ending(s: str, prefer: str = "함") -> str:
    """문장 끝을 '~함/임'으로 정리"""
    s = s.rstrip(" ,.;:…")
    if s.endswith(("함", "임")):
        return s
    if re.search(r"(합니다|십시오|하시오|하세요)$", s):
        return re.sub(r"(합니다|십시오|하시오|하세요)$", prefer, s)
    if s.endswith(("다", "요", "음")):
        return s[:-1] + prefer
    return s + prefer

def _truncate_with_clause(s: str, limit: int, prefer: str = "함") -> str:
    """limit 내로 자르고, 꼬리 정리 후 ~함/임으로 마무리 (말줄임표 X)"""
    s = s.strip()
    if len(s) <= limit:
        return _enforce_clause_ending(_tidy_tail(s), prefer)

    cut = s[:limit].rstrip()
    for sep in [" ", ",", ")", "]", "("]:
        idx = cut.rfind(sep)
        if idx >= max(6, int(limit * 0.6)):
            cut = cut[:idx].rstrip(" ,")
            break
    cut = _tidy_tail(cut)
    return _enforce_clause_ending(cut, prefer)

# --- 카테고리 우선순위 선택(세탁 → 건조 → 다림질 → 드라이) ---
_PRIORITY: List[Tuple[str, re.Pattern]] = [
    ("세탁", re.compile(r"(세탁|세탁기|울|코스|미지근|찬물|℃|°C)")),
    ("건조", re.compile(r"(건조기|자연 건조|그늘|행거|옷걸이)")),
    ("다림질", re.compile(r"(다림질|아이롱|^\s*\d{2,3}\s*(℃|°C))")),
    ("드라이", re.compile(r"(드라이클리닝|드라이)")),
]

def _prioritize_chunks(chunks: List[str], max_pick: int = 3) -> List[str]:
    """카테고리 우선순위로 최대 max_pick개 선택 (같은 카테고리는 1개)"""
    picked, used = [], set()
    for _, rx in _PRIORITY:
        for ch in chunks:
            if ch in used: 
                continue
            if rx.search(ch):
                picked.append(ch); used.add(ch); break
        if len(picked) >= max_pick:
            break
    return picked or chunks[:max_pick]

def _split_sentences_to_keywords(text: str, line_limit: int = 3, char_limit: int = 22, ending: str = "함") -> str:
    """
    모델 요약 결과 → ✅/⚠️ 키워드 목록
    - 우선순위 카테고리에서 최대 3줄
    - 각 줄 22자 이내, 항상 '~함/임' 종결
    - 최종 중복 라인 제거
    """
    if not text:
        return ""

    # 1) 문장 조각화
    raw_chunks = re.split(r"[\.!?•\-\n]+", text)
    chunks = []
    for ch in raw_chunks:
        ch = _compact_phrase(_BULLET_PREFIX_RE.sub("", ch))
        if ch:
            chunks.append(ch)

    # 2) 중복 제거 → 우선순위 선택
    chunks = _dedupe_preserve_order(chunks)
    chunks = _prioritize_chunks(chunks, max_pick=line_limit)

    # 3) 길이 제한/종결 보정/아이콘
    texts = []
    for ch in chunks:
        fixed = _truncate_with_clause(ch, char_limit, prefer=ending)
        icon = _classify_icon(ch)  # 원문 기준으로 부호 결정
        texts.append(f"{icon} {fixed}")

    # 4) 최종 중복 라인 제거
    out = _dedupe_preserve_order(texts)
    return "\n".join(out[:line_limit])

# ---------- CLOVA 호출: 키워드 요약 ----------
def summarize_steps_keywords(washing_steps: List[str]) -> str:
    """Washing_Steps 배열을 받아 키워드 목록(✅/⚠️)으로 요약"""
    api_key = settings.CLOVA_API_KEY
    url = settings.CLOVA_SUMMARY_URL
    if not api_key or not url:
        raise RuntimeError("CLOVA_API_KEY 또는 CLOVA_SUMMARY_URL이 설정되지 않았습니다.")

    # 입력 정리(+ 3000자 캡)
    steps_src = "\n".join(s.strip() for s in (washing_steps or []) if s and s.strip())
    steps_src = _clean_source(steps_src)
    if len(steps_src) > 3000:
        steps_src = steps_src[:3000]

    # 키워드형 요약 유도 지시문
    instruction = (
        "다음 세탁 단계를 바탕으로 핵심 조건/행동만 뽑아 키워드 목록으로 요약하세요. "
        "각 줄의 형식은 '내용'만 포함하며 불릿/번호/콜론 없이 간결하게 쓰고, "
        "줄 수는 3줄 이내, 각 줄은 22자 이내로 작성하세요. "
        "예시는 '세탁기 사용 가능 (30℃ 이하, 울 코스 권장)', "
        "'자연 건조 (옷걸이)', '다림질 150℃ 이하 주의', '드라이클리닝 가능'과 같습니다."
    )
    to_summarize = f"{instruction}\n\n{steps_src}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": uuid.uuid4().hex,
    }
    payload = {
        "texts": [to_summarize],
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1000,
        "segMinSize": 300,
        "includeAiFilters": False,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    raw = (data.get("result") or {}).get("text", "")

    return _split_sentences_to_keywords(raw, line_limit=3, char_limit=22, ending="함")

# ---------- 뷰에서 쓰는 래퍼(캐시 포함) ----------
def _cache_key_for_steps(prefix: str, steps: List[str]) -> str:
    joined_steps = "\n".join(map(str, steps))
    return f"{prefix}:{hash(joined_steps)}"

def make_stain_steps_one_liner(stain_guide: Dict) -> str:
    """stain_guide의 Washing_Steps → 키워드 요약(12시간 캐시)"""
    steps = (stain_guide or {}).get("Washing_Steps") or []
    if not isinstance(steps, list) or not steps:
        return ""
    key = _cache_key_for_steps("stain_steps_keywords", steps)

    cached = cache.get(key)
    if cached:
        return cached

    out = summarize_steps_keywords(steps)
    if out:
        cache.set(key, out, timeout=60 * 60 * 12)
    return out

def apply_stain_steps_summary(summary: Dict, stain_guide: Dict) -> Dict:
    """
    상단 요약 딕셔너리(summary)에 '키워드 목록'을 주입(덮어쓰기).
    템플릿에서는 {{ summary.stain }}를 <pre> 또는 white-space: pre-line으로 표시.
    """
    out = dict(summary or {"wash": None, "dry": None, "stain": None})
    try:
        kw = make_stain_steps_one_liner(stain_guide)
        if kw:
            out["stain"] = kw
    except Exception as e:
        print(f"[dev] apply_stain_steps_summary 실패: {e}")
    return out

# ======== CLOVA Summarization 헬스체크 (진단용) ========
def _clova_request(payload: dict):
    """헬스체크/진단용 raw 요청 (폴백/후처리 없음)"""
    api_key = settings.CLOVA_API_KEY
    url = settings.CLOVA_SUMMARY_URL
    if not api_key or not url:
        return (False, {"error": "MISSING_ENV", "detail": "CLOVA_API_KEY 또는 CLOVA_SUMMARY_URL 없음"})
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": uuid.uuid4().hex,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        status = r.status_code
        try:
            data = r.json()
        except Exception:
            data = {"_raw_text": r.text}
        ok = (status == 200) and bool((data.get("result") or {}).get("text"))
        return (ok, {"http_status": status, "response": data})
    except Exception as e:
        return (False, {"error": "NETWORK_OR_EXCEPTION", "detail": str(e)})

def check_clova_summary_health(sample_texts: List[str] = None):
    """CLOVA 요약 API 연결/응답 상태 점검"""
    if not sample_texts:
        sample_texts = [
            "액체 얼룩을 닦아내고 세제를 직접 바른 뒤 5~10분 두세요.",
            "미지근한 물(30℃ 이하)로 세탁하고 울 코스를 권장합니다.",
            "건조기는 피하고 자연 건조하세요.",
            "다림질은 150℃ 이하로 주의하세요.",
        ]
    payload = {
        "texts": ["\n".join(sample_texts)],
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1000,
        "segMinSize": 300,
        "includeAiFilters": False,
    }
    ok, info = _clova_request(payload)
    if not ok:
        return (False, info)
    data = info["response"]
    result = data.get("result") or {}
    return (True, {
        "http_status": info.get("http_status", 200),
        "result_text": result.get("text", ""),
        "input_tokens": result.get("inputTokens"),
        "status_code": (data.get("status") or {}).get("code"),
        "status_message": (data.get("status") or {}).get("message"),
    })
