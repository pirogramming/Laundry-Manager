# laundry_manager/urls.py

from django.urls import path
from . import views
# from .views import UploadView

urlpatterns = [
    path('', views.main_page, name='main'),
    path("upload/", views.upload_and_classify, name="upload"),
    path("uploadimage/", views.upload_view, name="upload_image"),
    path("stain-guide/", views.stain_guide_view, name="stain-guide"),
    path("stain_detail/<str:slug>/", views.stain_detail_view, name="stain_detail"),
    path("laundry/", views.laundry_info_view, name="laundry_view"),
    path('laundry-upload/', views.upload_view, name='laundry-upload'),
    path("stain-upload/", views.stain_guide_view, name="stain-upload"), 
    path("stain-info/", views.stain_info_page, name="stain-info"),
    # path('stain-upload/', views.stain_upload_page, name='stain-upload'),
    path('result/', views.result_view, name='result'),  
    path('laundry-info/', views.laundry_info_page, name='laundry-info'),  
    path('stain-info/', views.stain_info_page, name='stain-info'),
    path('first-info/', views.first_info_view, name='first_info'),
    path('final-info/', views.final_info_view, name='final_info'),
    # path('laundry-upload/', UploadView.as_view(), name='laundry-upload'),
    path('laundry-info-v1/', views.laundry_info_view1, name='laundry-info-v1'),
    path('records/', views.record_list_view, name='record_list'),
    path('record/<int:pk>/', views.record_detail_view, name='record-detail'),
    path('profile/', views.profile_view, name='profile'),


]
