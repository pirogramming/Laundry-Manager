from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),
    path('laundy-upload/', views.laundry_upload_page, name='laundry-upload'),
    path('stain-upload/', views.stain_upload_page, name='stain-upload'),
    path('result/', views.result_page, name='result'),  
    path('laundry-info/', views.laundry_info_page, name='laundry-info'),  
]
