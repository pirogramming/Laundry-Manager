# laundry_manager/views/dictionary.py
import os, json, logging
from datetime import date
import requests
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from urllib.parse import unquote
from django.template.loader import render_to_string
from django.contrib.staticfiles.finders import find

logger = logging.getLogger(__name__)

# ★ settings.py에서 정의한 값을 사용 (decouple 사용 X)
NAVER_CLIENT_ID = getattr(settings, "NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = getattr(settings, "NAVER_CLIENT_SECRET", "")


def _load_dictionary_data():
    try:
        p = os.path.join(
            settings.BASE_DIR, "laundry_manager", "json_data", "dictionary.json"
        )
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("dictionary.json 로드 실패: %s", e)
        return {}


def _ymd(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _start_end_for_months(months_back: int = 18):
    today = date.today()
    total = today.year * 12 + (today.month - 1) - months_back
    sy, sm = divmod(total, 12)
    sm += 1
    start = date(sy, sm, 1)
    return _ymd(start), _ymd(today)


def get_naver_trend_data(keywords, timeframe="today 3-m"):
    url = "https://naveropenapi.apigw.ntruss.com/datalab/v1/search"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json",
    }

    # API 호출을 위해 키워드 그룹을 구성
    # API는 최대 5개의 키워드 그룹을 지원하지만, 여기서는 전체 키워드를 하나의 그룹으로 묶습니다.
    # 키워드 수가 너무 많으면 API 오류가 발생할 수 있으니 주의해야 합니다.
    keyword_groups = [
        {"groupName": "인기 검색어", "keywords": keywords[:5]}
    ]  # 최대 5개 키워드만 사용 예시

    body = {
        "startDate": "2023-01-01",  # 더 긴 기간으로 설정
        "endDate": "2024-08-31",
        "timeUnit": "month",
        "keywordGroups": keyword_groups,
    }

    try:
        response = requests.post(url, data=json.dumps(body), headers=headers)
        # --- 디버깅용 코드 추가 ---
        print(f"디버깅: API 호출 상태 코드 -> {response.status_code}")
        print(f"디버깅: API 응답 내용 -> {response.text}")
        # ------------------------

        if response.status_code == 200:
            result = response.json()

            # 키워드 데이터를 직접 가져와 반환
            # result['results'][0]['keywords']에는 API 호출에 사용된 키워드가 들어있습니다.
            if "results" in result and len(result["results"]) > 0:
                return result["results"][0]["keywords"]
            else:
                return []

    except requests.exceptions.RequestException as e:
        print(f"네트워크 오류: {e}")
        return []


def load_dictionary_data():
    try:
        dictionary_path = os.path.join(
            settings.BASE_DIR, "laundry_manager", "json_data", "dictionary.json"
        )
        with open(dictionary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: dictionary.json not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: dictionary.json is not a valid JSON file.")
        return {}


def dictionary(request):
    dictionary_data = load_dictionary_data()
    query = request.GET.get("query")
    category_map = {
        "material_laundry_method": "소재별 세탁 방법",
        "dry_storage_method": "건조 및 보관 방법",
        "removal": "냄새 및 얼룩제거 방법",
        "words": "용어 사전",
        "how_laundry": "세탁 방법",
        "enjoy_looking": "즐겨찾기",
    }
    category_list = list(category_map.values())
    processed_data = {}

    from_search = "query" in request.GET

    item_index = 0  # 이미지 파일명에 사용할 인덱스를 초기화

    def preprocess_item(item):
        nonlocal item_index
        processed = item.copy()
        item_index += 1
        # Use a consistent file name pattern
        image_filename = f"dictionary_image/{item_index}.jpg"
        processed["image_url"] = (
            f"/static/{image_filename}"  # Check if the image file exists
        )
        image_path = find(image_filename)
        processed["has_image"] = os.path.exists(image_path)
        processed["image_filename"] = image_filename
        processed["json_data"] = json.dumps(item, ensure_ascii=False)
        return processed

    if query:
        is_category_query = query in category_list
        if is_category_query:
            category_key = next(
                (key for key, value in category_map.items() if value == query), None
            )
            if category_key and category_key in dictionary_data:
                processed_data[query] = [
                    preprocess_item(item) for item in dictionary_data[category_key]
                ]
        else:
            for category_key, display_name in category_map.items():
                items = dictionary_data.get(category_key, [])
                filtered_items = []
                for item in items:
                    search_string = item.get("title", "").lower()
                    if query.lower() in search_string:
                        filtered_items.append(preprocess_item(item))
                if filtered_items:
                    processed_data[display_name] = filtered_items
    else:
        for category_key, display_name in category_map.items():
            processed_data[display_name] = [
                preprocess_item(item) for item in dictionary_data.get(category_key, [])
            ]

    # Naver Trend API를 활용하여 인기 검색어 목록을 가져오는 로직 추가
    # 수정할 코드 (views.py 파일 내)
    all_keyword_data = []
    temp_item_index = 0
    for category_key in dictionary_data:
        for item in dictionary_data.get(category_key, []):
            temp_item_index += 1
            title = item.get("title")
            image_filename = f"dictionary_image/{temp_item_index}.jpg"
            if title:
                all_keyword_data.append(
                    {"title": title, "image_filename": image_filename}
                )

    unique_keywords_map = {item["title"]: item for item in all_keyword_data}
    unique_keywords = list(unique_keywords_map.keys())

    # get_naver_trend_data를 한 번만 호출하도록 수정
    naver_frequent_searches = get_naver_trend_data(unique_keywords)

    frequent_searches = []
    for keyword in naver_frequent_searches:
        if keyword in unique_keywords_map:
            frequent_searches.append(unique_keywords_map[keyword])

    context = {
        "query": query,
        "is_category_query": query in category_list if query else False,
        "category_list": category_list,
        "dictionary_data": processed_data,
        "frequent_searches": frequent_searches,
        "from_search": from_search,  # from_search 변수를 context에 추가
    }

    return render(request, "laundry_manager/dictionary.html", context)


# 과거 호환
# dictionary = dictionary_view
dictionary_view = dictionary


def dictionary_detail(request, item_title):
    decoded_title = unquote(item_title)
    dictionary_data = load_dictionary_data()
    item_data = None
    item_index = 0  # Index to track the image filename

    for category_key in dictionary_data:
        for item in dictionary_data.get(category_key, []):
            item_index += 1  # Increment the index for each item
            if item.get("title") == decoded_title:
                item_data = item
                break
        if item_data:
            break

    if not item_data:
        return render(
            request,
            "laundry_manager/not_found.html",
            {"message": f"'{decoded_title}'에 대한 세탁 정보를 찾을 수 없습니다."},
        )

    from_search = "query" in request.GET

    # ★★★ This is the key section to add/modify ★★★
    # Attach the image filename and URL to the item_data
    item_data["image_filename"] = f"dictionary_image/{item_index}.jpg"
    item_data["image_url"] = f"/static/{item_data['image_filename']}"

    context = {
        "item": item_data,
        "category_map": {
            "description": "설명",
            "content": "상세 내용",
            "Washing_Steps": "세탁 단계",
            "tip": "팁",
            "not_to_do": "주의 사항",
            "Other_Information": "기타 정보",
            "from_search": from_search,  # from_search 변수 추가
        },
    }

    return render(request, "laundry_manager/dictionary-detail.html", context)
