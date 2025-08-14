# laundry_manager/views.py

from django.shortcuts import render
from django.conf import settings


def map_test_view(request):
    """
    지도를 렌더링하고 API 키를 전달하는 뷰
    """
    naver_map_client_key = getattr(settings, "NAVER_MAP_CLIENT_KEY")

    context = {
        "naver_map_client_key": naver_map_client_key,
    }
    return render(request, "laundry_manager/map-test.html", context)
