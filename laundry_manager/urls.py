# laundry_manager/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # legacy
    # path("", views.upload_and_classify, name="home"),  # 루트 경로는 upload 중심으로 설정
    # path("upload/", views.upload_and_classify, name="upload"),
    # path("uploadimage/", views.upload_view, name="upload_image"),
    # # path("info/", laundry_result_view, name="laundry_info"),
    # # path("result/", laundry_result_view, name="laundry_result"),
    # path("laundry/", views.laundry_info_view, name="laundry_view"),
    # path("stain_guide/", views.stain_guide_view, name="stain_guide"),
    # path("stain_detail/<str:slug>/", views.stain_detail_view, name="stain_detail"),
    path("laundry/", views.laundry_info_view, name="laundry_view"),
    #path("stain_guide/", views.stain_guide_view, name="stain_guide"),
    path("stain_detail/<str:slug>/", views.stain_detail_view, name="stain_detail"),
    
    # 프론트 기본 연결
    path('', views.main_page, name='main'),
    path('laundy-upload/', views.laundry_upload_page, name='laundry-upload'),
    path('stain-upload/', views.stain_guide_view, name="stain_guide"),
    path('result/', views.result_page, name='result'),  
    path('laundry-info/', views.laundry_info_page, name='laundry-info'),  
    #path('stain-guide/', views.stain_guide_page, name='stain-guide'),
    #path('stain-detail/', views.stain_detail_page, name='stain-detail'),
]
