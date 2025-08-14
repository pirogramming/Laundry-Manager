# import os
# import uuid
# import time
# import json
# import re
# import requests
# from pathlib import Path

# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import JsonResponse, Http404
# from django.conf import settings

# from decouple import config
# from dotenv import load_dotenv

# from .forms import ImageUploadForm
# from .models import UploadedImage
# from .functions.recommend import laundry_recommend, get_material_guide, get_stain_guide
# from .functions.result import format_result
# from django.contrib import messages
# from .functions.info import first_info, final_info
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST

# from .functions.info import laundry_info, apply_user_correction
# from .utils import (
#     load_washing_definitions,
#     perform_ocr,
#     get_washing_symbol_definition,
#     classify_laundry_symbol,
#     classify_symbols_via_roboflow,
#     detect_symbols_via_roboflow,
#     normalize_to_canon,
#     _post_conflict_resolution,
#     save_result_json,
#     save_classification_result_json,
#     )

# # from rest_framework.views import APIView
# from django.shortcuts import render

# # from rest_framework.decorators import api_view

# from datetime import datetime, timedelta


# # Naver Trend API 키 로드
# NAVER_CLIENT_ID = config("NAVER_CLIENT_ID")
# NAVER_CLIENT_SECRET = config("NAVER_CLIENT_SECRET")


# def get_naver_trend_data(keywords, timeframe="today 3-m"):
#     url = "https://naveropenapi.apigw.ntruss.com/datalab/v1/search"
#     headers = {
#         "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
#         "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
#         "Content-Type": "application/json",
#     }

#     # API 호출을 위해 키워드 그룹을 구성
#     # API는 최대 5개의 키워드 그룹을 지원하지만, 여기서는 전체 키워드를 하나의 그룹으로 묶습니다.
#     # 키워드 수가 너무 많으면 API 오류가 발생할 수 있으니 주의해야 합니다.
#     keyword_groups = [
#         {"groupName": "인기 검색어", "keywords": keywords[:5]}
#     ]  # 최대 5개 키워드만 사용 예시

#     body = {
#         "startDate": "2023-01-01",  # 더 긴 기간으로 설정
#         "endDate": "2024-08-31",
#         "timeUnit": "month",
#         "keywordGroups": keyword_groups,
#     }

#     try:
#         response = requests.post(url, data=json.dumps(body), headers=headers)
#         # --- 디버깅용 코드 추가 ---
#         print(f"디버깅: API 호출 상태 코드 -> {response.status_code}")
#         print(f"디버깅: API 응답 내용 -> {response.text}")
#         # ------------------------

#         if response.status_code == 200:
#             result = response.json()

#             # 키워드 데이터를 직접 가져와 반환
#             # result['results'][0]['keywords']에는 API 호출에 사용된 키워드가 들어있습니다.
#             if "results" in result and len(result["results"]) > 0:
#                 return result["results"][0]["keywords"]
#             else:
#                 return []

#     except requests.exceptions.RequestException as e:
#         print(f"네트워크 오류: {e}")
#         return []


# def load_dictionary_data():
#     try:
#         dictionary_path = os.path.join(
#             settings.BASE_DIR, "laundry_manager", "json_data", "dictionary.json"
#         )
#         with open(dictionary_path, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         print("Error: dictionary.json not found.")
#         return {}
#     except json.JSONDecodeError:
#         print("Error: dictionary.json is not a valid JSON file.")
#         return {}


# def dictionary(request):
#     dictionary_data = load_dictionary_data()
#     query = request.GET.get("query")
#     category_map = {
#         "material_laundry_method": "소재별 세탁 방법",
#         "dry_storage_method": "건조 및 보관 방법",
#         "removal": "냄새 및 얼룩제거 방법",
#         "words": "용어 사전",
#         "how_laundry": "세탁 방법",
#     }
#     category_list = list(category_map.values())
#     processed_data = {}

#     def preprocess_item(item):
#         processed = item.copy()
#         processed["json_data"] = json.dumps(item, ensure_ascii=False)
#         return processed

#     if query:
#         is_category_query = query in category_list
#         if is_category_query:
#             category_key = next(
#                 (key for key, value in category_map.items() if value == query), None
#             )
#             if category_key and category_key in dictionary_data:
#                 processed_data[query] = [
#                     preprocess_item(item) for item in dictionary_data[category_key]
#                 ]
#         else:
#             for category_key, display_name in category_map.items():
#                 items = dictionary_data.get(category_key, [])
#                 filtered_items = []
#                 for item in items:
#                     search_string = (
#                         item.get("title", "").lower()
#                         + item.get("description", "").lower()
#                         + json.dumps(
#                             item.get("content", ""), ensure_ascii=False
#                         ).lower()
#                         + json.dumps(
#                             item.get("Washing_Steps", []), ensure_ascii=False
#                         ).lower()
#                         + json.dumps(item.get("tip", []), ensure_ascii=False).lower()
#                         + json.dumps(
#                             item.get("not_to_do", []), ensure_ascii=False
#                         ).lower()
#                         + json.dumps(
#                             item.get("Other_Information", []), ensure_ascii=False
#                         ).lower()
#                     )
#                     if query.lower() in search_string:
#                         filtered_items.append(preprocess_item(item))
#                 if filtered_items:
#                     processed_data[display_name] = filtered_items
#     else:
#         for category_key, display_name in category_map.items():
#             processed_data[display_name] = [
#                 preprocess_item(item) for item in dictionary_data.get(category_key, [])
#             ]

#     # Naver Trend API를 활용하여 인기 검색어 목록을 가져오는 로직 추가
#     # 수정할 코드 (views.py 파일 내)
#     all_keywords = []
#     for category_key in dictionary_data:
#         for item in dictionary_data.get(category_key, []):
#             title = item.get("title")
#             if title:
#                 all_keywords.append(title)

#     unique_keywords = list(set(all_keywords))
#     frequent_searches = get_naver_trend_data(unique_keywords)

#     context = {
#         "query": query,
#         "is_category_query": query in category_list if query else False,
#         "category_list": category_list,
#         "dictionary_data": processed_data,
#         "frequent_searches": frequent_searches,
#     }

#     return render(request, "laundry_manager/dictionary.html", context)


# load_dotenv()
# WASHING_SYMBOLS_DEFINITIONS = load_washing_definitions()

# # utils.py를 만들어서 함수들 분리했음

# # class UploadView(APIView):
# #     def info_check_view(self, request):
# #         if request.method == 'GET':
# #             return render(request, 'laundry_manager/recommend.html')


# # 세탁 정보 담긴 json 파일들 불러옴
# def load_json(filename):
#     path = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", filename)
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)


# # 세탁 정보 보여주는 함수 연결
# def laundry_result_view(request):
#     if request.method == "POST":
#         info = {
#             "material": request.POST.get("material"),
#             "stains": request.POST.getlist("stains"),
#             "symbols": request.POST.getlist("symbols") or request.session.get("symbol_labels", []),
#         }

#         material_json = load_json("blackup.json")
#         stain_json = load_json("persil_v2.json")
#         symbol_json = load_json("washing_symbol.json")

#         guides = laundry_recommend(info, material_json, stain_json, symbol_json)

#         return render(
#             request,
#             "laundry_manager/laundry_info.html",
#             {
#                 "material": guides.get("material_guide"),
#                 "stain": guides.get("stain_guide"),
#                 "symbols": guides.get("symbol_guide"),
#                 "info": info,
#                 "materials": [info["material"]],
#                 "stains": info["stains"],
#             },
#         )

#     return redirect("laundry-upload")


# def upload_view(request):
#     context = {
#         "form": ImageUploadForm(),
#         "uploaded_image_url": None,
#         "uploaded_image_name": None,
#         "recognized_texts": [],
#         "symbol_definition": "",
#         "error_message": None,
#     }

#     if request.method == "POST":
#         form = ImageUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             uploaded_instance = form.save()
#             messages.success(request, "사진이 업로드 됐습니다!")

#             image_path = uploaded_instance.image.path
#             context["uploaded_image_url"] = uploaded_instance.image.url
#             context["uploaded_image_name"] = uploaded_instance.image.name

#             print(f"파일이 {image_path} 에 저장되었습니다.")

#             # OCR 수행
#             ocr_result = perform_ocr(image_path)

#             if ocr_result.get("error"):
#                 context["error_message"] = ocr_result["message"]
#                 return render(request, "laundry_manager/laundry-upload.html", context)

#             # OCR 결과 파싱
#             defs = WASHING_SYMBOLS_DEFINITIONS
#             definition, texts = get_washing_symbol_definition(ocr_result, defs)
#             print("OCR 결과:", texts)

#             rf_preds = classify_symbols_via_roboflow(image_path)
#             threshold = 0.30
#             scored = {}

#             for t in texts:
#                 canon = normalize_to_canon(t)
#                 if canon:
#                     scored[canon] = scored.get(canon, 0.0) + 0.55
            
#             for p in rf_preds:
#                 lab = p.get("class", "")
#                 conf = float(p.get("confidence", 0) or 0)
#                 canon = normalize_to_canon(lab)
#                 if canon and conf >= threshold:
#                     scored[canon] = scored.get(canon, 0.0) + 0.45 * conf
            
#             resolved = _post_conflict_resolution(scored)

#             selected_labels = [k for k, v in resolved.items() if v >= 0.5]
#             selected_labels.sort(key=lambda k: resolved[k], reverse=True)


#             # 세션 저장
#             request.session["recognized_texts"] = texts
#             request.session["symbol_definition"] = definition
#             request.session["symbol_labels"] = selected_labels
#             request.session["material"] = request.POST.get("material")
#             request.session["stains"] = request.POST.getlist("stains")

#             # JSON 저장
#             save_result_json(
#                 image_path, 
#                 texts, 
#                 definition, 
#                 ocr_result,
#                 rf_detect_raw=None,
#                 rf_class_raw=rf_preds,
#                 fused_scores=resolved
#                 )

#             return redirect("result")

#     # GET 요청 또는 유효하지 않은 POST
#     return render(request, "laundry_manager/laundry-upload.html", context)


# def result_view(request):
#     texts = request.session.get("recognized_texts", [])
#     definition = request.session.get("symbol_definition", "")
#     material = request.session.get("material", "")
#     stains = request.session.get("stains", [])  # 리스트로 저장된 경우
#     symbol_labels = request.session.get("symbol_labels", [])

#     print("세션에서 가져온 OCR 결과:", texts)
#     print("세션에서 가져온 소재:", material)
#     print("세션에서 가져온 얼룩:", stains)

#     return render(
#         request,
#         "laundry_manager/result.html",
#         {
#             "recognized_texts": texts,
#             "symbol_definition": definition,
#             "materials": [material] if material else [],
#             "stains": stains,
#             "symbol_labels" : symbol_labels,
#         },
#     )


# # 이거는 roboflow에서 사용되는 함수임
# def upload_and_classify(request):
#     result = None

#     if request.method == "POST":
#         form = ImageUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             image_file = request.FILES["image"]
#             os.makedirs("temp", exist_ok=True)
#             ext = image_file.name.split(".")[-1]
#             filename = f"{uuid.uuid4().hex}.{ext}"
#             image_path = os.path.join("temp", filename)

#             # 파일 저장
#             with open(image_path, "wb+") as destination:
#                 for chunk in image_file.chunks():
#                     destination.write(chunk)

#             result = classify_laundry_symbol(image_path)

#             save_classification_result_json(image_path, result)

#             os.remove(image_path)

#     else:
#         form = ImageUploadForm()

#     return render(
#         request,
#         "laundry_manager/laundry-upload.html",
#         {
#             "form": form,
#             "result": result,
#         },
#     )


# # 2. 뷰 함수 정의
# def laundry_info_view(request):

#     # 추후 경로 수정!!
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     DATA_DIR = os.path.join(BASE_DIR, "data")

#     ocr_path = os.path.join(DATA_DIR, "ocr_data.json")
#     user_path = os.path.join(DATA_DIR, "user_input.json")
#     corrected_path = os.path.join(DATA_DIR, "corrected_input.json")

#     # 2차 수정 정보가 있으면 반영
#     if os.path.exists(corrected_path):
#         result = apply_user_correction(ocr_path, user_path, corrected_path)
#     else:
#         result = laundry_info(ocr_path, user_path)

#     # JSON 응답 반환
#     return JsonResponse(result, json_dumps_params={"ensure_ascii": False})


# # laundry_info_view1을 만들었는데 런드리 인포에서
# # 소재랑 얼룩이 뜨게하는 함수임


# def laundry_info_view1(request):
#     material_name = request.session.get("material", "")
#     stains = request.session.get("stains", [])

#     material_info = get_material_guide(material_name) if material_name else {}
#     stain_info = get_stain_guide(stains[0]) if stains else {}

#     return render(
#         request,
#         "laundry_manager/laundry_info.html",
#         {
#             "material_name": material_name,
#             "stains": stains,
#             "material": material_info,
#             "stain": stain_info,
#             "symbols": request.session.get("symbols", []),
#             "info": {"material": material_name, "stains": " / ".join(stains)},
#         },
#     )


# PROJECT_ROOT_DIR = (
#     Path(__file__).resolve().parent.parent
# )  # 전체 루트 디렉토리(Laundry-Manager)
# JSON_FILE_PATH = PROJECT_ROOT_DIR / "laundry_temp_json" / "persil_v2.json"
# _all_stains_data = (
#     None  # 얼룩 정보를 담은 json 파일에 대한 정보를 저장함..파이썬 딕셔너리 같은 기능
# )


# def load_stain_data():
#     global _all_stains_data  # 전역 변수 선언
#     if _all_stains_data is None:
#         try:
#             with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#                 _all_stains_data = data.get("washing_tips_categories", [])
#                 # 전체 목록을 가져옴
#             for stain_category in _all_stains_data:
#                 # 각각의 얼룩 카테고리를 저장함..혈흔, 화장품
#                 stain_category["slug"] = (
#                     stain_category["title"]
#                     .replace(" ", "_")  # 공백을 _f로 바꿈
#                     .replace("/", "_")  # /도 _로 바꿈
#                     .strip("_")  # 맨앞에 있는 _ 없앰
#                     .lower()  # 영어이면 소문자...
#                 )
#                 if not stain_category["slug"]:
#                     stain_category["slug"] = (
#                         f"untitled_stain_{_all_stains_data.index(stain_category)}"
#                     )

#         except FileNotFoundError:
#             print(f"Error: JSON file not found at {JSON_FILE_PATH}")
#             _all_stains_data = []  # 파일이 없으면 빈 리스트 반환
#         except json.JSONDecodeError:
#             print(f"Error: Could not decode JSON from {JSON_FILE_PATH}")
#             _all_stains_data = []
#     return _all_stains_data


# ALL_STAIN_DATA = load_stain_data()  # 최종적으로 로드되고 가공된 "모든 얼룩 데이터"


# def stain_guide_view(request):
#     frequent_stain_titles = [
#         "혈흔",
#         "화장품 얼룩",
#         "땀 얼룩",
#         "커피와 차 얼룩",
#         "펜과 잉크 얼룩",
#         "염색약, 페인트 등의 색상 얼룩",
#         "세탁과 건조 후 생긴 얼룩",
#         "껌 얼룩",
#         "자외선 차단제, 크림 및 로션 얼룩",
#         "겨자, 케첩, 소스 얼룩",
#     ]  # 사용자가 자주 찾아볼 만한 얼룩제거법은 따로 정리함

#     # 모든 얼룩 데이터에서 frequent_stains와 other_stains 분리
#     frequent_stains = []
#     other_stains = []

#     for stain_item in ALL_STAIN_DATA:
#         if stain_item["title"] in frequent_stain_titles:
#             frequent_stains.append(stain_item)
#         else:
#             other_stains.append(stain_item)

#     # 나머지 얼룩을 '음식'과 '생활' 카테고리로 분류 (title 기반)
#     categorized_stains = {
#         "음식": [],
#         "생활": [],
#     }

#     # 키워드 매칭은 Json 데이터의 'title'에 기반하여 더 정확하게 조정해야 합니다.
#     # 예를 들어, '토마토 제거법'은 음식으로, '곰팡이 제거법'은 생활로.
#     food_keywords = [
#         "커피",
#         "차",
#         "주스",
#         "카레",
#         "토마토",
#         "음식",
#         "과일",
#         "채소",
#         "초콜릿",
#         "적포도주",
#         "아이스크림",
#         "아보카도",
#         "소스",
#         "강황",
#     ]
#     life_keywords = [
#         "녹",
#         "크레용",
#         "왁스",
#         "반려동물",
#         "탈취제",
#         "청바지",
#         "매니큐어",
#         "대변",
#         "소변",
#         "꽃가루",
#         "껌",
#         "섬유 유연제",
#         "땀",
#         "겨드랑이",
#         "윤활유",
#         "기름",
#         "자외선",
#         "먼지",
#         "진흙",
#         "곰팡이",
#         "잔디",
#         "혈흔",
#         "화장품",
#         "펜",
#         "잉크",
#         "세탁",
#         "건조",
#         "모발 염료",
#         "염색약",
#         "페인트",
#         "치약",
#     ]

#     for stain_item in other_stains:
#         title_lower = stain_item["title"].lower()
#         is_food = any(keyword in title_lower for keyword in food_keywords)
#         is_life = any(keyword in title_lower for keyword in life_keywords)

#         if is_food and not is_life:
#             categorized_stains["음식"].append(stain_item)
#         elif is_life and not is_food:
#             categorized_stains["생활"].append(stain_item)
#         elif is_food and is_life:  # 둘 다 포함하는 경우, 음식으로 우선 분류
#             categorized_stains["음식"].append(stain_item)
#         else:  # 어떤 키워드에도 매칭되지 않으면 생활로 분류 (기본값)
#             categorized_stains["생활"].append(stain_item)

#     context = {
#         "frequent_stains": frequent_stains,
#         "categorized_stains": categorized_stains,
#     }
#     return render(request, "laundry_manager/stain-upload.html", context)

# """
# 이름 : first_info_view
# 인자 : request
# 기능 : 
# 1. post(사용자) 데이터 받기
# 2. first_info 함수 호출
# 3. 템플릿에 전달
# 4. upload.html 호출, first_info 정보 띄우기
# """


# @csrf_exempt
# def first_info_view(request):
#     if request.method == "POST":
#         # POST 데이터 받아오기
#         filename = request.POST.get("filename")
#         selected_materials = request.POST.getlist("materials[]")  # 다중 선택 고려
#         selected_stains = request.POST.getlist("stains[]")

#         # first_info 함수 호출
#         result = first_info(
#             filename=filename,
#             selected_materials=selected_materials,
#             selected_stains=selected_stains,
#         )

#         # 템플릿에 전달
#         return render(
#             request,
#             "laundry_manager/result.html",
#             {
#                 "materials": result.get("materials", []),
#                 "symbols": result.get("symbols", []),
#                 "stains": result.get("stains", []),
#                 "filename": filename,  # 이후 final_info에 넘기기 위함
#             },
#         )

#     # GET 요청 시는 업로드 페이지 보여줌
#     return render(request, "laundry_manager/result.html")


# """
# 이름 : final_info_view
# 인자 : request
# 기능 :
# 1. 이미지는 그대로, Post(사용자가 수정한 내용) 받기
# 2. final_info 호출
# 3. laundry_info.html 호출, final_info 정보 띄우기
# """


# @csrf_exempt
# def final_info_view(request):
#     if request.method == "POST":
#         # 기존 이미지 filename 받기
#         filename = request.POST.get("filename")

#         # result.html에서 수정된 값 받기
#         manual_materials = request.POST.getlist("manual_materials[]")
#         manual_symbols = request.POST.getlist("manual_symbols[]")
#         manual_stains = request.POST.getlist("manual_stains[]")

#         # 1차 info 먼저 재호출 (filename 기반)
#         first_result = first_info(filename=filename)

#         # 최종 정제
#         final_result = final_info(
#             first_info=first_result,
#             manual_materials=manual_materials,
#             manual_symbols=manual_symbols,
#             manual_stains=manual_stains,
#         )

#         return render(
#             request,
#             "laundry_manager/laundry_info.html",
#             {
#                 "materials": final_result.get("materials", []),
#                 "symbols": final_result.get("symbols", []),
#                 "stains": final_result.get("stains", []),
#             },
#         )

#     return JsonResponse({"error": "Invalid request"}, status=400)


# # 아직 미완
# def stain_detail_view(request, slug):
#     stain_data = next(
#         (item for item in ALL_STAIN_DATA if item.get("slug") == slug), None
#     )

#     if not stain_data:
#         raise Http404("해당 얼룩 정보를 찾을 수 없습니다.")

#     title = stain_data.get("title", "정보 없음")
#     washing_steps = stain_data.get("Washing_Steps", [])
#     raw_detail_info = stain_data.get("detail", {})  # 원본 detail_info를 가져옵니다.
#     tip_info = stain_data.get("tip", [])
#     not_to_do_info = stain_data.get("not_to_do", [])
#     other_info = stain_data.get("Other_Information", [])

#     # detail_info의 키를 가공하여 새로운 딕셔너리 생성
#     processed_detail_info = {}
#     for key, value in raw_detail_info.items():
#         # 여기서 언더스코어를 공백으로 바꿉니다.
#         processed_key = key.replace("_", " ")
#         processed_detail_info[processed_key] = value

#     context = {
#         "title": title,
#         "washing_steps": washing_steps,
#         "detail_info": processed_detail_info,  # 가공된 detail_info를 전달
#         "tip_info": tip_info,
#         "not_to_do_info": not_to_do_info,
#         "other_info": other_info,
#         "slug": slug,
#     }
#     return render(request, "laundry_manager/stain_detail.html", context)


# from django.shortcuts import render


# # Create your views here.
# def main_page(request):
#     return render(request, "laundry_manager/main.html")


# def laundry_upload_page(request):
#     return render(request, "laundry_manager/laundry-upload.html")


# def stain_upload_page(request):
#     return render(request, "laundry_manager/stain-upload.html")


# def result_page(request):
#     return render(request, "laundry_manager/result.html")


# # 결과 페이지에서 단어 호버하면 백과사전 페이지로 넘어가는 로직 짬
# def laundry_info_page(request):
#     # 백과사전 페이지로 링크할 용어 목록
#     dictionary_terms = [
#         "레이온",
#         "스웨이드",
#         "쉬폰",
#         "세제",
#         "중성세제",
#         "알칼리성세제",
#         "산성세제",
#     ]

#     context = {"dictionary_terms": dictionary_terms}
#     return render(request, "laundry_manager/laundry-info.html", context)


# def stain_info_page(request):
#     return render(request, "laundry_manager/stain-info.html")


# def stain_guide_page(request):
#     return render(request, "laundry_manager/stain_guide.html")


# def stain_detail_page(request):
#     return render(request, "laundry_manager/stain_detail.html")
