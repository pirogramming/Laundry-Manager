from django.urls import path
from .views import laundry_result_view

urlpatterns = [
    path('info/', laundry_result_view, name='laundry_info'), #이거 인식 정보 페이지 템플릿이랑 연결하도록 수정
    path('result/', laundry_result_view, name='laundry_result'),
]

    