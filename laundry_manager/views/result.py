# laundry_manager/views/result.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output
from ..models import LaundryHistory
from django.conf import settings
import json, re, os
from django.contrib import messages
from ..services.modal_data import load_material_items, load_stain_titles
MATERIALS_JSON = os.path.join(
    settings.BASE_DIR, "laundry_manager", "json_data", "blackup.json"
)
STAINS_JSON = os.path.join(
    settings.BASE_DIR, "laundry_manager", "json_data", "persil_v2.json"
)


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

# @login_required
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
    texts = request.session.get('recognized_texts', [])
    definition = request.session.get('symbol_definition', '')
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])
    symbols = request.session.get('symbols', [])

    if not texts:
        texts = load_latest_recognized_texts_from_output()

    instructions = analyze_texts(texts)

    # ▼ 모달용 옵션 (소재=material raw, 얼룩=title)
    material_items = load_material_items()                 # [{kor, eng, raw, ...}]
    stain_titles   = load_stain_titles()    
    material_option_labels = [it["raw"] for it in material_items]  # "면(Cotton)" 형식
    stain_option_labels = load_stain_titles()              # ["혈흔", "커피와 차 얼룩", ...]

    print("[RESULT] materials_json:", MATERIALS_JSON, "exists:", os.path.exists(MATERIALS_JSON), "count:", len(material_items))
    print("[RESULT] stains_json   :", STAINS_JSON, "exists:", os.path.exists(STAINS_JSON), "count:", len(stain_titles))

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
        'symbols': symbols,
        'instructions': instructions,

        "material_items": material_items,
        "stain_titles": stain_titles,
    })

