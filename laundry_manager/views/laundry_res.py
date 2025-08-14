# 인식된 정보 받아오기 / json 파일 매칭 / 세탁 정보 출력
import os, json, re
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

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
    # 리스트면 첫 항목
    if isinstance(text, list):
        text = text[0] if text else ""
    # 딕셔너리면 첫 value
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

    # 기호로 건조 요약 추론
    labels = {g.get("label") for g in (symbol_guides or [])}
    dry_summary = None
    if "do_not_machine_dry" in labels:
        dry_summary = "건조기 사용 금지"

    stain_text = stain_guide.get("Washing_Steps") or stain_guide.get("detail")
    stain_summary = _first_line(stain_text)

    return {
        "wash": wash_summary or None,
        "dry": dry_summary,
        "stain": stain_summary or None,
    }


def _material_guide_from_json(material_name: str, material_json: dict) -> dict:
    """
    blackup.json 가정 스키마:
    {'material_washing_tips': [{material, description, warning}, ...]}
    """
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


# ------- 얼룩 매칭(한글/영문, 부분 포함 허용) ---------------------------------
def _norm(s: str) -> str:
    """공백/구두점 제거 + 소문자 → 비교용 정규화"""
    return re.sub(r"[\s\W_]+", "", (s or "").lower())


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
        # 대표 타이틀류
        for k in ["title", "Title", "name", "Name", "ko", "kr", "korean", "slug", "_key"]:
            v = item.get(k)
            if v:
                cands.append(str(v))
        # 배열형 키워드/별칭류
        for k in ["aliases", "keywords", "tags"]:
            for v in item.get(k) or []:
                cands.append(str(v))
        return cands

    return []


def _stain_guide_from_json(stain_name: str, stain_json) -> dict:
    """
    title/aliases/keywords 문자열에 '입력 얼룩명'이 포함되면 매칭(정규화 비교).
    - dict 항목 우선 매칭
    - dict가 없고 문자열만 매칭되면 제목만 채운 최소 가이드를 반환
    """
    if not stain_name:
        return {}

    target_norm = _norm(stain_name)

    # 순회 리스트 표준화
    items = []
    if isinstance(stain_json, list):
        items = stain_json
    elif isinstance(stain_json, dict):
        for k, v in stain_json.items():
            if isinstance(v, dict):
                v = {"_key": k, **v}
            items.append(v)

    best = None            # dict로 매칭된 최선
    provisional_title = "" # 문자열로만 매칭되었을 때 제목 보관

    for it in items:
        cands = _candidate_strings_from_item(it)
        for s in cands:
            if target_norm in _norm(s):
                if isinstance(it, dict):
                    best = it
                    break
                else:
                    # 문자열/리스트에서 찾은 경우: 제목 후보만 확보
                    provisional_title = s
        if best:
            break

    if not best:
        if provisional_title:
            # 최소 가이드 반환(제목만)
            return {
                "title": provisional_title,
                "Washing_Steps": None,
                "detail": None,
                "tip": None,
                "Not_to__do": None,
                "Other_Information": None,
            }
        return {}

    return {
        "title": best.get("title") or best.get("Title") or best.get("_key") or stain_name,
        "Washing_Steps": best.get("Washing_Steps"),
        "detail": best.get("detail"),
        "tip": best.get("tip"),
        "Not_to__do": best.get("Not_to__do") or best.get("not_to_do"),
        "Other_Information": best.get("Other_Information") or best.get("other_information"),
    }


def _symbols_to_guides_safe(labels, defs_obj):
    """
    utils.symbols_to_guides가 없거나 실패해도 동작하도록 안전 폴백.
    """
    fn = getattr(U, "symbols_to_guides", None)
    if callable(fn):
        try:
            return fn(labels, defs_obj) or []
        except Exception as e:
            print("[dev] utils.symbols_to_guides 실행 오류:", e)

    guides = []
    if isinstance(defs_obj, dict):
        for lab in labels or []:
            meta = (defs_obj.get(lab) or {})
            name = meta.get("name") or lab
            desc = meta.get("description") or ""
            guides.append({"label": lab, "name": name, "description": desc})
    elif isinstance(defs_obj, list):
        by_label = {}
        for item in defs_obj or []:
            key = (item or {}).get("label") or (item or {}).get("id")
            if key:
                by_label[key] = item
        for lab in labels or []:
            meta = (by_label.get(lab) or {})
            name = meta.get("name") or lab
            desc = meta.get("description") or ""
            guides.append({"label": lab, "name": name, "description": desc})
    else:
        for lab in labels or []:
            guides.append({"label": lab, "name": lab, "description": ""})
    return guides


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
    symbols = (
        request.POST.getlist("symbols")
        or request.POST.getlist("symbols[]")
        or request.session.get("symbol_labels", [])
    )

    if not (material or stains or symbols):
        return redirect("result")

    # 2) JSON/정의 로드
    material_json = _load_json("blackup.json")
    stain_json = _load_json("persil_v2.json")
    washing_defs = U.load_washing_definitions()  # 런타임 로드(모듈 상단 X)

    # 3) 가이드 구성
    material_guide = _material_guide_from_json(material, material_json)
    stain_guide = _stain_guide_from_json(stains[0] if stains else "", stain_json)
    symbol_guides = _symbols_to_guides_safe(symbols, washing_defs)

    # 템플릿 호환: 문자열 설명 리스트도 함께 제공
    symbol_descs = [
        (g.get("description") or g.get("name") or g.get("label"))
        for g in symbol_guides
        if (g.get("description") or g.get("name") or g.get("label"))
    ]

    # 4) 상단 요약
    summary = _make_summary(material_guide, stain_guide, symbol_guides)

    # 5) 렌더
    ctx = {
        "material": material_guide,
        "stain": stain_guide,
        "symbol_guides": symbol_guides,
        "symbols": symbol_descs,  # 문자열 설명 배열(템플릿 호환)
        "info": {
            "material": material,
            "stains": " / ".join(stains) if stains else "",
        },
        "materials": [material] if material else [],
        "stains": stains,
        "summary": summary,
    }
    return render(request, "laundry_manager/laundry-info.html", ctx)
