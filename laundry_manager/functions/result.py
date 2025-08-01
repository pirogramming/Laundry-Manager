def format_result(guides):
    format_text = []

    #소재에 따른 추천
    if guides.get('material'):
        format_text.append(f"🧵 의류 소재에 따른 팁: {guides['material']}")

    # 얼룩에 따른 추천
    stains = guides.get('stains', [])
    if stains:
        format_text.append("🧼 얼룩 관련 팁:")
        for stain in stains:
            format_text.append(f" - {stain}")

    # 세탁 기호에 따른 추천
    symbols = guides.get('symbols', [])
    if symbols:
        format_text.append("🚫 세탁 기호 관련 팁:")
        for symbol in symbols:
            format_text.append(f" - {symbol}")

    return "\n".join(format_text)

    #전반적인 틀이 세탁 순서를 보기 좋게 제시하고, 하면 안되는 not to do랑, 안 될 경우의 팁 이렇게 세 단계로 수정해야함