# laundry_manager/views/result.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.text_rules import analyze_texts, load_latest_recognized_texts_from_output
from ..models import LaundryHistory

def _ensure_history(request, materials, stains, symbols):
    """로그인 시 세션에 history_id 없으면 하나 만들고 반환."""
    if not request.user.is_authenticated:
        return None
    hid = request.session.get("history_id")
    history = None
    if hid:
        try:
            history = LaundryHistory.objects.get(pk=hid, user=request.user)
        except LaundryHistory.DoesNotExist:
            history = None
    if not history:
        history = LaundryHistory.objects.create(
            user=request.user,
            materials=", ".join(materials) if materials else "",
            stains=(stains[0] if stains else ""),
            symbols=", ".join(symbols) if symbols else "",
        )
        request.session["history_id"] = history.id
    return history

def result_view(request):
    texts = request.session.get('recognized_texts', [])
    definition = request.session.get('symbol_definition', '')
    material = request.session.get('material', '')
    stains = request.session.get('stains', [])
    symbols = request.session.get('symbols', [])

    if not texts:
        texts = load_latest_recognized_texts_from_output()

    instructions = analyze_texts(texts)

    # ✅ 로그인 시 History 1건 보장
    history = _ensure_history(
        request,
        materials=[material] if material else [],
        stains=stains,
        symbols=symbols,
    )

    return render(request, 'laundry_manager/result.html', {
        'recognized_texts': texts,
        'symbol_definition': definition,
        'materials': [material] if material else [],
        'stains': stains,
        'symbols': symbols,
        'instructions': instructions,
        'history': history,   # 👈 템플릿에서 hidden/input/링크에 사용
    })
