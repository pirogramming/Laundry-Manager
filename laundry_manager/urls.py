from django.urls import path
from . import views

app_name = 'laundry_app'

urlpatterns = [
    path('', views.upload_view, name='upload_image'),
]