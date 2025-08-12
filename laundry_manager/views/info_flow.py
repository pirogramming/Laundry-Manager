import os, json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from ..functions.recommend import laundry_recommend, get_material_guide, get_stain_guide
from ..functions.info import first_info, final_info
from django.conf import settings

from ..models import LaundryHistory
from ..functions.recommend import laundry_recommend
from ..functions.result import format_result

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
            "stains": [info["stains"]],
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
        manual_stains = request.POST.getlist("manual_stains[]")
        first_result = first_info(filename=filename)
        final_result = final_info(first_info=first_result,
                                  manual_materials=manual_materials,
                                  manual_symbols=manual_symbols,
                                  manual_stains=manual_stains)
        # 1. 추천 결과 텍스트 생성
        material_json = load_json('blackup.json')
        stain_json = load_json('persil_v2.json')
        symbol_json = load_json('washing_symbol.json')
        guides = laundry_recommend(final_result, material_json, stain_json, symbol_json)
        recommendation_text = format_result(guides)

        # 2. 로그인 상태이면 DB에 저장
        if request.user.is_authenticated:
            LaundryHistory.objects.create(
                user=request.user,
                materials=', '.join(final_result.get("materials", [])),
                symbols=', '.join(final_result.get("symbols", [])),
                stains=', '.join(final_result.get("stains", [])),
                recommendation_result=recommendation_text
            )
        
        return render(request, "laundry_manager/laundry_info.html", {
            "materials": final_result.get("materials", []),
            "symbols": final_result.get("symbols", []),
            "stains": final_result.get("stains", []),
            "material_name": ", ".join(final_result.get("materials", [])), 
            "material" : guides.get('material_guide'),
            "stain": guides.get('stain_guide'),
            "info": {
                'stains': ", ".join(final_result.get("stains", [])),
                'material': ", ".join(final_result.get("materials", []))
            }
        })
    return JsonResponse({"error": "Invalid request"}, status=400)
