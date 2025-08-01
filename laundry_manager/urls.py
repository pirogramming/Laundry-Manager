# laundry_manager/urls.py

from django.urls import path
from .views import laundry_info_view

urlpatterns = [
    path('laundry/', laundry_info_view, name='laundry_view'),
]
