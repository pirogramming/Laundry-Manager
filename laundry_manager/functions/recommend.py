import json

with open('blackup.json', 'r', encoding='utf-8') as f:
    material_json = json.load(f)

with open('persil_v2.json', 'r', encoding='utf-8') as f:
    stain_json = json.load(f)

#ocr에서 세탁 기호 정보 받아온 json
with open('8843acc602414e1e9fe6d93c48e7386f_classify.json', 'r', encoding='utf-8') as f:
    symbol_json = json.load(f)


# 소재 정보 추출
def get_material_guide(material, material_json):

    for material_info in material_json.get('material_washing_tips', []):
        if material_info.get("material") == material:
            return {
                "description": material_json.get("description", "정보 없음"),
                "warning": material_json.get("warning", "주의사항 없음")
            }
    return None


def get_stain_guide(stains, stain_json):
    # 얼룩 정보 정리

    for stain_info in stain_json.get('washing_tips_categories', []):
        if stain_info.get('title') == stains:
            return {
                "Washing_Steps": stain_json.get("Washing_Steps"),
                "Not_to_do": stain_json.get("not_to_do"),
                "Tips": stain_json.get("tip", "팁 없음")
            }
    return "특별한 얼룩이 없음"


def get_symbol_guide(symbols, symbol_json):
    # 세탁 기호 정보 정리
    symbol_results = []
    for symbol in symbols:
        res = symbol_json.get('classification_result', {}).get(symbol)
        if res:
            symbol_results.append(res)
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


#laundry_info()
#→ 유저가 선택한 소재, 얼룩, 세탁 기호 정보를 딕셔너리 형태로 반환.

#get_material_guide(material, material_json)
#→ 소재 정보(description, warning) 반환.

#get_stain_guides(stains, stain_json)
#→ 입력된 얼룩 리스트에 따라 세탁 방법 반환.

#get_symbol_guides(symbols, symbol_json)
#→ 세탁 기호에 따라 세탁 방법 반환.

#laundry_recommend(info, material_json, stain_json, symbol_json)
#→ 위 함수들을 조합하여 material_guide, stain_guide, symbol_guide 세 개로 나눠서 반환.

#format_result()
#→ 위의 세 가지 가이드를 하나의 보기 좋은 문장/표 형태로 포맷.