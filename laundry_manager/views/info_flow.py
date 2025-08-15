import os, json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from ..functions.recommend import laundry_recommend, get_material_guide, get_stain_guide
from ..functions.info import first_info, final_info
from django.conf import settings

from ..models import LaundryHistory
from ..functions.recommend import laundry_recommend
from ..functions.result import format_result

# 맨 위 import에 몇 개 추가
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

# ===== 여기부터 새로 추가 =====
@require_POST
def update_selection_view(request):
    """
    모달에서 보내는 값으로 가이드 재계산해서 부분 HTML 반환.
    요청 파라미터:
      - field: 'materials' | 'stains'
      - value: 사용자가 수정한 문자열 (쉼표 허용: '면, 폴리에스터')
      - materials[]: 현재 선택(리스트) — field가 stains일 때 기준값으로 사용
      - stains[]: 현재 선택(리스트) — field가 materials일 때 기준값으로 사용
      - symbols[]: 현재 선택(리스트) — 항상 필요
      - history_id: 선택(로그인+저장 시)
    """
    field = request.POST.get("field")
    if field not in ("materials", "stains"):
        return HttpResponseBadRequest("invalid field")

    # 현재 상태 수신
    materials = request.POST.getlist("materials[]")
    stains = request.POST.getlist("stains[]")
    symbols = request.POST.getlist("symbols[]")

    # 모달에서 변경된 값 적용
    raw_value = (request.POST.get("value") or "").strip()
    if not raw_value:
        return HttpResponseBadRequest("empty value")

    if field == "materials":
        # 쉼표로 여러 개 입력 허용
        materials = [x.strip() for x in raw_value.split(",") if x.strip()]
    else:  # field == "stains"
        # 단일 대표 얼룩만 사용(필요 시 쉼표 분리로 복수 처리 가능)
        stains = [x.strip() for x in raw_value.split(",") if x.strip()]
        if not stains:
            stains = [""]  # 빈 문자열로 안전 처리

    # 추천 재계산
    material_json = load_json('blackup.json')
    stain_json = load_json('persil_v2.json')
    symbol_json = load_json('washing_symbol.json')

    info = {
        "material": ", ".join(materials),
        "stains": stains[0] if stains else "",
        "symbols": symbols,
    }
    guides = laundry_recommend(info, material_json, stain_json, symbol_json)

    # 로그인 + history_id가 있으면 최신 추천을 DB에 반영(선택)
    history_id = request.POST.get("history_id")
    if request.user.is_authenticated and history_id:
        try:
            lh = LaundryHistory.objects.get(pk=history_id, user=request.user)
            lh.materials = info["material"]
            lh.stains = info["stains"]
            lh.symbols = ", ".join(symbols)
            # 포맷팅 텍스트 저장
            lh.recommendation_result = format_result(guides)
            lh.save(update_fields=["materials", "stains", "symbols", "recommendation_result"])
        except LaundryHistory.DoesNotExist:
            pass

    # 부분 템플릿 렌더(가이드 카드 영역)
    # 없으면 만들어 주세요: templates/laundry_manager/partials/_recommendation.html
    html = render_to_string(
        "laundry_manager/partials/_recommendation.html",
        {
            "material": guides.get('material_guide'),
            "stain": guides.get("stain_guide"),
            "symbols": guides.get("symbol_guide"),
            "materials": materials,           # 페이지 상단 표시용
            "stains": info["stains"],         # 페이지 상단 표시용
        },
        request=request,
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "materials_text": info["material"],
        "stains_text": info["stains"],
    })
# ===== 새 코드 끝 =====




def load_json(filename):
    path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def laundry_result_view(request):
    if request.method == "POST":
        info = {
            "material": request.POST.get("material"),
            "stains": request.POST.get("stains"),
            "symbols": request.POST.getlist("symbols"),
        }
        material_json = load_json('blackup.json')
        stain_json = load_json('persil_v2.json')
        symbol_json = load_json('washing_symbol.json')
        guides = laundry_recommend(info, material_json, stain_json, symbol_json)
        return render(request, "laundry_manager/laundry_info.html", {
            "material": guides.get('material_guide'),
            "stain": guides.get("stain_guide"),
            "symbols": guides.get("symbol_guide"),
            "info": info,
            "materials": [info["material"]],
            "stains": info["stains"],
        })
    return redirect("laundry-upload")

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
        # 1. 추천 결과 텍스트 생성
        material_json = load_json('blackup.json')
        stain_json = load_json('persil_v2.json')
        symbol_json = load_json('washing_symbol.json')

        stain_name = final_result.get("stain") or (manual_stain or "")
        guides = laundry_recommend(
            {"material": ", ".join(final_result.get("materials", [])),
             "stains": stain_name,                     
             "symbols": final_result.get("symbols", [])},
            material_json, stain_json, symbol_json
        )
        recommendation_text = format_result(guides)

        # 2. 로그인 상태이면 DB에 저장
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
            "material" : guides.get('material_guide'),
            "stain": guides.get('stain_guide'),
            "info": {
                'stains': stain_name,
                'material': ", ".join(final_result.get("materials", []))
            }
        })