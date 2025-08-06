from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🔹 Swagger/OpenAPI 관련 import
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# 🔹 Swagger 문서 스키마 설정
schema_view = get_schema_view(
    openapi.Info(
        title="Laundry Manager API",
        default_version='v1',
        description="세탁 매니저 프로젝트의 API 명세서입니다.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include('laundry_manager.urls')),  # 앱 메인 연결
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # ✅ Swagger 경로 추가
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# 🔹 미디어 파일 설정 (개발환경에서만)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
