# laundry_manager/views/result.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output
from ..models import LaundryHistory
from django.conf import settings
import json, re, os
from django.contrib import messages
from ..services.modal_data import load_material_items, load_stain_titles
import logging
logger = logging.getLogger(__name__)


MATERIALS_JSON = os.path.join(
    settings.BASE_DIR, "laundry_manager", "json_data", "blackup.json"
)
STAINS_JSON = os.path.join(
    settings.BASE_DIR, "laundry_manager", "json_data", "persil_v2.json"
)
WASHING_SYMBOL_JSON = os.path.join(
    settings.BASE_DIR, "laundry_manager", "json_data", "washing_symbol.json"
)

DEFAULT_SYMBOL_ID_WHITELIST = {
    "wash_40_normal",
    "wash_30_normal",
    "wash_30_gentle",
    "wash_30_gentle_neutral_detergent",
    "do_not_wash",
    "do_not_bleach",
    "bleach_any",
    "iron_160_normal",
    "iron_120_normal",
    "do_not_iron",
    "dry_clean_perchloroethylene_normal",
    "do_not_dry_clean",
    "do_not_machine_dry",
    "natural_dry_hang_shade",
    "do_not_spin",
}

def _load_stain_titles():
    # (네가 이미 넣은 재귀 버전 써도 됨)
    try:
        with open(STAINS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and k.lower() == "title" and isinstance(v, str):
                    yield v.strip()
                else:
                    yield from walk(v)
        elif isinstance(node, list):
            for it in node: 
                yield from walk(it)

    seen, out = set(), []
    for t in walk(data):
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out

def _load_material_items():
    """
    materials_washing.json 에서 소재 chips용 목록을 빼옵니다.
    반환: [{kor, eng, raw, description, warning}]
    """
    try:
        with open(MATERIALS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("[MATERIAL] load error:", e)
        return []

    items = data.get("material_washing_tips") or []
    result = []
    seen = set()

    for row in items:
        raw = (row.get("material") or "").strip()
        if not raw:
            continue

        # "면(Cotton)" → kor="면", eng="Cotton"
        m = re.match(r"^\s*([^()]+?)\s*(?:\(([^)]+)\))?\s*$", raw)
        kor = (m.group(1).strip() if m else raw) if raw else ""
        eng = m.group(2).strip() if (m and m.group(2)) else ""

        if kor in seen:
            continue
        seen.add(kor)

        result.append({
            "kor": kor,
            "eng": eng,
            "raw": raw,
            "description": (row.get("description") or "").strip(),
            "warning": (row.get("warning") or "").strip(),
        })

    return result

def _load_symbol_items_from_json():
    try:
        with open(WASHING_SYMBOL_JSON, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        logger.error("[SYM] load error: %s", e)
        return []
    items = []
    if isinstance(raw, list):
        for it in raw:
            if isinstance(it, dict) and it.get("id"):
                items.append({
                    "id": it["id"].strip(),
                    "category": (it.get("category") or "").strip(),
                    "label": (it.get("keyword") or it["id"]).strip(),
                    "desc": (it.get("description") or "").strip(),
                })
    # dedup
    seen, out = set(), []
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"]); out.append(it)
    return out

# settings에 문자열로 넣었을 때도 안전하게 처리
def _allowed_symbol_ids():
    ids = getattr(settings, "SYMBOL_ID_WHITELIST", DEFAULT_SYMBOL_ID_WHITELIST)
    if isinstance(ids, str):
        ids = [x.strip() for x in ids.split(",") if x.strip()]
    return set(ids)

def _filter_symbol_items(items, allowed_ids):
    return [it for it in items if it.get("id") in allowed_ids]

def _debug_symbols_snapshot(path: str):
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    head = ""; err = ""
    try:
        if exists:
            with open(path, "r", encoding="utf-8") as f:
                head = f.read(300)
    except Exception as e:
        err = repr(e)
    return {"path": path, "exists": exists, "size": size, "head": head, "err": err}

def _load_symbol_items_from_json():
    try:
        with open(WASHING_SYMBOL_JSON, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        logger.error("[SYM] load error: %s", e)
        return []
    items = []
    if isinstance(raw, list):
        for it in raw:
            if isinstance(it, dict) and it.get("id"):
                items.append({
                    "id": it["id"].strip(),
                    "category": (it.get("category") or "").strip(),
                    "label": (it.get("keyword") or it["id"]).strip(),
                    "desc": (it.get("description") or "").strip(),
                })
    # dedup
    seen, out = set(), []
    for it in items:
        if it["id"] in seen: continue
        seen.add(it["id"]); out.append(it)
    return out

# @login_requireds
def laundry_upload_page(request):
    # stains
    stain_titles = load_stain_titles()

    # materials
    materials = load_material_items()
    mat_exists = os.path.exists(MATERIALS_JSON)

    # 디버그 로그(원하면 주석 처리)
    print(f"[UPLOAD] stains={len(stain_titles)} materials={len(materials)} mat_file_exist={mat_exists}")

    if not mat_exists or not materials:
        messages.warning(request, f"소재 데이터 개수={len(materials)} / 파일 존재={mat_exists}")

    ctx = {
        "stain_titles": stain_titles,
        "materials": materials,
        "debug_info": {
            "stain_count": len(stain_titles),
            "material_count": len(materials),
            "materials_json": MATERIALS_JSON,
            "materials_exists": mat_exists,
        }
    }
    return render(request, "laundry_manager/laundry-upload.html", ctx)

######

def _ensure_history(request, materials, stains, symbols):
    """로그인 시 세션에 history_id 없으면 하나 만들고 반환."""
    if not request.user.is_authenticated:
        return None
    hid = request.session.get("history_id")
    history = None
    if hid:
        try:
            history = LaundryHistory.objects.get(pk=hid, user=request.user)
        except LaundryHistory.DoesNotExist:
            history = None
    if not history:
        history = LaundryHistory.objects.create(
            user=request.user,
            materials=", ".join(materials) if materials else "",
            stains=(stains[0] if stains else ""),
            symbols=", ".join(symbols) if symbols else "",
        )
        request.session["history_id"] = history.id
    return history

def result_view(request):
    request.session["result_source"] = "legacy"
    debug_flag = (request.GET.get("debug") == "1")

    texts = request.session.get('recognized_texts', [])
    definition = request.session.get('symbol_definition', '')
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])
    # 세션 저장된 symbols(원본)
    symbols_in_session = request.session.get('symbols', []) or []

    if not texts:
        texts = load_latest_recognized_texts_from_output()
    instructions = analyze_texts(texts)

    # ── 심볼 로드 + 화이트리스트 필터 ─────────────────────────
    sym_dbg = _debug_symbols_snapshot(WASHING_SYMBOL_JSON)      # 파일 상태
    symbol_items_all = _load_symbol_items_from_json()           # 전체
    allowed_ids = _allowed_symbol_ids()
    symbol_items = _filter_symbol_items(symbol_items_all, allowed_ids)  # ★필터된 것만

    # 화면 active: 세션 값도 허용 id로 정리
    symbols_for_view = [sid for sid in symbols_in_session if sid in allowed_ids]

    # 선택 라벨 계산(필터된 목록 기준)
    id2label = {it["id"]: it["label"] for it in symbol_items}
    selected_symbol_labels = [id2label.get(x, x) for x in symbols_for_view]

    # 디버그 로그(전/후 카운트)
    logger.info("[SYM.FILTER] before=%d after=%d allowed=%s",
                len(symbol_items_all), len(symbol_items), sorted(list(allowed_ids)))
    if not symbol_items:
        messages.warning(request, f"[SYM] empty. exists={sym_dbg['exists']} size={sym_dbg['size']}")

    # ── 나머지 모달 데이터 ───────────────────────────────────
    material_items = load_material_items()
    stain_titles   = load_stain_titles()

    # 인식된 키워드 보장
    rule_keywords = request.session.get("rule_keywords", [])
    if not rule_keywords:
        if isinstance(instructions, dict):
            rule_keywords = (instructions.get("rule_keywords")
                             or instructions.get("keywords") or [])
        elif isinstance(instructions, list):
            rule_keywords = instructions
    if isinstance(rule_keywords, str):
        rule_keywords = [rule_keywords]
    rule_keywords = [str(x) for x in rule_keywords]

    print("[RESULT] materials_json:", MATERIALS_JSON, "exists:", os.path.exists(MATERIALS_JSON), "count:", len(material_items))
    print("[RESULT] stains_json   :", STAINS_JSON, "exists:", os.path.exists(STAINS_JSON), "count:", len(stain_titles))
    print("[RESULT] symbols_json  :", WASHING_SYMBOL_JSON, "exists:", sym_dbg["exists"],
          "before:", len(symbol_items_all), "after:", len(symbol_items))

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,

        'materials': [material] if material else [],
        'stains': stains,

        # ★ 허용된 것만 active 처리
        'symbols': symbols_for_view,

        # ★ 칩으로 보여줄 목록(허용된 것만)
        'symbol_items': symbol_items,

        'selected_symbol_labels': selected_symbol_labels,
        'instructions': instructions,
        'rule_keywords': rule_keywords,

        'material_items': material_items,
        'stain_titles': stain_titles,

        # 디버그
        'DEBUG_FLAG': debug_flag,
        'debug_symbols': {**sym_dbg,
                          'before_count': len(symbol_items_all),
                          'after_count': len(symbol_items),
                          'first3': symbol_items[:3]},
    })
