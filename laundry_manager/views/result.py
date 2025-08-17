# laundry_manager/views/result.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output
from ..models import LaundryHistory
from django.conf import settings
import os
import json

JSON_FILE = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "stains.json")
# 얼룩 유형 json에서 추출
def load_stain_titles():
    json_file = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "persil_v2.json")
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    # title 필드만 추출
    return [entry.get("title", "") for entry in data if "title" in entry]

def _load_stain_titles():
    json_file = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "persil_v2.json")
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    titles = []

    # 루트가 배열인 경우
    if isinstance(data, list):
        for e in data:
            if isinstance(e, str):
                titles.append(e.strip())
            elif isinstance(e, dict) and e.get("title"):
                titles.append(str(e["title"]).strip())

    # 루트가 객체인 경우: 흔한 키 후보 탐색
    elif isinstance(data, dict):
        for key in ("stains", "items", "data", "list"):
            if isinstance(data.get(key), list):
                for e in data[key]:
                    if isinstance(e, str):
                        titles.append(e.strip())
                    elif isinstance(e, dict) and e.get("title"):
                        titles.append(str(e["title"]).strip())
                break

    # 중복 제거(순서 유지)
    seen = set()
    uniq = []
    for t in titles:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq

def laundry_upload_page(request):
    stain_titles = _load_stain_titles()
    return render(request, "laundry_manager/laundry-upload.html", {
        "stain_titles": stain_titles,
    })
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

    # ✅ 로그인 시 History 1건 보장
    # history = _ensure_history(
    #     request,
    #     materials=[material] if material else [],
    #     stains=stains,
    #     symbols=symbols,
    # )

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
        'symbols': symbols,
        'instructions': instructions,
        # 'history': history,   # 👈 템플릿에서 hidden/input/링크에 사용
    })
