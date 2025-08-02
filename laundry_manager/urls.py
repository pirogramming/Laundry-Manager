from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main'),
    path('upload/', views.upload_page, name='upload'),
    path('result/', views.result_page, name='result'),  
]
