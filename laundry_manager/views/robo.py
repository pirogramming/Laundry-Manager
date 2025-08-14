import os, uuid
from django.shortcuts import render
from ..forms import ImageUploadForm
from ..utils import (
    classify_laundry_symbol,
    save_classification_result_json,
)

# 이거는 roboflow에서 사용되는 함수임
def upload_and_classify(request):
    result = None
    form = ImageUploadForm()

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES["image"]

            # 임시 저장 경로 생성
            os.makedirs("temp", exist_ok=True)
            ext = image_file.name.split(".")[-1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join("temp", filename)

            try:
                # 파일 저장
                with open(image_path, "wb+") as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)

                # roboflow 분류
                result = classify_laundry_symbol(image_path)

                # json 저장
                save_classification_result_json(image_path, result)

            finally:
                try:
                    if os.path.exists(image_path):
                        # 임시 파일 삭제
                        os.remove(image_path)
                except Exception:
                    pass

    return render(request, "laundry_manager/laundry-upload.html", {
            "form": form,
            "result": result,
        },
    )