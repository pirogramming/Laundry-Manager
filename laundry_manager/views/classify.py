# laundry_manager/views/classify.py
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from ..forms import ImageUploadForm  # 기존 폼 경로에 맞춰 조정
from .roboflow_client import classify_file

def classify_symbol_view(request):
    """
    이미지 업로드 -> Roboflow 분류 -> 결과 출력
    """
    context = {
        "form": ImageUploadForm(),
        "rf_enabled": settings.RF_ENABLED,
        "result": None,
        "error": None,
    }

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save()
            image_path = instance.image.path
            result = classify_file(image_path)
            context["form"] = form
            context["result"] = result
            if not result.get("ok"):
                context["error"] = result.get("error") or "분류 실패"
                messages.error(request, f"분류 실패: {context['error']}")
        else:
            context["form"] = form
            context["error"] = "유효하지 않은 업로드입니다."
    return render(request, "laundry_manager/roboflow.html", context)
