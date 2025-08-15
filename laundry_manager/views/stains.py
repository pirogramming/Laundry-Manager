import os, json
from django.http import Http404
from django.shortcuts import render
from pathlib import Path
from django.conf import settings

JSON_FILE_PATH = settings.BASE_DIR / "laundry_manager" / "json_data" / "persil_v2.json"
_ALL_STAIN_DATA = None


IMG_MAP = {
    "혈흔": "blood",
    "화장품 얼룩": "cosmetic",
    "땀 얼룩": "shirt-sweat",  # '땀과 겨드랑이 얼룩'과 구분
    "커피": "coffee",
    "펜과 잉크 얼룩": "pen",
    "녹 얼룩": "rust",
    "강황 얼룩": "curcuma",
    "크레용 및 왁스 얼룩": "crayon",
    "염색약, 페인트 등의 색상 얼룩": "paint",
    "세탁과 건조 후 생긴 얼룩": "after-laundry",
    "반려동물 소변 및 배설물 얼룩": "poop",
    "주스 얼룩": "juice",
    "탈취제 얼룩": "deodorant",
    "카레와 향신료 얼룩": "curry",
    "토마토 얼룩": "tomato",
    "청바지 얼룩": "jean",
    "매니큐어 얼룩": "manicure",
    "대변, 소변, 구토 얼룩": "poop",  # 반려동물 얼룩과 동일한 이미지
    "꽃가루 얼룩": "flower",
    "껌 얼룩": "gum",
    "음식 얼룩": "food-stain",
    "섬유 유연제 얼룩": "fabric-softner",
    "과일 및 야채 얼룩": "fruit",
    "초콜릿 얼룩": "chocolate",
    "땀과 겨드랑이 얼룩": "sweat-armpit",  # '땀 얼룩'과 구분
    "윤활유 및 기름 얼룩": "oil",
    "자외선 차단제, 크림 및 로션 얼룩": "suncream",
    "먼지와 진흙얼룩": "dust",
    "겨자, 케첩, 소스 얼룩": "sauce",
    "곰팡이 얼룩": "mold",
    "잔디의 녹색 색소 얼룩": "grass",
    "적포도주 얼룩": "wine",
    "모발 염료 및 염색약 얼룩": "hair-dye",
    "아이스크림 얼룩": "icecream",
    "치약 얼룩": "toothpaste",
    "아보카도 얼룩": "avocado",
    "옷감에서 얼룩 제거하는 법": "clothes",
    "시트에서 얼룩 제거하기": "bed-sheet",
    "오래되고 마른 얼룩을 제거하는 법": "old-dry",
    "흰 옷에서 얼룩을 제거하는 방법": "white-shirt",
    "면 옷의 얼룩 제거법": "cotton",
    "속옷에서 얼룩 제거하는 법": "underwear",
    "얼룩 제거를 위한 일반적인 팁": "NormalTipForStain",
    "흰 바지의 얼룩 제거법": "white-pants",
    "비단에서 얼룩 제거하기": "silk",
    "폴리에스테르 옷감의 얼룩 제거": "polyester",
    "모자에서 땀 얼룩 제거하는 법": "sweat-cap",
}


def _attach_image(item):
    title = (item.get("title") or "").strip()
    base = IMG_MAP.get(title) or item.get("slug")  # slug와 파일명이 같다면 fallback
    if base:
        item["image"] = f"stain_image/{base}.webp"
    else:
        item["image"] = f"stain_image/blood.webp"
    return item


def _load_stain_data():
    global _ALL_STAIN_DATA
    if _ALL_STAIN_DATA is None:
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f).get("washing_tips_categories", [])
            for idx, item in enumerate(data):
                slug = (
                    item.get("title", "")
                    .replace(" ", "_")
                    .replace("/", "_")
                    .strip("_")
                    .lower()
                )
                item["slug"] = slug or f"untitled_stain_{idx}"
                _attach_image(item)  # ← 여기서 이미지 경로 붙임
            _ALL_STAIN_DATA = data
        except Exception:
            _ALL_STAIN_DATA = []
    return _ALL_STAIN_DATA


ALL_STAIN_DATA = _load_stain_data()


def stain_guide_view(request):
    _load_stain_data()
    frequent_titles = [
        "혈흔",
        "화장품 얼룩",
        "땀 얼룩",
        "커피와 차 얼룩",
        "펜과 잉크 얼룩",
        "염색약, 페인트 등의 색상 얼룩",
        "세탁과 건조 후 생긴 얼룩",
        "껌 얼룩",
        "자외선 차단제, 크림 및 로션 얼룩",
        "겨자, 케첩, 소스 얼룩",
    ]
    frequent, other = [], []
    for s in ALL_STAIN_DATA:
        (frequent if s["title"] in frequent_titles else other).append(s)

    food_kw = [
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
    life_kw = [
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

    categorized = {"음식": [], "생활": []}
    for s in other:
        t = s["title"].lower()
        is_food = any(k in t for k in food_kw)
        is_life = any(k in t for k in life_kw)
        if is_food and not is_life:
            categorized["음식"].append(s)
        elif is_life and not is_food:
            categorized["생활"].append(s)
        else:
            categorized["생활"].append(s)

    return render(
        request,
        "laundry_manager/stain-upload.html",
        {
            "frequent_stains": frequent,
            "categorized_stains": categorized,
        },
    )


def stain_detail_view(request, slug):
    item = next((i for i in ALL_STAIN_DATA if i.get("slug") == slug), None)
    if not item:
        raise Http404("해당 얼룩 정보를 찾을 수 없습니다.")
    raw_detail = item.get("detail", {})
    processed_detail = {k.replace("_", " "): v for k, v in raw_detail.items()}
    return render(
        request,
        "laundry_manager/stain-info.html",
        {
            "title": item.get("title", "정보 없음"),
            "washing_steps": item.get("Washing_Steps", []),
            "detail_info": processed_detail,
            "tip_info": item.get("tip", []),
            "not_to_do_info": item.get("not_to_do", []),
            "other_info": item.get("Other_Information", []),
            "slug": slug,
        },
    )
