# laundry_manager/views/summary.py
import uuid
import re
import difflib
import requests
from typing import List, Dict
from django.conf import settings
from django.core.cache import cache

# ---------- 공통 정규식/유틸 ----------
_WS_RE = re.compile(r"\s+")
_BULLET_PREFIX_RE = re.compile(r"^\s*([\-–—•·]+|\d+\s*[\.\)]\s*)")

# 지시문/예시 느낌 문장 제거용 패턴
_INSTRUCTION_NOISE_RE = re.compile(
    r"(요약|3\s*줄|세\s*줄|문장|작성|불릿|번호|말줄임표|핵심\s*규칙|포함하라|평서형)"
)
# 열거형/예시성 문장(지시문이 아니더라도 결과에 남아버린 경우) 제거
_ENUMY_LINE_RE = re.compile(
    r"(?:/.*/)|"      # 슬래시가 2번 이상 등장 (예: 가능/금지, 자연건조/그늘건조/…)
    r"(가능/금지)|"    # '가능/금지' 패턴 자체
    r"(등\s*$)"       # '…등'으로 끝나는 문장
)

def _filter_instruction_noise(lines: List[str]) -> List[str]:
    out = []
    for ln in (lines or []):
        if _INSTRUCTION_NOISE_RE.search(ln):
            continue
        # 열거형 필터: 숫자/온도/구체 규칙이 전혀 없고 열거형 특성이 강하면 제거
        if _ENUMY_LINE_RE.search(ln) and not re.search(r"(\d|℃|°C|도|분|시간)", ln):
            continue
        out.append(ln)
    return out

def _dedupe_preserve_order_simple(items: List[str]) -> List[str]:
    seen, out = set(), []
    for it in items or []:
        t = (it or "").strip()
        if not t:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def _clean_source(text: str) -> str:
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

def _compact_phrase(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s*[:;]\s*", ", ", s)
    s = re.sub(r"\s*[-–—]\s*", ", ", s)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    s = re.sub(r"\s*,\s*,\s*", ", ", s)
    s = _WS_RE.sub(" ", s).strip(" ,")
    return s.rstrip(".!?:;、，")

def _norm_for_chunk(s: str) -> str:
    s = s.lower()
    s = re.sub(r"(함|임|다|요|음)$", "", s)
    s = re.sub(r"[\s,.;:()\[\]{}•·\-–—]+", "", s)
    return s

def _dedupe_chunks_strong(chunks: List[str], sim_th: float = 0.92) -> List[str]:
    kept, norms = [], []
    for ch in chunks:
        n = _norm_for_chunk(ch)
        dup = any(n == kn or difflib.SequenceMatcher(None, n, kn).ratio() >= sim_th for kn in norms)
        if not dup:
            kept.append(ch); norms.append(n)
    return kept

def _normalize_for_dedupe_line(s: str) -> str:
    s = re.sub(r"^[\s✅⚠️]+", "", s).strip()
    s = re.sub(r"(함|임|다|요|음)$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,.")
    return s.lower()

def _dedupe_preserve_order_final(lines: List[str]) -> List[str]:
    seen, out = set(), []
    for line in lines:
        key = _normalize_for_dedupe_line(line)
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return out

def _soft_truncate(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s.rstrip(".")
    cut = s[:limit].rstrip()
    for sep in [" ", ",", ")", "]", ";", "·", "•"]:
        i = cut.rfind(sep)
        if i >= max(8, int(limit * 0.5)):
            cut = cut[:i]; break
    return cut.strip().rstrip(".,;")

def _to_plain_lines(raw: str, line_limit: int = 3, char_limit: int = 34) -> List[str]:
    parts = []
    for ln in re.split(r"[\r\n]+", raw or ""):
        ln = _compact_phrase(_BULLET_PREFIX_RE.sub("", ln).strip())
        if ln:
            parts.append(ln)
    parts = _dedupe_chunks_strong(parts)

    out = [_soft_truncate(p, char_limit) for p in parts]
    out = _filter_instruction_noise(out)
    out = _dedupe_preserve_order_final(out)
    return [x for x in out if x][:line_limit]

def _clean_join(sources: List[str]) -> str:
    src = "\n".join(s.strip() for s in (sources or []) if s and str(s).strip())
    return _clean_source(src)[:3000]

# ---------- CLOVA 호출 ----------
def _call_clova(text: str) -> str:
    api_key = settings.CLOVA_API_KEY
    url = settings.CLOVA_SUMMARY_URL
    if not api_key or not url:
        raise RuntimeError("CLOVA_API_KEY 또는 CLOVA_SUMMARY_URL이 설정되지 않았습니다.")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": uuid.uuid4().hex,
    }
    payload = {
        "texts": [text],
        "autoSentenceSplitter": True,
        "segCount": -1,
        "segMaxSize": 1000,
        "segMinSize": 300,
        "includeAiFilters": False,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return (data.get("result") or {}).get("text", "")

def _summarize_lines_via_clova(
    sources: List[str],
    instruction: str,
    cache_prefix: str,
    line_limit: int = 3,
    char_limit: int = 34,
) -> str:
    src = _clean_join(sources)
    if not src:
        return ""
    cache_key = f"{cache_prefix}:{hash(src)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    prompt = f"{instruction}\n\n{src}"
    raw = _call_clova(prompt)

    # 혹시 모델이 지시문을 그대로 되돌려줄 경우 대비
    if instruction:
        raw = raw.replace(instruction, "")

    lines = _to_plain_lines(raw, line_limit=line_limit, char_limit=char_limit)

    # 전부 걸러지면 원문에서 직접 조밀 요약
    if not lines:
        base = _dedupe_preserve_order_simple(sources)
        lines = [_soft_truncate(_compact_phrase(s), char_limit) for s in base[:line_limit]]

    out = "\n".join(lines)
    if out:
        cache.set(cache_key, out, 60 * 60 * 12)
    return out

# ---------- 세탁/건조/얼룩 요약 ----------
def make_wash_summary(material_desc: str, washing_descs: List[str]) -> str:
    instruction = (
        "아래는 의류 소재 설명과 세탁 기호 설명이다. "
        "핵심 세탁 규칙만 3줄 이내의 짧은 문장으로 요약하라. "
        "각 줄은 한 가지 규칙만 담고, 온도/수온/세제/코스 같은 핵심 수치를 포함하라. "
        "번호/불릿/말줄임표 없이 자연스러운 평서형으로 작성하라."
    )
    sources = [material_desc or ""] + (washing_descs or [])
    return _summarize_lines_via_clova(sources, instruction, "wash_summary_v3", line_limit=3, char_limit=34)

def make_dry_summary(drying_descs: List[str]) -> str:
    # 단일 문장만 있는 경우 CLOVA를 거치지 않고 그대로 사용 (지시문 재출력 방지)
    clean = [d for d in (drying_descs or []) if d and str(d).strip()]
    if len(clean) == 1:
        return _soft_truncate(_compact_phrase(clean[0]), 34)

    instruction = (
        "아래는 건조 관련 기호/설명이다. "
        "건조 방법의 핵심 규칙만 3줄 이내의 짧은 문장으로 요약하라. "
        "건조기 사용 가능/금지, 자연건조/그늘건조/뒤집어 건조 등 핵심 키워드를 포함하라. "
        "번호/불릿/말줄임표 없이 자연스러운 평서형으로 작성하라."
    )
    return _summarize_lines_via_clova(clean, instruction, "dry_summary_v3", line_limit=3, char_limit=34)

def summarize_steps_keywords(washing_steps: List[str]) -> str:
    instruction = (
        "아래 얼룩 제거 단계를 읽고 핵심 행동/주의사항만 3줄 이내의 짧은 문장으로 요약하라. "
        "각 줄은 서로 다른 포인트를 담고, 번호/불릿/말줄임표 없이 자연스러운 평서형으로 작성하라."
    )
    src = _clean_join(washing_steps or [])
    if not src:
        return ""
    raw = _call_clova(f"{instruction}\n\n{src}")
    lines = _to_plain_lines(raw, line_limit=3, char_limit=34)
    return "\n".join(lines)

# ---------- 뷰에서 쓰는 래퍼/캐시 ----------
def _cache_key_for_steps(prefix: str, steps: List[str]) -> str:
    joined_steps = "\n".join(map(str, steps))
    return f"{prefix}:{hash(joined_steps)}"

def make_stain_steps_one_liner(stain_guide: Dict) -> str:
    steps = (stain_guide or {}).get("Washing_Steps") or []
    if not isinstance(steps, list) or not steps:
        return ""
    key = _cache_key_for_steps("stain_steps_keywords_v2", steps)
    cached = cache.get(key)
    if cached:
        return cached
    out = summarize_steps_keywords(steps)
    if out:
        cache.set(key, out, timeout=60 * 60 * 12)
    return out

def apply_wash_dry_summaries(summary: Dict, material_desc: str,
                             washing_descs: List[str], drying_descs: List[str]) -> Dict:
    out = dict(summary or {"wash": None, "dry": None, "stain": None})
    try:
        w = make_wash_summary(material_desc, washing_descs)
        if w: out["wash"] = w
    except Exception as e:
        print(f"[dev] apply_wash_dry_summaries(wash) 실패: {e}")
    try:
        d = make_dry_summary(drying_descs)
        if d: out["dry"] = d
    except Exception as e:
        print(f"[dev] apply_wash_dry_summaries(dry) 실패: {e}")
    return out

def apply_stain_steps_summary(summary: Dict, stain_guide: Dict) -> Dict:
    out = dict(summary or {"wash": None, "dry": None, "stain": None})
    try:
        kw = make_stain_steps_one_liner(stain_guide)
        if kw: out["stain"] = kw
    except Exception as e:
        print(f"[dev] apply_stain_steps_summary 실패: {e}")
    return out
