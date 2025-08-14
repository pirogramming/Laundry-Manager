import os, uuid
from django.shortcuts import render, redirect
from django.contrib import messages

from ..forms import ImageUploadForm
from ..utils import (
    perform_ocr, load_washing_definitions, save_result_json,
    extract_ocr_texts, parse_symbols_from_texts, parse_material_from_texts,
    should_call_roboflow, pick_rf_symbols_for_targets, filter_non_rf_symbols,
    symbols_to_guides,
)

WASHING_SYMBOLS_DEFINITIONS = load_washing_definitions()

def upload_view(request):
    context = {
        "form": ImageUploadForm(),
        "uploaded_image_url": None,
        "uploaded_image_name": None,
        "recognized_texts": [],
        "error_message": None,
    }

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_instance = form.save()
            messages.success(request, "사진이 업로드 됐습니다!")

            image_path = uploaded_instance.image.path
            context["uploaded_image_url"] = uploaded_instance.image.url
            context["uploaded_image_name"] = uploaded_instance.image.name

            ocr_result = perform_ocr(image_path)
            if ocr_result.get("error"):
                context["error_message"] = ocr_result["message"]
                return render(request, 'laundry_manager/laundry-upload.html', context)
            
            #ocr에서 텍스트 추출
            texts = extract_ocr_texts(ocr_result)

            # ocr 텍스트에서 세탁 라벨 후보 추출
            ocr_labels_all = parse_symbols_from_texts(texts)

            # 9개 기호는 ocr 후보에서 제외 (roboflow로 인식하도록)
            ocr_labels_non_rf = filter_non_rf_symbols(ocr_labels_all)

            # 필요시 roboflow로 9개 기호만 분류해서 보완
            rf_labels = []
            if should_call_roboflow():
                rf_labels = pick_rf_symbols_for_targets(image_path)
            
            # 최종 라벨 병합
            merged_labels = list(dict.fromkeys(ocr_labels_non_rf + rf_labels))

            # ocr 텍스트에서 소재 키워드 매칭
            material_canon, material_display = parse_material_from_texts(texts)

            # 세탁 기호랑 설명 배열 생성
            symbol_guides = symbols_to_guides(merged_labels, WASHING_SYMBOLS_DEFINITIONS)

            # 세션 저장
            request.session['recognized_texts'] = texts
            request.session['symbol_labels'] = merged_labels
            request.session['symbol_guides'] = symbol_guides
            request.session['symbols'] = merged_labels
            # 사용자가 폼에서 선택한 것도 같이
            request.session['material'] = material_display or request.POST.get("material")
            request.session['stains'] = request.POST.getlist("stains") or request.POST.getlist("stains[]")

            #json으로 저장
            save_result_json(
                image_path=image_path,
                texts=texts,
                definition=None,
                ocr_raw=ocr_result,
                rf_detect_raw=None, 
                rf_class_raw=rf_labels,
                fused_scores=None 
            )

            return redirect('result')
        
    return render(request, 'laundry_manager/laundry-upload.html', context)

def result_view(request):
    texts = request.session.get('recognized_texts', [])
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])
    symbol_labels = request.session.get("symbol_labels", [])
    symbol_guides = request.session.get("symbol_guides", [])

    return render(request, 'laundry_manager/result.html', 
        {
        'materials': [material] if material else [],
        'stains': stains,
        "symbol_labels": symbol_labels,
        "symbol_guides" : symbol_guides,
    },
    )