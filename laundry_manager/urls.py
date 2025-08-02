# laundry_manager/urls.py

from django.urls import path
from . import views
from .views import laundry_result_view

urlpatterns = [
    path("", views.upload_and_classify, name="home"),  # 루트 경로는 upload 중심으로 설정
    path("upload/", views.upload_and_classify, name="upload"),
    path("uploadimage/", views.upload_view, name="upload_image"),
    path("info/", laundry_result_view, name="laundry_info"),
    path("result/", laundry_result_view, name="laundry_result"),

    path("laundry/", views.laundry_info_view, name="laundry_view"),
    path("stain_guide/", views.stain_guide_view, name="stain_guide"),
    path("stain_detail/<str:slug>/", views.stain_detail_view, name="stain_detail"),

    path('main/', views.main_page, name='main'),
    path('upload123/', views.upload_page, name='upload'),
    path('result123/', views.result_page, name='result'),  
]
