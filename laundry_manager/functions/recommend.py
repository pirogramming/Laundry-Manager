# info는 laundry_info() 함수에서 반환한 정보들을 의미, rule_json은 크롤링한 세탁 방법 json 파일명
def laundry_recommend(info, rule_json):
    #세탁 정보들 하나씩 추가할 리스트  -> json 형태로 저장
    guides = {
        "material" : None,
        "color" : None,
        "category" : None,
        "thickness" : None,
        "sensitivity" : None,
        "composition" : None,
        "stains" : [],
        "symbols" : []
    }

    #info로부터 정보 꺼내오기
    material = info.get('material')
    stains = info.get('stains', [])
    symbols = info.get('symbols', []) #세탁 기호는 여러 개일 수도 있는데 배열로 받으면 되려나


    #정보들과 rule_json 연결하기 --> 엄청 반복되니까 함수 하나 정의해서 간단하게 만들어도 될 듯! 
    # 1. 소재
    if material in rule_json.get('material_rules'):
        guides['material'] = rule_json['material_rules'][material]
    
    # 7. 얼룩
    if not stains:
        guides['stains'] = ['특별한 얼룩이 없음']
    else:
        for stain in stains:
            res = rule_json.get('stain_rules',{}).get(stain)
            if res:
                guides['stains'].append(res)
    
    # 8. 세탁 기호 
    for symbol in symbols:
        res = rule_json.get('symbol_rules',{}).get(symbol)
        if res:
            guides['symbols'].append(res)

    # 세탁 정보들 추가해둔 json 반환
    return guides