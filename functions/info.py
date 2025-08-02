import os
import json
import re
from django.conf import settings

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def laundry_info_from_ocr(filename: str, selected_stains: list) -> dict:
    # 경로 설정
    base_dir = settings.BASE_DIR
    ocr_path = os.path.join(base_dir, 'output', f"{os.path.splitext(filename)[0]}_result.json")
    material_path = os.path.join(base_dir, 'laundry_temp_json', 'blackup.json')
    symbol_path = os.path.join(base_dir, 'laundry_manager', 'washing_symbol.json')
    stain_path = os.path.join(base_dir, 'laundry_temp_json', 'persil_v2.json')

    # 기준 데이터 로드
    materials_data = load_json(material_path).get("material_washing_tips", [])
    symbols_data = load_json(symbol_path)
    stains_data = load_json(stain_path).get("washing_tips_categories", [])

    #valid_materials = {"면", "울", "폴리"} 이런식으로 정리
    valid_materials = set()
    for entry in materials_data:
        name = entry.get("material", "")
        if "(" in name:
            name = name.split("(")[0]
        valid_materials.add(name.strip())

    valid_symbols = set()
    for entry in symbols_data:
        valid_symbols.update(entry.get("id", []))


    #얼룩 분류
    valid_stains = set()
    frequent_stain_titles=[]
    food_keywords=[]
    life_keywords=[]
    # 사전 정의된 키워드
    food_keywords = [
        "커피", "차", "주스", "카레", "토마토", "음식", "과일", "채소", "초콜릿",
        "적포도주", "아이스크림", "아보카도", "소스", "강황"
    ]

    life_keywords = [
        "녹", "크레용", "왁스", "반려동물", "탈취제", "청바지", "매니큐어", "대변",
        "소변", "꽃가루", "껌", "섬유 유연제", "땀", "겨드랑이", "윤활유", "기름",
        "자외선", "먼지", "진흙", "곰팡이", "잔디", "혈흔", "화장품", "펜", "잉크",
        "세탁", "건조", "모발 염료", "염색약", "페인트", "치약"
    ]



    for entry in stains_data:
        title = entry.get("category", "")
        
        if title == "없음":
            frequent_stain_titles.extend([
                "혈흔", "화장품 얼룩", "땀 얼룩", "커피와 차 얼룩", "펜과 잉크 얼룩 제거법",
                "염색약, 페인트 등의 색상 얼룩", "세탁과 건조 후의 생긴 얼룩", "껌 얼룩",
                "자외선 차단제, 크림 및 로션 얼룩 제거하는 법", "겨자, 케첩, 소스 얼룩"
            ])
        else:
            for keyword in food_keywords:
                if keyword in title:
                    food_keywords.append(title)
                    break  # 중복 추가 방지

            for keyword in life_keywords:
                if keyword in title:
                    life_keywords.append(title)
                    break


            
            if title:
                clean_title = title.replace("제거법", "").strip()
                valid_stains.add(clean_title)


        # 결과 리스트 초기화
        materials = []
        symbols = []
        stains = []

        # OCR 결과 처리
        if os.path.exists(ocr_path):
            ocr_json = load_json(ocr_path)
            raw_texts = ocr_json.get("recognized_texts", [])
            joined_text = " ".join(raw_texts).lower()
            ocr_words = set(re.findall(r'[가-힣a-zA-Z0-9]+', joined_text))

            for material in valid_materials:
                if material.lower() in ocr_words:
                    materials.append(material)

            for symbol in valid_symbols:
                if symbol.lower() in ocr_words:
                    symbols.append(symbol)

        # stains는 사용자 입력 기반
        for stain in selected_stains:
            if stain in valid_stains:
                stains.append(stain)

        return {
            "materials": materials,
            "symbols": symbols,
            "stains": stains
        }
