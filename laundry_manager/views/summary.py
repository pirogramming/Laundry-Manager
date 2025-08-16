# laundry_manager/views/summary.py
import uuid
import re
import difflib
import requests
from typing import List, Dict, Tuple
from django.conf import settings
from django.core.cache import cache

# ---------- 공통 정규식 ----------
_WS_RE = re.compile(r"\s+")
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
_NEG_PAT = re.compile(
    r"(금지|피하|피해|위험|주의|불가|손상|과산화|표백\s*금지|건조기\s*금지|"
    r"하지\s*말|하지말|하지\s*마|않습니다|않음|않다)"
)

def _classify_icon(s: str) -> str:
    """문장에 부정/금지/주의류 패턴이 포함되면 ⚠️, 그 외에는 전부 ✅"""
    return "⚠️" if _NEG_PAT.search(s) else "✅"

def _compact_phrase(s: str) -> str:
    """한 줄 키워드 압축: 군더더기 제거, 구두점 간소화"""
    s = s.strip()
    s = re.sub(r"\s*[:;]\s*", ", ", s)
    s = re.sub(r"\s*[-–—]\s*", ", ", s)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    s = re.sub(r"\s*,\s*,\s*", ", ", s)
    s = _WS_RE.sub(" ", s).strip(" ,")
    return s.rstrip(".!?:;、，")

# ----- 강한 중복 제거 -----
def _norm_for_chunk(s: str) -> str:
    """중복 판단용 정규화: 소문자, 공백/구두점 제거, 종결어미 제거"""
    s = s.lower()
    s = re.sub(r"(함|임|다|요|음)$", "", s)
    s = re.sub(r"[\s,.;:()\[\]{}•·\-–—]+", "", s)
    return s

def _dedupe_chunks_strong(chunks: List[str], sim_th: float = 0.92) -> List[str]:
    """문장 조각의 강한 중복 제거(정규화 동일 또는 유사도>=sim_th)"""
    kept: List[str] = []
    norms: List[str] = []
    for ch in chunks:
        n = _norm_for_chunk(ch)
        dup = False
        for i, kn in enumerate(norms):
            if n == kn:
                dup = True
                break
            # 유사도 비교(띄어쓰기/어미만 다른 경우 제거)
            if difflib.SequenceMatcher(None, n, kn).ratio() >= sim_th:
                dup = True
                break
        if not dup:
            kept.append(ch)
            norms.append(n)
    return kept

def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items:
        k = it.lower()
        if k not in seen:
            seen.add(k)
            out.append(it)
    return out

# --- 절 종결 보정 + 길이 제한 ---
def _tidy_tail(s: str) -> str:
    """잘린 끝의 어색한 꼬리(조사/접속/형용사 어미 등) 정리"""
    s = s.rstrip(" ,)")
    s = re.sub(r"(은|는|이|가|을|를|에|로|으로|과|와|랑|및|도|만|까지|부터)$", "", s)
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
    """
    카테고리 우선순위로 최대 max_pick개 선택 (같은 카테고리는 1개).
    부족하면 남은 조각에서 순서대로 채워서 항상 최대치까지 반환.
    """
    picked: List[str] = []
    used_idx = set()

    # 1) 카테고리별 1개씩
    for _, rx in _PRIORITY:
        for i, ch in enumerate(chunks):
            if i in used_idx:
                continue
            if rx.search(ch):
                picked.append(ch)
                used_idx.add(i)
                break
        if len(picked) >= max_pick:
            return picked

    # 2) 부족하면 남은 조각으로 채움
    for i, ch in enumerate(chunks):
        if len(picked) >= max_pick:
            break
        if i not in used_idx:
            picked.append(ch)
            used_idx.add(i)
    return picked

def _normalize_for_dedupe_line(s: str) -> str:
    """최종 라인 중복 판정용 정규화: 이모지 제거, 공백 압축, 어미 제거, 소문자 비교"""
    s = re.sub(r"^[\s✅⚠️]+", "", s).strip()
    s = re.sub(r"(함|임|다|요|음)$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,.")
    return s.lower()

def _dedupe_preserve_order_final(lines: List[str]) -> List[str]:
    """최종 출력 라인에서 강한 중복 제거(아이콘/어미/공백 차이 무시)"""
    seen = set()
    out = []
    for line in lines:
        key = _normalize_for_dedupe_line(line)
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out

def _split_sentences_to_keywords(text: str, line_limit: int = 3, char_limit: int = 22, ending: str = "함") -> str:
    """
    모델 요약 결과 → ✅/⚠️ 키워드 목록
    - 우선순위 카테고리에서 최대 3줄
    - 각 줄 22자 이내, 항상 '~함/임' 종결
    - 강한 중복 제거
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

    # 2) 강한 중복 제거 → 우선순위 선택
    chunks = _dedupe_chunks_strong(chunks)
    chunks = _prioritize_chunks(chunks, max_pick=line_limit)

    # 3) 길이 제한/종결 보정/아이콘
    texts = []
    for ch in chunks:
        fixed = _truncate_with_clause(ch, char_limit, prefer=ending)
        icon = _classify_icon(ch)
        texts.append(f"{icon} {fixed}")

    # 4) 최종 중복 라인 제거
    out = _dedupe_preserve_order_final(texts)
    return "\n".join(out[:line_limit])

# ---------- CLOVA 호출: 키워드 요약 ----------
def summarize_steps_keywords(washing_steps: List[str]) -> str:
    """Washing_Steps 배열을 받아 키워드 목록(✅/⚠️)으로 요약"""
    api_key = settings.CLOVA_API_KEY
    url = settings.CLOVA_SUMMARY_URL
    if not api_key or not url:
        raise RuntimeError("CLOVA_API_KEY 또는 CLOVA_SUMMARY_URL이 설정되지 않았습니다.")

    steps_src = "\n".join(s.strip() for s in (washing_steps or []) if s and s.strip())
    steps_src = _clean_source(steps_src)
    if len(steps_src) > 3000:
        steps_src = steps_src[:3000]

    instruction = (
        "다음 세탁 단계를 바탕으로 핵심 조건/행동만 뽑아 키워드 목록으로 요약하세요. "
        "각 줄의 형식은 '내용'만 포함하며 불릿/번호/콜론 없이 간결하게 쓰고, "
        "줄 수는 3줄 이내, 각 줄은 40자 이내로 작성하세요. "
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
    """상단 요약 딕셔너리(summary)에 '키워드 목록'을 주입(덮어쓰기)."""
    out = dict(summary or {"wash": None, "dry": None, "stain": None})
    try:
        kw = make_stain_steps_one_liner(stain_guide)
        if kw:
            out["stain"] = kw
    except Exception as e:
        print(f"[dev] apply_stain_steps_summary 실패: {e}")
    return out
