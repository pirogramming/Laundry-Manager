# laundry_manager/views/result_router.py
from django.http import HttpRequest
from . import ocr as ocr_views
from . import result as legacy_views

def result_router_view(request: HttpRequest):
    """
    결과 페이지 라우터.
    우선순위: GET ?source=.. → 세션 result_source → 기본값('ocr')
    """
    source = (request.GET.get("source") or
              request.session.get("result_source") or
              "ocr")

    if source == "legacy":
        return legacy_views.result_view(request)
    # 기본은 OCR 결과 화면
    return ocr_views.result_view(request)
