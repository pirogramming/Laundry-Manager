import os
import json
import re
from django.conf import settings

#경로 받아와서 json 불러오기
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


'''
이름 : first_laundry_info
매개변수 : filename, selected_materials, selected_stains
기능  
1. 경로 설정/데이터 로드 
2. 기준 소재/심볼/얼룩 정제 리스트 생성(json 데이터로)
3. 얼룩 카테고리화
4. ocr 결과 반영--소재, 심볼 (기준리스트와 비교해서)
5. 사용자 수동 선택 소재, 얼룩 반영 (기준리스트와 비교)
6. 최종 반환
'''



# def first_info(filename: str = None,
#                           selected_materials: list = None,
#                           selected_stains: list = None) -> dict:

#     # 경로 설정
#     base_dir = settings.BASE_DIR
#     if filename:
#         ocr_path = os.path.join(base_dir, 'output', f"{os.path.splitext(filename)[0]}_result.json")
#     material_path = os.path.join(base_dir, 'laundry_temp_json', 'blackup.json')
#     symbol_path = os.path.join(base_dir, 'laundry_manager', 'washing_symbol.json')
#     stain_path = os.path.join(base_dir, 'laundry_temp_json', 'persil_v2.json')

#     # 기준 데이터 로드
#     materials_data = load_json(material_path).get("material_washing_tips", [])
#     symbols_data = load_json(symbol_path)
#     stains_data = load_json(stain_path).get("washing_tips_categories", [])

#     #기준 소재 정리 // valid_materials = {"면", "울", "폴리"} 이런식으로 정리
#     valid_materials = set()
#     for entry in materials_data:
#         name = entry.get("material", "")
#         if "(" in name:
#             name = name.split("(")[0]
#         valid_materials.add(name.strip()) #앞뒤 공백제거

#     # 기준 심볼 정리 // valid_symbols={"wash_95_normal",...} 이런식으로 정리
#     valid_symbols = set()
#     for entry in symbols_data:
#         valid_symbols.update(entry.get("id", []))


#     #얼룩 분류
#     valid_stains = set()
#     frequent_stain_titles=[]
#     food_titles = []
#     life_titles = []
#     food_keywords=[]
#     life_keywords=[]

#     # 사전 정의된 키워드
#     food_keywords = [
#         "커피", "차", "주스", "카레", "토마토", "음식", "과일", "채소", "초콜릿",
#         "적포도주", "아이스크림", "아보카도", "소스", "강황"
#     ]

#     life_keywords = [
#         "녹", "크레용", "왁스", "반려동물", "탈취제", "청바지", "매니큐어", "대변",
#         "소변", "꽃가루", "껌", "섬유 유연제", "땀", "겨드랑이", "윤활유", "기름",
#         "자외선", "먼지", "진흙", "곰팡이", "잔디", "혈흔", "화장품", "펜", "잉크",
#         "세탁", "건조", "모발 염료", "염색약", "페인트", "치약"
#     ]


    

#     for entry in stains_data:

#         category = entry.get("category", "")
#         title = entry.get("title", "")

#         if category == "없음":
#             frequent_stain_titles.append(title)
#         elif category == "음식":
#             food_titles.append(title)
#         elif category == "생활":
#             life_titles.append(title)


#         if title:
#             clean_title = title.replace("제거법", "").strip()
#             valid_stains.add(clean_title)

    
#     materials = []
#     symbols = []
#     stains = []
            
            

#     # OCR 결과 처리
#     ocr_words = set()
#     if filename:
#         ocr_path = os.path.join(base_dir, 'output', f"{os.path.splitext(filename)[0]}_result.json")
#         if os.path.exists(ocr_path):
#             ocr_json = load_json(ocr_path)
#             raw_texts = ocr_json.get("recognized_texts", [])
#             joined_text = " ".join(raw_texts).lower()
#             ocr_words = set(re.findall(r'[가-힣a-zA-Z0-9]+', joined_text))

#     for material in valid_materials:
#         if material.lower() in ocr_words:
#             materials.append(material)

#     for symbol in valid_symbols:
#         if symbol.lower() in ocr_words:
#             symbols.append(symbol)

#         #사용자가 소재 선택
#     if selected_materials:
#         for material in selected_materials:
#             if material in valid_materials:
#                 materials.append(material)



#     # 사용자가 얼룩 선택
#     if selected_stains:
#         for stain in selected_stains:
#             if stain in valid_stains:
#                 stains.append(stain)

#     return {
#         "materials": sorted(set(materials)),
#         "symbols": sorted(set(symbols)),
#         "stains": sorted(set(stains))
#     }


def first_info(filename: str = None,
               selected_materials: list = None,
               selected_stains: list = None) -> dict:

    # 경로 설정
    base_dir = settings.BASE_DIR
    if filename:
        ocr_path = os.path.join(base_dir, 'output', f"{os.path.splitext(filename)[0]}_result.json")
    material_path = os.path.join(base_dir, 'laundry_temp_json', 'blackup.json')
    symbol_path = os.path.join(base_dir, 'laundry_manager', 'washing_symbol.json')
    stain_path = os.path.join(base_dir, 'laundry_temp_json', 'persil_v2.json')

    # 기준 데이터 로드
    materials_data = load_json(material_path).get("material_washing_tips", [])
    symbols_data = load_json(symbol_path)
    stains_data = load_json(stain_path).get("washing_tips_categories", [])

    # 기준 소재 정리
    valid_materials = set()
    for entry in materials_data:
        name = entry.get("material", "")
        if "(" in name:
            name = name.split("(")[0]
        valid_materials.add(name.strip())

    # 기준 심볼 정리
    valid_symbols = set()
    for entry in symbols_data:
        valid_symbols.update(entry.get("id", []))

    # 얼룩 분류
    valid_stains = set()
    for entry in stains_data:
        title = entry.get("title", "")
        if title:
            clean_title = title.replace("제거법", "").strip()
            valid_stains.add(clean_title)

    materials = []
    symbols = []
    stains = []

    # OCR 결과 처리
    ocr_words = set()
    if filename and os.path.exists(ocr_path):
        ocr_json = load_json(ocr_path)
        raw_texts = ocr_json.get("recognized_texts", [])
        joined_text = " ".join(raw_texts).lower()
        ocr_words = set(re.findall(r'[가-힣a-zA-Z0-9]+', joined_text))

    # OCR 기반 필터링
    for material in valid_materials:
        if material.lower() in ocr_words:
            materials.append(material)

    for symbol in valid_symbols:
        if symbol.lower() in ocr_words:
            symbols.append(symbol)

    # ✅ 사용자 선택 소재 (기준과 유사하면 사용자가 선택한 값 그대로 추가)
    if selected_materials:
        for material in selected_materials:
            for valid in valid_materials:
                if material in valid or valid in material:
                    materials.append(material)
                    break

    # ✅ 사용자 선택 얼룩 (기준과 유사하면 사용자가 선택한 값 그대로 추가)
    if selected_stains:
        for stain in selected_stains:
            for valid in valid_stains:
                if stain in valid or valid in stain:
                    stains.append(stain)
                    break

    return {
        "materials": sorted(set(materials)),
        "symbols": sorted(set(symbols)),
        "stains": sorted(set(stains))
    }




# 2차 함수
'''
이름 : final_info
인자 : first_result, manual_materials, manual_symbols, manual_stains
기능 : 사용자가 직접 소재, 심볼, 얼룩정보 변경
'''

def final_info(first_result: dict,
               manual_materials: list = None,
               manual_symbols: list = None,
               manual_stains: list = None) -> dict:
   
    final_materials = set(first_result.get("materials", []))
    final_symbols = set(first_result.get("symbols", []))
    final_stains = set(first_result.get("stains", []))

    if manual_materials:
        final_materials.update(manual_materials)
    if manual_symbols:
        final_symbols.update(manual_symbols)
    if manual_stains:
        final_stains.update(manual_stains)


    final_info={
        "materials": sorted(final_materials),
        "symbols": sorted(final_symbols),
        "stains": sorted(final_stains)

    }
    return final_info