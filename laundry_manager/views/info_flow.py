# views/info_flow.py
import os
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.decorators import login_required

from ..functions.recommend import laundry_recommend, get_material_guide, get_stain_guide
from ..functions.info import first_info, final_info
from ..functions.result import format_result
from ..models import LaundryHistory


# ─────────────────────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────────────────────
def _clean_str(s):
    return (s or "").strip()

def _as_list_one(s):
    """단일 선택값을 템플릿용 리스트로 변환 (없으면 [])"""
    s = _clean_str(s)
    return [s] if s else []

def load_json(filename):
    path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@login_required
def guide_from_result(request):
    # 1) history_id 우선
    hid = request.GET.get("history_id") or request.session.get("history_id")
    lh = None
    if hid:
        lh = get_object_or_404(LaundryHistory, pk=hid, user=request.user)

    # 2) info 구성: DB → 세션 → 기본
    material = (lh.materials if lh else (request.session.get("material") or "")).strip()
    stains   = (lh.stains   if lh else (request.session.get("stains") or [""])[0]).strip()
    symbols  = (lh.symbols.split(",") if (lh and lh.symbols) else request.session.get("symbols", []))

    info = {"material": material, "stains": stains, "symbols": [s.strip() for s in symbols if s and s.strip()]}

    # 3) 추천 계산
    material_json = load_json('blackup.json')
    stain_json    = load_json('persil_v2.json')
    symbol_json   = load_json('washing_symbol.json')
    guides = laundry_recommend(info, material_json, stain_json, symbol_json)

    return render(request, "laundry_manager/laundry_info.html", {
        "material": guides.get('material_guide'),
        "stain": guides.get("stain_guide"),
        "symbols": guides.get("symbol_guide"),
        "info": info,                         # ✅ 템플릿 제목/본문에서 이 값을 우선 사용
        "materials": [material] if material else [],
        "stains": stains,
        "history": lh,
        # summary 필요하면 여기서 함께 계산해 넣으세요
    })

# ─────────────────────────────────────────────────────────────────────────────
# 선택(모달) 수정 → 가이드 재계산 (AJAX)
# ─────────────────────────────────────────────────────────────────────────────
@require_POST
def update_selection_view(request):
    """
    모달에서 보내는 값으로 가이드 재계산해서 부분 HTML 반환.
    요청 파라미터:
      - field: 'materials' | 'stains'
      - value: 사용자가 수정한 문자열 (단일 값 권장, 쉼표 들어오면 첫 값만 사용)
      - materials[]: 현재 선택(리스트)
      - stains[]: 현재 선택(리스트)
      - symbols[]: 현재 선택(리스트)
      - history_id: 선택(로그인+저장 시)
    """
    field = request.POST.get("field")
    if field not in ("materials", "stains"):
        return HttpResponseBadRequest("invalid field")

    # 현재 상태 수신
    materials = request.POST.getlist("materials[]")
    stains = request.POST.getlist("stains[]")
    symbols = request.POST.getlist("symbols[]")

    # 변경 단일 값 적용 (쉼표가 온 경우 첫 토큰만)
    raw_value = _clean_str(request.POST.get("value"))
    if not raw_value:
        return HttpResponseBadRequest("empty value")
    single_value = _clean_str(raw_value.split(",")[0])

    if field == "materials":
        materials = _as_list_one(single_value)
    else:  # "stains"
        stains = _as_list_one(single_value)

    # 추천 재계산
    material_json = load_json('blackup.json')
    stain_json = load_json('persil_v2.json')
    symbol_json = load_json('washing_symbol.json')

    info = {
        "material": ", ".join(materials),          # recommend 시그니처 유지
        "stains": stains[0] if stains else "",
        "symbols": symbols,
    }
    guides = laundry_recommend(info, material_json, stain_json, symbol_json)

    # 로그인 + history 저장 (선택)
    history_id = request.POST.get("history_id")
    if request.user.is_authenticated and history_id:
        try:
            lh = LaundryHistory.objects.get(pk=history_id, user=request.user)
            lh.materials = info["material"]
            lh.stains = info["stains"]
            lh.symbols = ", ".join(symbols)
            lh.recommendation_result = format_result(guides)
            lh.save(update_fields=["materials", "stains", "symbols", "recommendation_result"])
        except LaundryHistory.DoesNotExist:
            pass

    # 부분 템플릿 렌더
    html = render_to_string(
        "laundry_manager/partials/_recommendation.html",
        {
            "material": guides.get('material_guide'),
            "stain": guides.get("stain_guide"),
            "symbols": guides.get("symbol_guide"),
            "materials": materials,            # 상단 표시용(리스트)
            "stains": info["stains"],          # 상단 표시용(문자열)
        },
        request=request,
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "materials_text": info["material"],   # ex) "니트"
        "stains_text": info["stains"],        # ex) "김치"
    })


# ─────────────────────────────────────────────────────────────────────────────
# 업로드 → 가이드 화면
# ─────────────────────────────────────────────────────────────────────────────
def laundry_result_view(request):
    if request.method == "POST":
        # 업로드 폼에서 단일 값으로 넘어옴
        material = _clean_str(request.POST.get("material"))     # ex: "니트"
        stain = _clean_str(request.POST.get("stains"))          # ex: "김치"
        symbols = request.POST.getlist("symbols") or []

        info = {
            "material": material,
            "stains": stain,
            "symbols": symbols,
        }

        material_json = load_json('blackup.json')
        stain_json = load_json('persil_v2.json')
        symbol_json = load_json('washing_symbol.json')
        guides = laundry_recommend(info, material_json, stain_json, symbol_json)

        # 다음 단계용 세션 저장
        request.session["material"] = material
        request.session["stains"] = _as_list_one(stain)
        request.session["symbols"] = symbols

        return render(request, "laundry_manager/laundry_info.html", {
            "material": guides.get('material_guide'),
            "stain": guides.get("stain_guide"),
            "symbols": guides.get("symbol_guide"),

            # 화면 표시용
            "info": info,                           # {'material': '니트', 'stains': '김치', ...}
            "materials": _as_list_one(material),    # 타이틀/상단 표시에서 join 사용 가능
            "stains": stain,                        # 해당 템플릿이 문자열을 기대한다면 유지
        })
    return redirect("laundry-upload")


# ─────────────────────────────────────────────────────────────────────────────
# 세션 기반 가이드 화면(기존 흐름 유지)
# ─────────────────────────────────────────────────────────────────────────────
def laundry_info_view1(request):
    material_name = request.session.get('material', '')
    stains = request.session.get('stains', [])
    material_info = get_material_guide(material_name) if material_name else {}
    stain_info = get_stain_guide(stains[0]) if stains else {}
    return render(request, 'laundry_manager/laundry_info.html', {
        'material_name': material_name,
        'stains': stains,
        'material': material_info,
        'stain': stain_info,
        'symbols': request.session.get('symbols', []),
        'info': {'material': material_name, 'stains': " / ".join(stains)}
    })


# ─────────────────────────────────────────────────────────────────────────────
# 1단계: 파일 분석 결과 → result.html
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def first_info_view(request):
    if request.method == "POST":
        filename = request.POST.get("filename")
        selected_materials = request.POST.getlist("materials[]")
        selected_stains = request.POST.getlist("stains[]")
        result = first_info(filename=filename, selected_materials=selected_materials, selected_stains=selected_stains)
        return render(request, "laundry_manager/result.html", {
            "materials": result.get("materials", []),
            "symbols": result.get("symbols", []),
            "stains": result.get("stains", []),
            "filename": filename,
        })
    return render(request, "laundry_manager/result.html")


# ─────────────────────────────────────────────────────────────────────────────
# 2단계: 수동 보정 반영 → 최종 가이드 + 저장
# ─────────────────────────────────────────────────────────────────────────────
@csrf_exempt
def final_info_view(request):
    if request.method == "POST":
        filename = request.POST.get("filename")
        manual_materials = request.POST.getlist("manual_materials[]")
        manual_symbols = request.POST.getlist("manual_symbols[]")
        manual_stain = request.POST.get("manual_stain")

        first_result = first_info(filename=filename)
        final_result = final_info(first_info=first_result,
                                  manual_materials=manual_materials,
                                  manual_symbols=manual_symbols,
                                  manual_stain=manual_stain)

        # 추천 결과 텍스트 생성
        material_json = load_json('blackup.json')
        stain_json = load_json('persil_v2.json')
        symbol_json = load_json('washing_symbol.json')

        stain_name = final_result.get("stain") or (manual_stain or "")
        guides = laundry_recommend(
            {
                "material": ", ".join(final_result.get("materials", [])),
                "stains": stain_name,
                "symbols": final_result.get("symbols", []),
            },
            material_json, stain_json, symbol_json
        )
        recommendation_text = format_result(guides)

        # 로그인 상태이면 DB 저장
        if request.user.is_authenticated:
            LaundryHistory.objects.create(
                user=request.user,
                materials=', '.join(final_result.get("materials", [])),
                symbols=', '.join(final_result.get("symbols", [])),
                stains=stain_name,
                recommendation_result=recommendation_text
            )

        return render(request, "laundry_manager/laundry_info.html", {
            "materials": final_result.get("materials", []),
            "symbols": final_result.get("symbols", []),
            "stains": stain_name,
            "material_name": ", ".join(final_result.get("materials", [])),
            "material": guides.get('material_guide'),
            "stain": guides.get('stain_guide'),
            "info": {
                'stains': stain_name,
                'material': ", ".join(final_result.get("materials", []))
            }
        })
    # GET은 업로드 화면으로
    return redirect("laundry-upload")
