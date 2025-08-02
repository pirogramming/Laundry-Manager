# laundry_manager/urls.py
from django.urls import path
from . import views
from .views import laundry_result_view


urlpatterns = [
    path("", views.upload_and_classify, name="home"),  # 루트 경로에 연결
    path("upload/", views.upload_and_classify, name="upload"),
    path('uploadimage/', views.upload_view, name='upload_image'),
    path('info/', laundry_result_view, name='laundry_info'), #이거 인식 정보 페이지 템플릿이랑 연결하도록 수정
    path('result/', laundry_result_view, name='laundry_result'),
    
]

