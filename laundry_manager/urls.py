# laundry_manager/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # legacy
    # path("", views.upload_and_classify, name="home"),  # 루트 경로는 upload 중심으로 설정
    path("upload/", views.upload_and_classify, name="upload"),
    path("uploadimage/", views.upload_view, name="upload_image"),
    # path("info/", laundry_result_view, name="laundry_info"),
    # path("result/", laundry_result_view, name="laundry_result"),
    # path("laundry/", views.laundry_info_view, name="laundry_view"),
    # path("stain_guide/", views.stain_guide_view, name="stain_guide"),
    # path("stain_detail/<str:slug>/", views.stain_detail_view, name="stain_detail"),

    # 프론트 기본 연결
    path('', views.main_page, name='main'),
    path('laundy-upload/', views.laundry_upload_page, name='laundry-upload'),
    path('stain-upload/', views.stain_upload_page, name='stain-upload'),
    path('result/', views.result_view, name='result'),  
    path('laundry-info/', views.laundry_info_page, name='laundry-info'),  

    path('first-info/', views.first_info_view, name='first_info'),
    path('final-info/', views.final_info_view, name='final_info'),

]
