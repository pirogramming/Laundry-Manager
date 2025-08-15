# 인식된 정보 받아오기 / json 파일 매칭 / 세탁 정보 출력
import os, json, re, difflib
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .summary import apply_stain_steps_summary

# utils 모듈 전체 임포트 (이름 임포트로 인한 ImportError/AttributeError 회피)
from .. import utils as U


# ---- JSON 로더 -------------------------------------------------------------
def _load_json(filename: str):
    """앱의 json_data 폴더에서 JSON을 로드. 없으면 안전한 기본 구조 반환."""
    path = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[dev] JSON 로드 실패 {filename}: {e}")
        if filename == "blackup.json":
            return {"material_washing_tips": []}
        if filename == "persil_v2.json":
            return []
        return {}


# ---- JSON 매칭/요약 유틸 ---------------------------------------------------
def _first_line(text) -> str:
    """문자열/리스트/딕셔너리를 받아 첫 문장만 뽑아 간단 요약."""
    if text is None:
        return ""
    if isinstance(text, list):
        text = text[0] if text else ""
    if isinstance(text, dict):
        text = next((str(v) for v in text.values() if v), "")
    t = str(text).strip()
    for sep in ["\n", "•", "·", "．", ". "]:
        if sep in t:
            return t.split(sep)[0].strip()
    return t


def _make_summary(material_guide, stain_guide, symbol_guides):
    """상단 요약 카드용 텍스트 구성."""
    wash_summary = _first_line(material_guide.get("description"))

    labels = {g.get("label") for g in (symbol_guides or [])}
    dry_summary = "건조기 사용 금지" if "do_not_machine_dry" in labels else None

    stain_text = stain_guide.get("Washing_Steps") or stain_guide.get("detail")
    stain_summary = _first_line(stain_text)

    return {"wash": wash_summary or None, "dry": dry_summary, "stain": stain_summary or None}


def _material_guide_from_json(material_name: str, material_json: dict) -> dict:
    """blackup.json: {'material_washing_tips': [{material, description, warning}, ...]}"""
    if not material_name:
        return {}
    items = material_json.get("material_washing_tips", [])
    target = material_name.strip().lower()
    for it in items:
        name = (it.get("material") or "").strip().lower()
        if name == target or target in name:
            return {
                "name": it.get("material"),
                "description": it.get("description"),
                "warning": it.get("warning"),
            }
    return {}


# ------- 얼룩 이름 정규화/별칭 ---------------------------------
_STAIN_STOPWORDS = ["자국", "얼룩", "국물", "자국들", "얼룩제거", "자국제거"]

# 한↔영 동의어/별칭 (필요하면 계속 추가)
_STAIN_ALIASES = {
    "커피": ["커피", "coffee", "coffee stain", "coffeestain"],
    "차": ["차", "tea", "green tea", "black tea"],
    "김치": ["김치", "kimchi", "김칫국물", "kimchi stain"],
    "와인": ["와인", "wine", "red wine", "white wine"],
    "혈액": ["혈액", "피", "blood", "blood stain"],
    "기름": ["기름", "기름때", "oil", "grease", "oil stain", "grease stain"],
    "과일": ["과일", "fruit", "berries", "berry", "fruit stain"],
    "초콜릿": ["초콜릿", "chocolate", "cocoa"],
    "잉크": ["잉크", "ink", "pen ink", "marker"],
    "메이크업": ["메이크업", "화장품", "makeup", "lipstick", "foundation", "mascara"],
}

def _norm(s: str) -> str:
    """불용어 제거 → 소문자 → 공백/특수문자 제거"""
    t = (s or "")
    for sw in _STAIN_STOPWORDS:
        t = t.replace(sw, "")
    t = t.strip().lower()
    return re.sub(r"[\s\W_]+", "", t)

def _expand_aliases(q: str):
    """입력으로부터 가능한 별칭 집합(정규화된) 생성"""
    qn = _norm(q)
    pool = {qn}
    for variants in _STAIN_ALIASES.values():
        norms = {_norm(v) for v in variants}
        if qn in norms:
            pool |= norms
            break
    return pool


def _candidate_strings_from_item(item):
    """
    항목에서 매칭 후보 문자열을 최대한 수집.
    - dict: title/aliases/keywords 등
    - str : 그 자체를 후보로
    - list: 내부의 str/dict를 재귀 수집
    """
    if isinstance(item, str):
        return [item]

    if isinstance(item, list):
        out = []
        for v in item:
            out.extend(_candidate_strings_from_item(v))
        return out

    if isinstance(item, dict):
        cands = []
        for k in ["title", "Title", "name", "Name", "ko", "kr", "korean", "slug", "_key"]:
            v = item.get(k)
            if v:
                cands.append(str(v))
        for k in ["aliases", "keywords", "tags"]:
            for v in item.get(k) or []:
                cands.append(str(v))
        return cands

    return []

def _normalize_items(stain_json):
    """
    다양한 구조의 persil_v2.json을 'dict 아이템 리스트'로 표준화.
    - 최상위가 list면 dict/str 각각을 dict로 변환
    - 최상위가 dict면, value가
        * dict: 바로 아이템으로
        * list: 내부의 dict들 펼쳐서 추가 (ex. washing_tips_categories)
        * str : title로 감싼 dict로 추가
    """
    items = []
    if isinstance(stain_json, list):
        for el in stain_json:
            if isinstance(el, dict):
                items.append(el)
            elif isinstance(el, str):
                items.append({"title": el})
        return items

    if isinstance(stain_json, dict):
        for k, v in stain_json.items():
            if isinstance(v, dict):
                items.append({"_key": k, **v})
            elif isinstance(v, list):
                for el in v:
                    if isinstance(el, dict):
                        items.append(el)
                    elif isinstance(el, str):
                        items.append({"_key": k, "title": el})
            elif isinstance(v, str):
                items.append({"_key": k, "title": v})
    return items


def _stain_guide_from_json(stain_name: str, stain_json) -> dict:
    """
    강화 매칭 로직:
      1) 정규화된 타깃 별칭과 후보 문자열 간 '부분 포함'을 양방향으로 검사
      2) 없으면 유사도(SequenceMatcher) 최대값으로 선택 (threshold 0.55)
      3) 반드시 dict 아이템을 대상으로 매칭 (리스트 중첩 구조도 flatten 처리)
    """
    if not stain_name:
        return {}

    targets = _expand_aliases(stain_name)  # 정규화된 타깃 별칭 집합

    # ✅ 항상 dict 아이템 리스트로 변환
    items = _normalize_items(stain_json)

    best = None

    # 1) 부분 포함 매칭 (양방향)
    for it in items:
        cands = _candidate_strings_from_item(it)
        for s in cands:
            ns = _norm(s)
            if any(t in ns or ns in t for t in targets):
                best = it
                break
        if best:
            break

    # 2) 유사도 매칭
    if not best and items:
        def _best_score_for_item(d: dict) -> float:
            cands = _candidate_strings_from_item(d)
            scores = []
            for s in cands:
                ns = _norm(s)
                score = max(difflib.SequenceMatcher(None, ns, t).ratio() for t in targets)
                scores.append(score)
            return max(scores) if scores else 0.0

        scored = [(it, _best_score_for_item(it)) for it in items]
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored and scored[0][1] >= 0.55:
            best = scored[0][0]

    if not best:
        return {}

    # ✅ not_to_do / Not_to__do 둘 다 채워서 템플릿 호환
    val_not_to_do = best.get("not_to_do") or best.get("Not_to__do")
    return {
        "title": best.get("title") or best.get("Title") or best.get("_key") or stain_name,
        "Washing_Steps": best.get("Washing_Steps"),
        "detail": best.get("detail"),
        "tip": best.get("tip"),
        "not_to_do": val_not_to_do,
        "Not_to__do": val_not_to_do,
        "Other_Information": best.get("Other_Information") or best.get("other_information"),
    }


# ------- 세탁 기호 → 가이드(설명) -------------------------------------------
def _norm_txt(s: str) -> str:
    """공백/특수문자 제거 + 소문자. (한글은 소문자 영향 X)"""
    return re.sub(r"[\s\W_]+", "", (s or "").lower())

def _iter_def_items(defs_obj):
    """
    washing_symbol.json을 (key, meta) 형태의 이터레이터로 통일.
    - dict: key -> meta
    - list : meta 내 'label' 또는 'id'를 key로 사용
    """
    if isinstance(defs_obj, dict):
        for k, v in defs_obj.items():
            yield k, v or {}
    elif isinstance(defs_obj, list):
        for item in defs_obj:
            item = item or {}
            key = item.get("label") or item.get("id")
            if key:
                yield key, item

def _match_def_by_keyword(free_label: str, defs_obj):
    """
    자유 텍스트(예: '드라이클리닝', '다림질')를 washing_symbol.json 항목과 퍼지 매칭.
    - 1순위: key 완전 일치
    - 2순위: name/keywords 포함 관계(양방향) 매칭
    - 3순위: 없으면 None
    """
    if not free_label:
        return None

    labn = _norm_txt(free_label)
    best = None

    # 1) key 완전 일치
    if isinstance(defs_obj, dict) and free_label in defs_obj:
        return defs_obj[free_label] or {}

    # 2) name / keywords 기반 포함 매칭
    for key, meta in _iter_def_items(defs_obj):
        name = (meta.get("name") or key or "")
        name_n = _norm_txt(name)
        if labn and (labn in name_n or name_n in labn):
            best = meta
            break

        for kw in (meta.get("keywords") or []):
            kwn = _norm_txt(kw)
            if labn and (labn in kwn or kwn in labn):
                best = meta
                break
        if best:
            break

    return best

def _symbols_to_guides_fuzzy(labels, defs_obj):
    """
    기호 이름 배열 -> [ {label,name,description}, ... ]
    자유 텍스트도 정의의 keywords/name과 매칭해 description을 찾아준다.
    """
    guides = []
    for lab in labels or []:
        meta = None

        # dict형 정의에서 key 직매칭
        if isinstance(defs_obj, dict) and lab in defs_obj:
            meta = defs_obj.get(lab) or {}

        # 퍼지 매칭
        if not meta:
            meta = _match_def_by_keyword(lab, defs_obj) or {}

        name = meta.get("name") or lab
        desc = meta.get("description") or ""
        guides.append({"label": lab, "name": name, "description": desc})
    return guides


# ------- 기호 설명 중복/쌍(일반/약하게) 병합 -------------------------------
def _collapse_normal_gentle_key(desc: str) -> str:
    """설명에서 '일반/약하게 + (세탁|드라이클리닝|클리닝)' 부분을 공통키로 정규화."""
    if not desc:
        return ""
    s = re.sub(r"\s+", " ", desc)
    s = re.sub(r"\b일반\s+(세탁|드라이클리닝|클리닝)", r"\1", s)
    s = re.sub(r"\b약하게\s+(세탁|드라이클리닝|클리닝)", r"\1", s)
    return s.strip()

def _dedupe_and_collapse_guides(guides, prefer_gentle=True):
    """
    1) (name|label, description) 기준 완전 동일 항목 제거
    2) '일반/약하게 + (세탁|드라이클리닝|클리닝)' 변형은 하나로 병합 (약하게 우선)
    """
    # 1) 완전 중복 제거
    uniq, seen = [], set()
    for g in guides or []:
        key = ((g.get("name") or g.get("label") or ""), g.get("description") or "")
        if key in seen:
            continue
        seen.add(key)
        uniq.append(g)

    # 2) 일반/약하게 병합
    pick_by_base = {}
    order_keys = []  # 출력 시 원래 순서 보존
    for g in uniq:
        desc = g.get("description") or ""
        base = _collapse_normal_gentle_key(desc)
        if not base or base == desc:
            k = ("__self__", desc)
        else:
            k = ("__base__", base)

        if k not in pick_by_base:
            pick_by_base[k] = g
            order_keys.append(k)
        else:
            cur = pick_by_base[k]
            cur_is_gentle = "약하게" in (cur.get("description") or "")
            new_is_gentle = "약하게" in desc
            if prefer_gentle and (new_is_gentle and not cur_is_gentle):
                pick_by_base[k] = g

    return [pick_by_base[k] for k in order_keys]


# ---- 메인 뷰 ---------------------------------------------------------------
@require_http_methods(["GET", "POST"])
def guide_from_result(request):
    """
    결과 화면(result.html)에서 넘어온 값(material / stains[] / symbols[])을 기반으로
    blackup.json / persil_v2.json / washing_symbol.json을 조회하여
    laundry-info.html로 가이드를 렌더.
    - POST 값 우선, 없으면 세션 값 폴백.
    """
    # 1) 입력값 수집
    material = request.POST.get("material") or request.session.get("material", "")

    stains = (
        request.POST.getlist("stains")
        or request.POST.getlist("stains[]")
        or request.session.get("stains", [])
    )
    # 리스트 표준화 + 빈 문자열 제거
    if isinstance(stains, str):
        stains = [stains]
    stains = [s for s in stains if s and str(s).strip()]

    symbols = (
        request.POST.getlist("symbols")
        or request.POST.getlist("symbols[]")
        or request.session.get("symbol_labels", [])
    )

    if not (material or stains or symbols):
        return redirect("result")

    # 2) JSON/정의 로드
    material_json = _load_json("blackup.json")
    stain_json    = _load_json("persil_v2.json")
    washing_defs  = U.load_washing_definitions()  # 런타임 로드(모듈 상단 X)

    # 3) 가이드 구성
    material_guide = _material_guide_from_json(material, material_json)
    stain_guide    = _stain_guide_from_json(stains[0] if stains else "", stain_json)
    symbol_guides  = _symbols_to_guides_fuzzy(symbols, washing_defs)

    # ✅ 중복 제거 + 일반/약하게 병합 적용
    symbol_guides  = _dedupe_and_collapse_guides(symbol_guides)

    # 4) 템플릿 호환: 문자열 설명 리스트도 함께 제공
    symbol_descs = [
        (g.get("description") or g.get("name") or g.get("label"))
        for g in symbol_guides
        if (g.get("description") or g.get("name") or g.get("label"))
    ]

    # 5) 상단 요약
    top_summary = _make_summary(material_guide, stain_guide, symbol_guides)
    summary = apply_stain_steps_summary(top_summary, stain_guide)

    # ✅ 피해야 하는 세탁법(not_to_do) 3개로 제한하여 템플릿에 전달
    stain_guide_limited = dict(stain_guide)  # 얕은 복사
    for key in ("not_to_do", "Not_to__do"):
        lst = stain_guide_limited.get(key) or []
        if isinstance(lst, list):
            stain_guide_limited[key] = lst[:2]

    # 6) 렌더
    ctx = {
        "material": material_guide,
        "stain": stain_guide_limited,  # ← 제한된 버전 사용
        "symbol_guides": symbol_guides,
        "symbols": symbol_descs,
        "info": {"material": material, "stains": " / ".join(stains) if stains else ""},
        "materials": [material] if material else [],
        "stains": stains,
        "summary": summary,
    }
    return render(request, "laundry_manager/laundry-info.html", ctx)
