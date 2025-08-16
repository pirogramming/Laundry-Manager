# views/info_flow.py
import os
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404  
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
    # material = (lh.materials if lh else (request.session.get("material") or "")).strip()
    # stains   = (lh.stains   if lh else (request.session.get("stains") or [""])[0]).strip()
    # 세션에 최신이 있으면 세션 우선, 없으면 History 사용
    sess_mat = (request.session.get("material") or "").strip()
    sess_sts = request.session.get("stains") or []
    material = (sess_mat or (lh.materials if lh else "")).strip()
    stains   = ((sess_sts[0] if isinstance(sess_sts, list) and sess_sts else "")
                or (lh.stains if lh else "")).strip()
    symbols  = (lh.symbols.split(",") if (lh and lh.symbols) else request.session.get("symbols", []))

    info = {"material": material, "stains": stains, "symbols": [s.strip() for s in symbols if s and s.strip()]}

    # 3) 추천 계산
    material_json = load_json('blackup.json')
    stain_json    = load_json('persil_v2.json')
    symbol_json   = load_json('washing_symbol.json')
    guides = laundry_recommend(info, material_json, stain_json, symbol_json)

    return render(request, "laundry_manager/laundry-info.html", {
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
# views/info_flow.py

@require_POST
def update_selection_view(request):
    field = (request.POST.get("field") or "").strip().lower()
    raw_value = _clean_str(request.POST.get("value"))

    # 폼/세션 현재값 (폴백 겸 안전망)
    sess_mats = request.session.get("materials") or []
    sess_stns = request.session.get("stains") or []
    symbols   = request.POST.getlist("symbols[]") or (request.session.get("symbols") or [])

    materials = list(request.POST.getlist("materials[]") or sess_mats)
    stains    = list(request.POST.getlist("stains[]")    or sess_stns)

    if field == "both":
        # value='{"materials":["니트"],"stains":["커피"]}'
        try:
            obj = json.loads(raw_value or "{}")
        except Exception:
            obj = {}
        m = obj.get("materials") or []
        s = obj.get("stains") or []
        if isinstance(m, str): m = [m]
        if isinstance(s, str): s = [s]
        materials = [_clean_str(m[0])] if m else []
        stains    = [_clean_str(s[0])] if s else []

    elif field == "materials":
        if not raw_value:
            return HttpResponseBadRequest("empty value")
        materials = _as_list_one(raw_value.split(",")[0])
        # 변경하지 않은 얼룩은 세션값 유지
        stains = stains or sess_stns

    elif field == "stains":
        if not raw_value:
            return HttpResponseBadRequest("empty value")
        stains = _as_list_one(raw_value.split(",")[0])
        # 변경하지 않은 소재는 세션값 유지
        materials = materials or sess_mats

    else:
        return HttpResponseBadRequest("invalid field")

    # 세션 최신화
    request.session["material"]  = (materials[0] if materials else "")
    request.session["materials"] = materials
    request.session["stains"]    = stains
    request.session["symbols"]   = symbols
    request.session.modified     = True

    # 가이드 재계산
    material_json = load_json('blackup.json')
    stain_json    = load_json('persil_v2.json')
    symbol_json   = load_json('washing_symbol.json')

    info = {
        "material": ", ".join(materials),
        "stains":   (stains[0] if stains else ""),
        "symbols":  symbols,
    }
    guides = laundry_recommend(info, material_json, stain_json, symbol_json)

    # 로그인 + history 저장(있을 때)
    history_id = request.POST.get("history_id")
    if request.user.is_authenticated and history_id:
        try:
            lh = LaundryHistory.objects.get(pk=history_id, user=request.user)
            lh.materials = info["material"]
            lh.stains    = info["stains"]
            lh.symbols   = ", ".join(symbols)
            lh.recommendation_result = format_result(guides)
            lh.save(update_fields=["materials","stains","symbols","recommendation_result"])
        except LaundryHistory.DoesNotExist:
            pass

    # 부분 템플릿(있으면) 렌더
    html = render_to_string(
        "laundry_manager/partials/_recommendation.html",
        {
            "material": guides.get('material_guide'),
            "stain":    guides.get("stain_guide"),
            "symbols":  guides.get("symbol_guide"),
            "materials": materials,
            "stains":    info["stains"],
        },
        request=request,
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "materials_text": info["material"],
        "stains_text": info["stains"],
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

        return render(request, "laundry_manager/laundry-info.html", {
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
    return render(request, 'laundry_manager/laundry-info.html', {
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

        return render(request, "laundry_manager/laundry-info.html", {
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
