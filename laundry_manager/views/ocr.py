import os, uuid, json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from ..forms import ImageUploadForm
from ..utils import (
    perform_ocr, get_washing_symbol_definition, classify_laundry_symbol,
    load_washing_definitions, save_result_json, save_classification_result_json,
)

from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output

WASHING_SYMBOLS_DEFINITIONS = load_washing_definitions()


def upload_view(request):
    context = {
        "form": ImageUploadForm(),
        "uploaded_image_url": None,
        "uploaded_image_name": None,
        "recognized_texts": [],
        "symbol_definition": "",
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

            definition, texts = get_washing_symbol_definition(
                ocr_result, WASHING_SYMBOLS_DEFINITIONS
            )

            # 세션 저장
            request.session['recognized_texts'] = texts or []
            request.session['symbol_definition'] = definition or ""
            request.session['material'] = request.POST.get("material")
            request.session['stains'] = request.POST.getlist("stains")

            # 결과 JSON 저장(이미 하고 있던 로깅)
            save_result_json(image_path, texts, definition, ocr_result)

            return redirect('result')

    return render(request, 'laundry_manager/laundry-upload.html', context)


def result_view(request):
    # 세션에서 기본값 가져오기
    texts = request.session.get('recognized_texts', [])
    definition = request.session.get('symbol_definition', '')
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])

    # 새로고침/직접 접근 등으로 세션이 비었을 때 보조 복구(옵션)
    if not texts:
        texts = load_latest_recognized_texts_from_output()

    # ★ OCR 텍스트 → 룰 분석 → 지시문 생성
    instructions = analyze_texts(texts)

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
        'instructions': instructions,   # ← 템플릿에서 사용
    })


def upload_and_classify(request):
    result = None
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES["image"]
            os.makedirs("temp", exist_ok=True)
            ext = image_file.name.split(".")[-1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join("temp", filename)
            with open(image_path, "wb+") as dst:
                for chunk in image_file.chunks():
                    dst.write(chunk)

            result = classify_laundry_symbol(image_path)
            save_classification_result_json(image_path, result)
            os.remove(image_path)
    else:
        form = ImageUploadForm()

    return render(
        request, "laundry_manager/laundry-upload.html",
        {"form": form, "result": result}
    )
