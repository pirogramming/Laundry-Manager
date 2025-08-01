"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from laundry_manager.views import laundry_result_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('laundry/info/', laundry_result_view, name='laundry_info'), #이거 인식 정보 페이지 템플릿이랑 연결하도록 수정
    path('laundry/result/', laundry_result_view, name='laundry_result'),
]
