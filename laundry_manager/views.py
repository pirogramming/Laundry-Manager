from django.shortcuts import render
from functions.recommend import laundry_recommend
from functions.result import format_result
import json, os
from django.conf import settings

def info_check_view(request):
    if request.method == 'GET':
        return render(request, 'laundry_manager/recommend.html')

def laundry_result_view(request):
    if request.method == "POST":
        # 1. info 준비 (예: request.POST나 session, 혹은 laundry_info 함수 활용)
        info = {
            'material': request.POST.get('material'),
            'stains': request.POST.getlist('stains'),
            'symbols': request.POST.getlist('symbols')
        }

        # 2. 세탁 정보 정리한 json 파일 불러오기
        rule_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'laundry_rules.json') # json 파일 이름으로 바꾸기
        with open(rule_path, 'r', encoding='utf-8') as f:
            rule_json = json.load(f) # JSON으로 파싱해서 파이썬 딕셔너리로 변환

        # 3. 세탁 추천 실행
        guides = laundry_recommend(info, rule_json)
        # 4. 출력 포맷
        result_text = format_result(guides)

        # 5. 템플릿에 전달
        return render(request, 'laundry_manager/recommend.html', {'result_text': result_text})
