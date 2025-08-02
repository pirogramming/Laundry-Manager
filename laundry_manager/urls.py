# laundry_manager/urls.py

# laundry_manager/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.stain_guide_view, name="home"),
    path("laundry/", views.laundry_info_view, name="laundry_view"),
    path("stain_guide/", views.stain_guide_view, name="stain_guide"),
    path("stain_detail/<str:slug>/", views.stain_detail_view, name="stain_detail"),
]
