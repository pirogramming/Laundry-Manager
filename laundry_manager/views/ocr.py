# laundry_manager/views/ocr.py
import os
import uuid
import json
from typing import List, Dict, Any, Optional

from django.shortcuts import render, redirect
from django.contrib import messages

from ..forms import ImageUploadForm
from ..utils import (
    perform_ocr,
    get_washing_symbol_definition,
    classify_laundry_symbol,
    load_washing_definitions,
    save_result_json,
    save_classification_result_json,
)

# 룰 엔진 (services/text_rules.py)
# views/ 폴더 기준 상대 경로 주의: '..services'
from ..services.text_rules import (
    analyze_texts,
    load_latest_recognized_texts_from_output,
    extract_rule_keywords,
)

# 세탁 기호 정의 로드(앱 시작 시 1회)
WASHING_SYMBOLS_DEFINITIONS = load_washing_definitions()


def upload_view(request):
    """
    이미지 업로드 → OCR 수행 → 세션 저장 → result 페이지로 리다이렉트
    """
    context: Dict[str, Any] = {
        "form": ImageUploadForm(),
        "uploaded_image_url": None,
        "uploaded_image_name": None,
        "recognized_texts": [],
        "symbol_definition": "",
        "error_message": None,
    }

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 1) 업로드 저장
            uploaded_instance = form.save()
            messages.success(request, "사진이 업로드 됐습니다!")

            image_path = uploaded_instance.image.path
            context["uploaded_image_url"] = uploaded_instance.image.url
            context["uploaded_image_name"] = uploaded_instance.image.name

            # 2) OCR
            ocr_result = perform_ocr(image_path)
            if ocr_result.get("error"):
                context["error_message"] = ocr_result.get("message", "OCR 오류가 발생했습니다.")
                return render(request, "laundry_manager/laundry-upload.html", context)

            # 3) OCR 결과 → 세탁 기호 설명 / 인식 텍스트 추출
            definition, texts = get_washing_symbol_definition(
                ocr_result, WASHING_SYMBOLS_DEFINITIONS
            )

            # 4) 세션 저장 (다음 result 페이지에서 사용)
            request.session["recognized_texts"] = texts or []
            request.session["symbol_definition"] = definition or ""
            request.session["material"] = request.POST.get("material")
            request.session["stains"] = request.POST.getlist("stains")

            # 5) 로깅/디버깅용 결과 JSON 저장 (output/{원본파일명}_result.json)
            save_result_json(image_path, texts, definition, ocr_result)

            # 6) 결과 페이지로 이동
            return redirect("result")

        # form.is_valid()가 아니면 아래로 떨어져 템플릿 렌더링
        context["form"] = form

    return render(request, "laundry_manager/laundry-upload.html", context)


def result_view(request):
    """
    결과 페이지:
      - 세션에서 recognized_texts, material, stains 등을 가져옴
      - (옵션) 세션이 비었을 경우 output 폴더의 최신 *_result.json에서 복구
      - 룰 엔진으로 지시문 생성(instructions)
      - RULES에 정의된 키워드만 추출(rule_keywords)하여 "인식된 기호"에 표시
    """
    texts: List[str] = request.session.get("recognized_texts", [])
    definition: str = request.session.get("symbol_definition", "")
    material: str = request.session.get("material", "")
    stains: List[str] = request.session.get("stains", [])

    # 세션이 비었을 때 직접 접근/새로고침 대비 복구
    if not texts:
        texts = load_latest_recognized_texts_from_output()

    # OCR 텍스트 → 룰 엔진 분석
    instructions = analyze_texts(texts)  # [{code,state,message,...}, ...]

    # OCR 텍스트에서 RULES에 정의된 키워드만 표시용 라벨로 추출
    rule_keywords = extract_rule_keywords(texts)  # ["드라이클리닝", "손세탁", ...]

    return render(
        request,
        "laundry_manager/result.html",
        {
            "recognized_texts": texts,          # 원문 전체(필요하면 숨김/디버깅용)
            "rule_keywords": rule_keywords,     # 화면 "인식된 기호" 표시에 사용
            "symbol_definition": definition,
            "materials": [material] if material else [],
            "stains": stains,
            "instructions": instructions,       # 화면 "세탁 지시문" 표시에 사용
        },
    )


def upload_and_classify(request):
    """
    (별도) 분류 모델만 돌리는 업로드 엔드포인트.
    temp/에 저장 후 분류 → JSON 저장 → temp 삭제
    """
    result: Optional[Dict[str, Any]] = None

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES["image"]

            os.makedirs("temp", exist_ok=True)
            ext = image_file.name.split(".")[-1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join("temp", filename)

            # 파일 저장
            with open(image_path, "wb+") as dst:
                for chunk in image_file.chunks():
                    dst.write(chunk)

            # 분류 수행 및 결과 저장
            result = classify_laundry_symbol(image_path)
            save_classification_result_json(image_path, result)

            # 임시 파일 제거
            try:
                os.remove(image_path)
            except OSError:
                pass
        else:
            # 검증 실패 시 폼 그대로 렌더
            return render(
                request,
                "laundry_manager/laundry-upload.html",
                {"form": form, "result": result},
            )
    else:
        form = ImageUploadForm()

    return render(
        request,
        "laundry_manager/laundry-upload.html",
        {"form": form, "result": result},
    )
