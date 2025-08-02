import os
import uuid
import time
import json
import re
import requests

from django.shortcuts import render
from django.conf import settings

from .forms import ImageUploadForm
from .models import UploadedImage
from decouple import config
from dotenv import load_dotenv

from .functions.recommend import laundry_recommend
from .functions.result import format_result


load_dotenv()
# WASHING_SYMBOLS_DEFINITIONS = load_washing_definitions()

# utils.py를 만들어서 함수들 분리했음
from .utils import (
    perform_ocr,
    get_washing_symbol_definition,
    classify_laundry_symbol,
    load_washing_definitions,
    save_result_json,
    save_classification_result_json,
    
)

def info_check_view(request):
    if request.method == 'GET':
        return render(request, 'laundry_manager/recommend.html')

def laundry_result_view(request):
    if request.method == "POST":
        # 1. info 준비 (예: request.POST나 session, 혹은 laundry_info 함수 활용)
        info = {
            'material': request.POST.get('material'),
            'stains': request.POST.getlist('stains'),
            'symbols': request.POST.getlist('symbols')
        }

        # 2. 세탁 정보 정리한 json 파일 불러오기
        rule_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'laundry_rules.json') # json 파일 이름으로 바꾸기
        with open(rule_path, 'r', encoding='utf-8') as f:
            rule_json = json.load(f) # JSON으로 파싱해서 파이썬 딕셔너리로 변환

        # 3. 세탁 추천 실행
        guides = laundry_recommend(info, rule_json)
        # 4. 출력 포맷
        result_text = format_result(guides)

        # 5. 템플릿에 전달
        return render(request, 'laundry_manager/recommend.html', {'result_text': result_text})

# views.py에는 필요한 애들만 남겼음
def upload_view(request):
    context = {
        'form': ImageUploadForm(),
        'uploaded_image_url': None,
        'uploaded_image_name': None,
        'recognized_texts': [],
        'symbol_definition': '',
        'error_message': None,
    }

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_instance = form.save()
            image_path = uploaded_instance.image.path
            context['uploaded_image_url'] = uploaded_instance.image.url
            context['uploaded_image_name'] = uploaded_instance.image.name

            print(f"파일이 {image_path} 에 저장되었습니다.")
            ocr_result = perform_ocr(image_path)

            if ocr_result.get("error"):
                context["error_message"] = ocr_result["message"]
            else:
                definition, texts = get_washing_symbol_definition(ocr_result, WASHING_SYMBOLS_DEFINITIONS)
                context["recognized_texts"] = texts
                context["symbol_definition"] = definition

                save_result_json(image_path, texts, definition, ocr_result)

    return render(request, 'laundry_manager/index.html', context)

# 이거는 roboflow에서 사용되는 함수임
def upload_and_classify(request):
    result = None

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES['image']
            os.makedirs("temp", exist_ok=True)

            ext = image_file.name.split('.')[-1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join("temp", filename)

            # 파일 저장
            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            result = classify_laundry_symbol(image_path)

            save_classification_result_json(image_path, result)

            os.remove(image_path)

    else:
        form = ImageUploadForm()

    return render(request, "laundry_manager/upload.html", {
        "form": form,
        "result": result,
    })
