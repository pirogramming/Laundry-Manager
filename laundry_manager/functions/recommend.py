import json

with open('persil_v2.json', 'r', encoding='utf-8') as f:
    rule_json = json.load(f)

with open('blackup.json', 'r', encoding='utf-8') as f:
    material_json = json.load(f)


# info는 laundry_info() 함수에서 반환한 정보들을 의미, rule_json은 크롤링한 세탁 방법 json 파일명
def laundry_recommend(info, material_json, rule_json):
    #세탁 정보들 하나씩 추가할 리스트  -> json 형태로 저장
    guides = {
        "material" : None,
        "stains" : [],
        "symbols" : []
    }

    #info로부터 정보 꺼내오기
    material = info.get('material')
    stains = info.get('stains', [])
    symbols = info.get('symbols', []) #세탁 기호는 여러 개일 수도 있는데 배열로 받으면 되려나


    #정보들과 json 연결하기 
    # 1. 소재
    if material in material_json.get('descriptions'):
        guides['material'] = material_json['descriptions'][material]
    
    # 7. 얼룩
    if not stains:
        guides['stains'] = ['특별한 얼룩이 없음']
    else:
        for stain in stains:
            res = rule_json.get('Washing_Steps',{}).get(stain)
            if res:
                guides['stains'].append(res)
    
    # 8. 세탁 기호 # ocr에서 인식한 세탁 기호 정보들을 그대로 가져오면 되는데...!
    for symbol in symbols:
        res = rule_json.get('symbol_rules',{}).get(symbol)
        if res:
            guides['symbols'].append(res)

    # 세탁 정보들 추가해둔 json 반환
    return guides