import os
import uuid
import time
import json
import re
import requests
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.conf import settings

from decouple import config
from dotenv import load_dotenv

from .forms import ImageUploadForm
from .models import UploadedImage
from .functions.recommend import laundry_recommend
from .functions.result import format_result
# from functions.info import laundry_info, apply_user_correction



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
  
  
  
# 2. 뷰 함수 정의
def laundry_info_view(request):

    # 추후 경로 수정!!
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")

    ocr_path = os.path.join(DATA_DIR, "ocr_data.json")
    user_path = os.path.join(DATA_DIR, "user_input.json")
    corrected_path = os.path.join(DATA_DIR, "corrected_input.json")

    # 2차 수정 정보가 있으면 반영
    if os.path.exists(corrected_path):
        result = apply_user_correction(ocr_path, user_path, corrected_path)
    else:
        result = laundry_info(ocr_path, user_path)

    # JSON 응답 반환
    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})


PROJECT_ROOT_DIR = (
    Path(__file__).resolve().parent.parent
)  # 전체 루트 디렉토리(Laundry-Manager)
JSON_FILE_PATH = PROJECT_ROOT_DIR / "laundry_temp_json" / "persil_v2.json"
_all_stains_data = (
    None  # 얼룩 정보를 담은 json 파일에 대한 정보를 저장함..파이썬 딕셔너리 같은 기능
)


def load_stain_data():
    global _all_stains_data  # 전역 변수 선언
    if _all_stains_data is None:
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _all_stains_data = data.get("washing_tips_categories", [])
                # 전체 목록을 가져옴
            for stain_category in _all_stains_data:
                # 각각의 얼룩 카테고리를 저장함..혈흔, 화장품
                stain_category["slug"] = (
                    stain_category["title"]
                    .replace(" ", "_")  # 공백을 _f로 바꿈
                    .replace("/", "_")  # /도 _로 바꿈
                    .replace("제거법", "")  # 제거법이라는 글자 없앰
                    .strip("_")  # 맨앞에 있는 _ 없앰
                    .lower()  # 영어이면 소문자...
                )
                if not stain_category["slug"]:
                    stain_category["slug"] = (
                        f"untitled_stain_{_all_stains_data.index(stain_category)}"
                    )

        except FileNotFoundError:
            print(f"Error: JSON file not found at {JSON_FILE_PATH}")
            _all_stains_data = []  # 파일이 없으면 빈 리스트 반환
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {JSON_FILE_PATH}")
            _all_stains_data = []
    return _all_stains_data


ALL_STAIN_DATA = load_stain_data()  # 최종적으로 로드되고 가공된 "모든 얼룩 데이터"


def stain_guide_view(request):
    frequent_stain_titles = [
        "혈흔 제거법",
        "메이크업 및 립스틱 얼룩 제거",
        "셔츠에서 땀 얼룩을 제거하는 법",
        "커피와 차 얼룩 제거법",
        "펜과 잉크 얼룩을 제거하기",
        "염색약, 페인트 그리고 색상 얼룩을 제거하는 법",
        "세탁과 건조 후의 옷에서 얼룩 제거하는 법",
        "껌 얼룩 제거하는 법",
        "자외선 차단제, 크림 및 로션 얼룩 제거하는 법",
        "겨자, 케첩, 소스 얼룩 제거법",
    ]  # 사용자가 자주 찾아볼 만한 얼룩제거법은 따로 정리함

    # 모든 얼룩 데이터에서 frequent_stains와 other_stains 분리
    frequent_stains = []
    other_stains = []

    for stain_item in ALL_STAIN_DATA:
        if stain_item["title"] in frequent_stain_titles:
            frequent_stains.append(stain_item)
        else:
            other_stains.append(stain_item)

    # 나머지 얼룩을 '음식'과 '생활' 카테고리로 분류 (title 기반)
    categorized_stains = {
        "음식": [],
        "생활": [],
    }

    # 키워드 매칭은 Json 데이터의 'title'에 기반하여 더 정확하게 조정해야 합니다.
    # 예를 들어, '토마토 제거법'은 음식으로, '곰팡이 제거법'은 생활로.
    food_keywords = [
        "커피",
        "차",
        "주스",
        "카레",
        "토마토",
        "음식",
        "과일",
        "채소",
        "초콜릿",
        "적포도주",
        "아이스크림",
        "아보카도",
        "소스",
        "강황",
    ]
    life_keywords = [
        "녹",
        "크레용",
        "왁스",
        "반려동물",
        "탈취제",
        "청바지",
        "매니큐어",
        "대변",
        "소변",
        "꽃가루",
        "껌",
        "섬유 유연제",
        "땀",
        "겨드랑이",
        "윤활유",
        "기름",
        "자외선",
        "먼지",
        "진흙",
        "곰팡이",
        "잔디",
        "혈흔",
        "화장품",
        "펜",
        "잉크",
        "세탁",
        "건조",
        "모발 염료",
        "염색약",
        "페인트",
        "치약",
    ]

    for stain_item in other_stains:
        title_lower = stain_item["title"].lower()
        is_food = any(keyword in title_lower for keyword in food_keywords)
        is_life = any(keyword in title_lower for keyword in life_keywords)

        if is_food and not is_life:
            categorized_stains["음식"].append(stain_item)
        elif is_life and not is_food:
            categorized_stains["생활"].append(stain_item)
        elif is_food and is_life:  # 둘 다 포함하는 경우, 음식으로 우선 분류
            categorized_stains["음식"].append(stain_item)
        else:  # 어떤 키워드에도 매칭되지 않으면 생활로 분류 (기본값)
            categorized_stains["생활"].append(stain_item)

    context = {
        "frequent_stains": frequent_stains,
        "categorized_stains": categorized_stains,
    }
    return render(request, "laundry_manager/stain_guide.html", context)


# 아직 미완
def stain_detail_view(request, slug):
    stain_data = next(
        (item for item in ALL_STAIN_DATA if item.get("slug") == slug), None
    )

    if not stain_data:
        raise Http404("해당 얼룩 정보를 찾을 수 없습니다.")

    title = stain_data.get("title", "정보 없음")
    washing_steps = stain_data.get("Washing_Steps", [])
    raw_detail_info = stain_data.get("detail", {})  # 원본 detail_info를 가져옵니다.
    tip_info = stain_data.get("tip", [])
    not_to_do_info = stain_data.get("not_to_do", [])
    other_info = stain_data.get("Other_Information", [])

    # detail_info의 키를 가공하여 새로운 딕셔너리 생성
    processed_detail_info = {}
    for key, value in raw_detail_info.items():
        # 여기서 언더스코어를 공백으로 바꿉니다.
        processed_key = key.replace("_", " ")
        processed_detail_info[processed_key] = value

    context = {
        "title": title,
        "washing_steps": washing_steps,
        "detail_info": processed_detail_info,  # 가공된 detail_info를 전달
        "tip_info": tip_info,
        "not_to_do_info": not_to_do_info,
        "other_info": other_info,
        "slug": slug,
    }
    return render(request, "laundry_manager/stain_detail.html", context)
from django.shortcuts import render

# Create your views here.
def main_page(request):
    return render(request, 'laundry_manager/main.html')

def upload_page(request):
    return render(request, 'laundry_manager/upload.html')
def result_page(request):
    return render(request, 'laundry_manager/result.html')