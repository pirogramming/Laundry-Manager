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

    instructions = analyze_texts(texts)

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
        'instructions': instructions,
    })
