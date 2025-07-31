# laundry_manager/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_and_classify, name="home"),  # 루트 경로에 연결
    path("upload/", views.upload_and_classify, name="upload"),
]
