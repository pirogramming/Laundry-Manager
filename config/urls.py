# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    path('', include('laundry_manager.urls')),  # 메인 연결
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # allauth 소셜 로그인
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
