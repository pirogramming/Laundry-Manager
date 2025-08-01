# laundry-manager/views.py
from django.http import JsonResponse
import os
from functions.info import laundry_info, apply_user_correction

# 2. 뷰 함수 정의
def laundry_info_view(request):

    #추후 경로 수정!!
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")

    ocr_path = os.path.join(DATA_DIR, "ocr_data.json")
    user_path = os.path.join(DATA_DIR, "user_input.json")
    corrected_path = os.path.join(DATA_DIR, "corrected_input.json")

    # 2차 수정 정보가 있으면 반영
    if os.path.exists(corrected_path):
        result = apply_user_correction(ocr_path, user_path, corrected_path)
    else:
        result = laundry_info(ocr_path, user_path)

    # JSON 응답 반환
    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})