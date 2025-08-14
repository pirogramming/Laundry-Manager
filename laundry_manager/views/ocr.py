import os, uuid, json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from ..forms import ImageUploadForm
from ..utils import (
    perform_ocr, get_washing_symbol_definition, classify_laundry_symbol,
    load_washing_definitions, save_result_json, save_classification_result_json,
)

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

            definition, texts = get_washing_symbol_definition(ocr_result, WASHING_SYMBOLS_DEFINITIONS)
            request.session['recognized_texts'] = texts
            request.session['symbol_definition'] = definition
            request.session['material'] = request.POST.get("material")
            request.session['stains'] = request.POST.getlist("stains")
            save_result_json(image_path, texts, definition, ocr_result)
            return redirect('result')
    return render(request, 'laundry_manager/laundry-upload.html', context)

def result_view(request):
    texts = request.session.get('recognized_texts', [])
    definition = request.session.get('symbol_definition', '')
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])
    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
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
    return render(request, "laundry_manager/laundry-upload.html", {"form": form, "result": result})
