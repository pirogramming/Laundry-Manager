# laundry_manager/views/result.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output
from ..models import LaundryHistory
from django.conf import settings
import os
import json
from django.contrib import messages


def _load_stain_titles():
    json_file = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "persil_v2.json")

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("[UPLOAD] JSON load error:", e)
        return []

    def iter_titles(node):
        # 어디에 있어도 'title'을 뽑아내는 재귀 탐색
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and k.lower() == "title" and isinstance(v, str):
                    yield v.strip()
                else:
                    yield from iter_titles(v)
        elif isinstance(node, list):
            for item in node:
                yield from iter_titles(item)

    titles = list(iter_titles(data))

    # 중복 제거(순서 유지)
    seen, uniq = set(), []
    for t in titles:
        if t and t not in seen:
            seen.add(t); uniq.append(t)

    # 디버그: 루트 타입/키 출력
    root_info = type(data).__name__
    root_keys = list(data.keys())[:10] if isinstance(data, dict) else None
    print(f"[UPLOAD] root={root_info} keys={root_keys} titles_count={len(uniq)}")

    return uniq



def laundry_upload_page(request):
    json_file = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "persil_v2.json")

    # ---------- JSON 로드 ----------
    exists = os.path.exists(json_file)
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        messages.error(request, f"JSON 파일을 찾을 수 없음: {json_file}")
        print("[UPLOAD] FileNotFound:", json_file)
        data = []
    except json.JSONDecodeError as e:
        messages.error(request, f"JSON 파싱 오류: {e}")
        print("[UPLOAD] JSONDecodeError:", e)
        data = []

    # ---------- title 재귀 추출 ----------
    def iter_titles(node):
        """
        dict/list 어디에 있든 'title' 키를 전부 찾아서 yield.
        """
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and k.lower() == "title" and isinstance(v, str):
                    yield v.strip()
                else:
                    # 하위 구조 계속 탐색
                    yield from iter_titles(v)
        elif isinstance(node, list):
            for item in node:
                yield from iter_titles(item)

    titles = list(iter_titles(data))

    # ---------- 중복 제거(순서 유지) ----------
    seen, uniq = set(), []
    for t in titles:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)

    # ---------- 디버그/메시지 ----------
    print(f"[UPLOAD] JSON path exist?: {exists} titles_count: {len(uniq)}")
    if not exists or len(uniq) == 0:
        messages.warning(request, f"stain_titles 개수 = {len(uniq)} / 파일 존재 = {exists}")

    # ---------- 렌더 ----------
    ctx = {
        "stain_titles": uniq,
        "debug_info": {
            "json_path": json_file,
            "json_exists": exists,
            "count": len(uniq),
        },
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
