import os
from django.conf import settings
import json

json_dir = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data')

with open(os.path.join(json_dir, 'blackup.json'), 'r', encoding='utf-8') as f:
    material_json = json.load(f)

with open(os.path.join(json_dir, 'persil_v2.json'), 'r', encoding='utf-8') as f:
    stain_json = json.load(f)

with open(os.path.join(json_dir, 'washing_symbol.json'), 'r', encoding='utf-8') as f:
    symbol_json = json.load(f)



# 소재 정보 추출
def get_material_guide(material, material_json):

    for material_info in material_json.get('material_washing_tips', []):
        if material_info.get("material") == material:
            return {
                "description": material_info.get("description", "정보 없음"),
                "warning": material_info.get("warning", "주의사항 없음")
            }
    return None


def get_stain_guide(stains, stain_json):
    # 얼룩 정보 정리

    for stain_info in stain_json.get('washing_tips_categories', []):
        if stain_info.get('title') == stains:
            return {
                "Washing_Steps": stain_info.get("Washing_Steps"),
                "Not_to_do": stain_info.get("not_to_do"),
                "Tips": stain_info.get("tip", "팁 없음")
            }
    return "특별한 얼룩이 없음"

# 세탁 기호 키워드들이랑 인식된 기호 텍스트의 유사도 판별하는 함수 
def is_similar(keyword, user_input):
    return keyword in user_input or user_input in keyword


def get_symbol_guide(symbols, symbol_json):
    symbol_results = []

    for user_input in symbols:
        for item in symbol_json:
            for keyword in item.get("keywords", []):
                if is_similar(keyword, user_input):
                    symbol_results.append(item["description"])
                    break  # 한 항목 매칭되면 다음 user_input으로
            else:
                continue
            break  # 중첩된 for문 빠져나오기

    return symbol_results


def laundry_recommend(info, material_json, stain_json, symbol_json):
    # laundry_info() 함수에서 반환한 info에서 소재, 얼룩, 세탁 기호 받아 오기
    material = info.get('material')
    stains = info.get('stains')
    symbols = info.get('symbols', [])

    guides = {
        "material_guide": get_material_guide(material, material_json),
        "stain_guide": get_stain_guide(stains, stain_json),
        "symbol_guide": get_symbol_guide(symbols, symbol_json)
    }

    return guides