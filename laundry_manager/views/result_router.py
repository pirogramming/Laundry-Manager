# laundry_manager/views/result_router.py
from django.http import HttpRequest
from . import ocr as ocr_views
from . import result as legacy_views
from django.shortcuts import redirect
import logging
logger = logging.getLogger(__name__)

def result_router_view(request):
    source = (request.GET.get("source")
              or request.session.get("result_source")
              or "ocr")
    logger.info("[ROUTER] source=%s", source)   # ★ 추가

    if source == "legacy":
        from . import result as legacy_views
        return legacy_views.result_view(request)
    from . import ocr as ocr_views
    return ocr_views.result_view(request)

