# laundry_manager/views/summary.py
import uuid
import re
import difflib
import requests
from typing import List, Dict, Union
from django.conf import settings
from django.core.cache import cache
from django.utils.html import conditional_escape
from django.templatetags.static import static

# ---------- 공통 정규식/유틸 ----------
_WS_RE = re.compile(r"\s+")
_BULLET_PREFIX_RE = re.compile(r"^\s*([\-–—•·]+|\d+\s*[\.\)]\s*)")
_NEG_PAT  = re.compile(r"(금지|불가|하지\s*말|피하|금물|표백\s*금지|염소계\s*표백|과산화)")
_WARN_PAT = re.compile(r"(주의|손상|조심|약하게)")

# 키워드/정규식
_TEMP_RE   = re.compile(r"(\d{2,3})\s*(?:℃|°C)")
_HAND_RE   = re.compile(r"(손세탁)")
_GENTLE_RE = re.compile(r"(약하게|울\s*코스|섬세\s*코스)")
_DET_RE    = re.compile(r"(중성세제|울\s*전용\s*세제)")
_NOWASH_RE = re.compile(r"(물세탁\s*금지|세탁\s*불가)")

_DRYER_NO_RE   = re.compile(r"(건조기.*금지|건조기\s*금지|do not tumble dry)", re.I)
_DRYER_OK_RE   = re.compile(r"(건조기.*가능|tumble dry)", re.I)
_FLAT_RE       = re.compile(r"(뉘어서|평평하게)")
_HANG_RE       = re.compile(r"(걸어서|옷걸이|행거)")
_SHADE_RE      = re.compile(r"(그늘)")
_SUN_RE        = re.compile(r"(햇볕|직사광선)")
_NOWRING_RE    = re.compile(r"(비틀어|짜지\s*말)")
INFO_ICON_FILENAME = "square-check-solid-full.png"

# 이미지 추가 
def _static_icon_url(filename: str) -> str:
    return static(filename)
# ---------- 전처리 ----------
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

def _emoji_to_markup(marker: str) -> str:
    if marker == "❇️":
        url = _static_icon_url(INFO_ICON_FILENAME)
        return (
            f"<img src='{url}' alt='' "
            f"style='width:18px;height:18px;vertical-align:-2px;'/>"
        )
    return conditional_escape(marker)

def _icon_for_line(s: str) -> str:
    if _NEG_PAT.search(s):
        return "🚫"
    if _WARN_PAT.search(s):
        return "⚠️"
    return "❇️"

def _ban_first(lines: List[str]) -> List[str]:
    bans = [x for x in (lines or []) if _NEG_PAT.search(x)]
    others = [x for x in (lines or []) if not _NEG_PAT.search(x)]
    return bans + others

def _verbify_wash_line(s: str) -> str:
    t = _compact_phrase(s)
    t = re.sub(r"[\.·•]+$", "", t).strip()

    if _NEG_PAT.search(t):
        t = re.sub(r"(금지|불가).*$", r"\1", t)
        return t
    
    if "중성세제" in t and "사용" not in t:
        t += " 사용"

    if t.endswith("코스") and "사용" not in t:
        t += " 사용"
    
    if re.search(r"(세탁|사용|가능|권장|제거)$", t):
        return t
    
    return t + " 세탁"

def _filter_instruction_noise(lines: List[str]) -> List[str]:
    out = []
    for ln in (lines or []):
        if _INSTRUCTION_NOISE_RE.search(ln):
            continue
        #열거형 필터: 숫자/온도/구체 규칙이 전혀 없고 열거형 특성이 강하면 제거하기
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

def _tidy_tail_short(s: str) -> str:
    """끝에 어색한 조사 정리"""
    s = s.rstrip(" ,)·•.;")
    s = re.sub(r"(은|는|이|가|을|를|에|로|으로|과|와|및|도|만|까지|부터)$", "", s)
    if s.endswith("한") and len(s) > 1:
        s = s[:-1]
    return s.strip()

def _enforce_clause_ending(s: str, prefer: str = "함") -> str:
    s = s.rstrip(" ,.;:…")
    if s.endswith(("함", "임")):
        return s
    if re.search(r"(합니다|하십시오|하시오|하세요)$", s):
        return re.sub(r"(합니다|십시오|하시오|하세요)$", prefer, s)
    if s.endswith(("다", "요", "음")):
        return s[:-1] + prefer
    return s + prefer

def _to_eumseum(s: str, default_suffix: str = "함") -> str:
    t = (s or "").strip().rstrip(".")
    # 흔한 종결형 → 음슴체
    t = re.sub(r"(합니다|한다)$", default_suffix, t)
    t = re.sub(r"(하세요|하시오|하십시오)$", default_suffix, t)
    t = re.sub(r"(이다|입니다)$", "임", t)
    # '~할 수 있다' 류 → '가능'
    t = re.sub(r"(할\s*수\s*있다|할\s*수\s*있습니다)$", "가능", t)
    # 남은 '...다' 일반형은 기본 음슴체로
    t = re.sub(r"다$", default_suffix, t)
    return t

def _to_plain_lines(raw: str, line_limit: int = 3, char_limit: int = 34) -> List[str]:
    parts = []
    for ln in re.split(r"[\r\n]+", raw or ""):
        ln = _compact_phrase(_BULLET_PREFIX_RE.sub("", ln).strip())
        if ln:
            parts.append(ln)
    parts = _dedupe_chunks_strong(parts)

    out = [_soft_truncate(p, char_limit) for p in parts]
    out = [_to_eumseum(x, "함") for x in out]
    out = _filter_instruction_noise(out)
    out = _dedupe_preserve_order_final(out)
    return [x for x in out if x][:line_limit]

def _clean_join(sources: List[str]) -> str:
    src = "\n".join(s.strip() for s in (sources or []) if s and str(s).strip())
    return _clean_source(src)[:3000]

def _render_lines_html(lines: List[str], emoji: str = "❇️", auto_icon: bool = False) -> str:
    esc = conditional_escape
    container_style = ("display:flex;align-items:flex-start;gap:8px;margin:2px 0;")
    icon_style = ("flex:0 0 auto;line-height:1; font-size:16px;transform:translateY(2px);")
    text_style = "flex:1 1 auto; line-height:1.4; margin:0;"

    html = []
    for ln in (lines or []):
        if not ln:
            continue
        marker = _icon_for_line(ln) if auto_icon else emoji
        ico_html = _emoji_to_markup(marker)
        html.append(
            f"<div class='sumline' style='{container_style}'>"
            f"<span class='sum-ico' style='{icon_style}'>{ico_html}</span>"
            f"<span class='sum-txt' style='{text_style}'>{esc(ln)}</span>"
            f"</div>" 
        )
    return "".join(html)

def _shorten_tokens(s: str) -> str:
    if not s: return ""
    s = re.sub(r"\s*\([^)]{8,}\)", "", s)  # 너무 긴 괄호 내용 제거
    s = re.sub(r"\s*[,·•]\s*", ", ", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ,")
    return s

def _pick_first_match(texts, *patterns) -> bool:
    src = " ".join(t for t in texts if t)
    return any(p.search(src) for p in patterns)

def _extract_temp(texts) -> str:
    for t in texts:
        m = _TEMP_RE.search(t or "")
        if m:
            v = m.group(1)
            # 20~30 같은 범위면 최댓값만 표시
            rng = re.findall(r"\d{2,3}", t)
            if len(rng) >= 2: v = max(rng, key=int)
            return f"{v}℃ 이하"
    return ""

def _wash_lines_from_texts(material_desc: str, washing_descs: list[str]) -> list[str]:
    texts = [material_desc or ""] + list(washing_descs or [])

    nowash  = _pick_first_match(texts, _NOWASH_RE)
    temp    = _extract_temp(texts)
    hand    = _pick_first_match(texts, _HAND_RE)
    gentle  = _pick_first_match(texts, _GENTLE_RE)
    det_ok  = _pick_first_match(texts, _DET_RE)

    lines = []
    if nowash:
        # 물세탁 금지면 다른 규칙보다 우선
        lines.append("물세탁 금지, 드라이클리닝 의뢰 권장")
    else:
        parts1 = []
        if hand:   parts1.append("손세탁")
        if gentle: parts1.append("약하게")
        if temp:   parts1.append(temp)
        if det_ok: parts1.append("중성세제")
        if parts1:
            lines.append(_shorten_tokens(", ".join(parts1)))

        # 보조 문장(세탁기 사용하는 경우)
        if gentle and temp and not hand:
            lines.append(_shorten_tokens(f"세탁기 사용 시 {temp}, 섬세/울 코스"))

    # 최소 1줄도 못 만들면 빈 리스트 반환(→ CLOVA 백업)
    return [ln for ln in lines if ln][:2]  # 1~2줄로 제한

def _dry_lines_from_texts(drying_descs: list[str]) -> list[str]:
    texts = list(drying_descs or [])
    dryer_no = _pick_first_match(texts, _DRYER_NO_RE)
    dryer_ok = _pick_first_match(texts, _DRYER_OK_RE)
    flat     = _pick_first_match(texts, _FLAT_RE)
    hang     = _pick_first_match(texts, _HANG_RE)
    shade    = _pick_first_match(texts, _SHADE_RE)
    sun      = _pick_first_match(texts, _SUN_RE)
    nowring  = _pick_first_match(texts, _NOWRING_RE)

    lines = []
    if dryer_no:
        lines.append("건조기 금지")
    elif dryer_ok:
        lines.append("건조기 사용 가능")

    parts = []
    if flat:  parts.append("뉘어서")
    if hang:  parts.append("걸어서")
    if shade: parts.append("그늘 건조")
    if sun and not shade: parts.append("햇볕 건조")
    if parts:
        # '뉘어서/걸어서' 두 개가 동시에 있으면 앞 하나만
        if len(parts) > 1 and ("뉘어서" in parts and "걸어서" in parts):
            parts = [parts[0], parts[-1]]
        lines.append(_shorten_tokens(", ".join(parts)))
    if nowring:
        lines.append("비틀어 짜지 말 것")

    return [ln for ln in lines if ln][:2]

def _polish_dry_one_liner(s: str) -> str:
    t = _compact_phrase(s)
    t = re.sub(r"\s*적합한\s*", " ", t)
    t = re.sub(r"\s*일반\s*", " ", t)
    t = re.sub(r"드라이클리닝할\s*수\s*있다\.?", " 드라이클리닝 가능", t)
    if "용제 등" in t and "용제 등으로" not in t:
        t = t.replace("용제 등", "용제 등으로")
    t = re.sub(r"\s+", " ", t).strip().rstrip(".")
    # ✅ 음슴체로 마무리
    return _to_eumseum(t, "함")

def split_lines_for_ui(text: str) -> list[str]:
    if not text:
        return []
    return [
        re.sub(r"\s+", " ", ln.strip())
        for ln in re.split(r"[\r\n]+", str(text))
        if ln and str(ln).strip()
    ]


# --------------- CLOVA 호출 ----------------
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
        return_html: bool = False,
        emoji: str = "❇️",
        return_list: bool = False,
) -> Union[str, List[str]]:
    src = _clean_join(sources)
    if not src:
        return [] if return_list else ""
    fmt = "list" if return_list else ("html" if return_html else "txt")
    cache_key = f"{cache_prefix}:{hash(src)}:{fmt}"
    cached = cache.get(cache_key)
    if cached:
        return cached.split("\n") if return_list else cached

    prompt = f"{instruction}\n\n{src}"
    raw = _call_clova(prompt)
    lines = _to_plain_lines(raw, line_limit=line_limit, char_limit=char_limit)
    if not lines:
        base = _dedupe_preserve_order_simple(sources)
        lines = [_soft_truncate(_compact_phrase(s), char_limit) for s in base[:line_limit]]
    
    if return_list:
        cache.set(cache_key, "\n".join(lines), 60 * 60 * 12)
        return lines
    
    out = _render_lines_html(lines, emoji) if return_html else "\n".join(lines)
    cache.set(cache_key, out, 60 * 60 * 12)
    return out

# ---------- 세탁/건조/얼룩 요약 ----------
def make_wash_summary(material_desc: str, washing_descs: List[str]) -> str:
    lines = _wash_lines_from_texts(material_desc, washing_descs)

    if not lines:
        instruction = (
            "아래는 의류 소재 설명과 세탁 기호 설명이다. "
            "핵심 세탁 규칙만 2~3줄로 간결히 요약하라. "
            "숫자·수온·세제·코스는 남기고, 장황한 예시/화학명/중복 표현은 생략하라. "
            "쉼표는 한 줄에 최대 2개, 존대/명령형 금지."
        )
        sources = [material_desc or ""] + (washing_descs or [])
        lines = _summarize_lines_via_clova(
            sources, instruction, "wash_summary_v3",
            line_limit=3, char_limit=34, return_list=True
        )

    lines = [_verbify_wash_line(x) for x in lines]
    lines = _dedupe_preserve_order_final(lines)
    lines = _ban_first(lines)
    return _render_lines_html(lines, auto_icon=True)

def make_dry_summary(drying_descs: List[str]) -> str:
    lines = _dry_lines_from_texts(drying_descs)
    if lines:
        return _render_lines_html(_ban_first(lines), auto_icon=True)

    clean = [d for d in (drying_descs or []) if d and str(d).strip()]
    if len(clean) == 1:
        one = _polish_dry_one_liner(clean[0])
        return _render_lines_html([one], auto_icon=True)

    instruction = (
        "아래는 건조 관련 기호/설명이다. "
        "핵심만 2~3줄로 요약하라(건조기 가능/금지, 그늘/햇볕, 뉘어서/걸어서 등). "
        "장황한 부연은 생략하고 간결한 평서형으로."
    )
    lines_from_clova = _summarize_lines_via_clova(
        clean, instruction, "dry_summary_v3",
        line_limit=3, char_limit=34, return_list=True
    )
    lines_from_clova = _ban_first(lines_from_clova)
    return _render_lines_html(lines_from_clova, auto_icon=True)


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
    return _render_lines_html(lines, emoji="❇️")

# ---------- 뷰에서 쓰는 래퍼(캐시) ----------
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
        if kw:
            out["stain"] = kw
    except Exception as e:
        print(f"[dev] apply_stain_steps_summary 실패: {e}")
    return out
