# laundry_manager/views/result.py
from django.shortcuts import render
from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output

def result_view(request):
    # 세션 기반 기본값
    texts = request.session.get('recognized_texts', [])
    definition = request.session.get('symbol_definition', '')
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])

    # 세션에 없으면(새로고침/직접접속 등) output 최신 파일에서 복구 (옵션)
    if not texts:
        texts = load_latest_recognized_texts_from_output()

    # 룰 분석
    instructions = analyze_texts(texts)

    # 인식된 기호(짧은 키워드) 리스트 생성: label → keyword → description 폴백, 중복 제거
    seen = set()
    rule_keywords = []
    for ins in instructions:
        lbl = (ins.get("label") or ins.get("keyword") or ins.get("message") or "").strip()
        if lbl and lbl not in seen:
            seen.add(lbl)
            rule_keywords.append(lbl)

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
        'instructions': instructions,
        'rule_keywords': rule_keywords,  # ✅ 템플릿에서 {{ rule_keywords|join:", " }} 로 표시
    })
