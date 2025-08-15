# laundry_manager/maps.py

import json
import os
from django.shortcuts import render
from django.conf import settings

def map_test_view(request):
    naver_map_client_key = getattr(settings, "NAVER_MAP_CLIENT_KEY", None)
    file_path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'laundromats.json')
    laundromats_data = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            laundromats_data = json.load(f)
    except Exception as e:
        print(f"JSON 파일 처리 오류: {e}")

    context = {
        "naver_map_client_key": naver_map_client_key,
        "laundromats_data": laundromats_data,  # 파이썬 객체를 그대로 전달
    }

    return render(request, "laundry_manager/map-test.html", context)