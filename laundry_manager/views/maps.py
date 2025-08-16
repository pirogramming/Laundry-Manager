# # laundry_manager/maps.py

# import json
# import os
# from django.shortcuts import render
# from django.conf import settings

# def map_test_view(request):
#     naver_map_client_key = getattr(settings, "NAVER_MAP_CLIENT_KEY", None)
#     file_path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'laundromats.json')
#     laundromats_data = []

#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             laundromats_data = json.load(f)
#     except Exception as e:
#         print(f"JSON 파일 처리 오류: {e}")

#     context = {
#         "naver_map_client_key": naver_map_client_key,
#         "laundromats_data": laundromats_data,  # 파이썬 객체를 그대로 전달
#     }

#     return render(request, "laundry_manager/map-test.html", context)


# laundry_manager/maps.py
'''
import json
import os
from django.shortcuts import render
from django.conf import settings


def map_test_view(request):
    """
    지도를 렌더링하고, JSON 파일의 전체 데이터를 템플릿으로 전달하는 뷰
    """
    naver_map_client_key = getattr(settings, "NAVER_MAP_CLIENT_KEY", None)
    
    file_path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'laundromats.json')
    laundromats_data = {}  # 기본값으로 빈 딕셔너리 설정

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
'''

# laundry_manager/maps.py

import json
import os
from django.conf import settings
from datetime import datetime, time

def is_shop_open_py(shop):
    """영업시간 판단 함수 (수정 없음)"""
    # ... (기존 is_shop_open_py 함수 내용은 그대로 복사) ...
    hours_info = shop.get('hours')
    if hours_info is True: return True
    if not isinstance(hours_info, dict): return False
    now = datetime.now()
    day_map = ['월', '화', '수', '목', '금', '토', '일']
    today_str = day_map[now.weekday()]
    today_hours_string = hours_info.get('days', {}).get(today_str, hours_info.get('default', ''))
    if today_hours_string == 'default': today_hours_string = hours_info.get('default', '')
    if not today_hours_string or today_hours_string == "휴무": return False
    if "24시간" in today_hours_string: return True
    try:
        start_str, end_str = today_hours_string.split(' - ')
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        if start_time > end_time: return now.time() >= start_time or now.time() < end_time
        else: return start_time <= now.time() < end_time
    except (ValueError, AttributeError): return False


def get_map_data():
    """
    지도에 필요한 데이터를 가공하여 딕셔너리 형태로 반환하는 함수
    """
    file_path = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'laundromats.json')
    raw_data = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"JSON 파일 처리 오류: {e}")

    transformed_stores = []
    store_id_counter = 1
    all_raw_shops = raw_data.get('sinchon', []) + raw_data.get('kondae', [])

    for shop in all_raw_shops:
        products_list = []
        if shop.get('self'): products_list.append('셀프 빨래방')
        if shop.get('dry_cleaning'): products_list.append('드라이클리닝')
        if shop.get('shoes'): products_list.append('운동화 세탁')

        rating_value = shop.get('rating')
        final_rating = rating_value if isinstance(rating_value, (int, float)) else 0.0

        transformed_stores.append({
            'id': f"store_{store_id_counter}",
            'name': shop.get('name', '이름 없음'),
            'rating': final_rating,
            'openNow': is_shop_open_py(shop),
            'address': shop.get('address', ''),
            'products': products_list,
            'phone': shop.get('phone_number') or shop.get('phone', '번호 없음')
        })
        store_id_counter += 1

    context = {
        "naver_map_client_key": settings.NAVER_MAP_CLIENT_KEY,
        # 이제 stores_data는 객체가 아닌 단일 배열입니다.
        "stores_data": transformed_stores,
    }
    
    return context