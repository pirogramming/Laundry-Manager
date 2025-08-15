# laundry_manager/views/ocr.py
import os
import uuid
import json
from typing import List, Dict, Any, Optional

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from ..forms import ImageUploadForm
from ..utils import (
    perform_ocr,
    get_washing_symbol_definition,
    classify_laundry_symbol,
    load_washing_definitions,
    save_result_json,
    save_classification_result_json,
)

# 룰 엔진
from ..services.text_rules import (
    analyze_texts,
    load_latest_recognized_texts_from_output,
    extract_rule_keywords,
    rules_loaded_count,
    rules_debug_snapshot,
)

# 세션 → 기록 저장 유틸 (이미 작성한 함수)
from .history import save_history_from_session

# 세탁 기호 정의 로드(앱 시작 시 1회)
WASHING_SYMBOLS_DEFINITIONS = load_washing_definitions()


def _relax_seed_texts() -> List[str]:
    """RELAX 컨텍스트 시드"""
    return [
        "세탁 세탁기 물세탁 손세탁 중성세제",
        "표백 염소계 산소계",
        "다리미 다림질 스팀",
        "드라이 드라이클리닝 클리닝",
        "웨트 웨트클리닝 습식",
        "자연건조 건조 햇볕 그늘 옷걸이 텀블 건조기 탈수 짜다 원심",
    ]


def _analyze_with_fallback(texts: List[str], use_relax: bool) -> (List[Dict[str, Any]], bool):
    """룰엔진 분석 + 필요 시 RELAX 1회 재시도"""
    instructions = analyze_texts(texts)
    if instructions:
        return instructions, False
    if use_relax:
        relaxed_texts = (texts or []) + _relax_seed_texts()
        ins2 = analyze_texts(relaxed_texts)
        if ins2:
            return ins2, True
    return [], False


def _coerce_csv(v):
    """리스트/문자열 → 쉼표 문자열"""
    if not v:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple, set)):
        return ", ".join([str(x).strip() for x in v if str(x).strip()])
    return str(v).strip()


@login_required
@require_http_methods(["GET", "POST"])
def upload_view(request):
    """
    이미지 업로드 → OCR → 정의/텍스트 추출 → 룰엔진 분석 → 세션 저장 → ★기록 생성★ → result로 이동
    """
    context: Dict[str, Any] = {
        "form": ImageUploadForm(),
        "uploaded_image_url": None,
        "uploaded_image_name": None,
        "recognized_texts": [],
        "symbol_definition": "",
        "error_message": None,
    }

    if request.method == "GET":
        return render(request, "laundry_manager/laundry-upload.html", context)

    # POST
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        context["form"] = form
        messages.error(request, "이미지를 업로드해 주세요.")
        return render(request, "laundry_manager/laundry-upload.html", context)

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

    # 3) OCR 결과 → 세탁 기호 설명 / 인식 텍스트
    definition, texts = get_washing_symbol_definition(
        ocr_result, WASHING_SYMBOLS_DEFINITIONS
    )

    # 4) 폼에서 넘어온 수동 입력 파싱
    material = (request.POST.get("material") or "").strip()

    # hidden 하나로 넘어오기 때문에 CSV 파싱 필요
    stains_csv = (request.POST.get("stains") or "").strip()
    stains_list = [x.strip() for x in stains_csv.split(",") if x.strip()]

    # 5) 룰엔진 분석 (+RELAX: DEBUG일 때 허용)
    relax_flag = request.GET.get("relax") == "1" or settings.DEBUG is True
    instructions, used_relax = _analyze_with_fallback(texts or [], use_relax=relax_flag)
    rule_keywords = extract_rule_keywords(texts or []) if instructions else []

    # 6) 세션 저장 (결과/기록 공용 키)
    s = request.session
    s["recognized_texts"] = texts or []
    s["symbol_definition"] = definition or ""
    if material:
        s["material"] = material
        s["materials"] = material  # 기록 저장 호환
    s["stains"] = stains_list
    s["instructions"] = instructions  # 템플릿에서 바로 사용 (list[dict])
    s["rule_keywords"] = rule_keywords
    s["symbols"] = rule_keywords or (texts or [])
    s["recommendation_result"] = _coerce_csv(instructions) if isinstance(instructions, (list, tuple)) else (instructions or "")

    # 7) 디버깅용 결과 JSON 저장
    save_result_json(image_path, texts, definition, ocr_result)

    # 8) ★ 기록 생성 ★
    try:
        # 현재 LaundryHistory 모델에는 image 필드가 없으므로 image_file=None 유지
        record = save_history_from_session(request, image_file=None)
    except Exception as e:
        # 기록 실패해도 결과 페이지는 보이게 함
        import logging
        logging.getLogger(__name__).warning("save history failed: %s", e)
        messages.warning(request, f"기록 저장에 실패했습니다: {e}")

    # 9) 결과 페이지로 이동
    return redirect("result")


def result_view(request):
    """
    결과 페이지:
      - 세션에서 recognized_texts, material, stains 등을 가져옴
      - (옵션) 세션이 비었을 경우 output 폴더의 최신 *_result.json에서 복구
      - 룰 엔진으로 지시문 생성(instructions)
      - RULES에 정의된 키워드만 추출(rule_keywords)하여 "인식된 기호"에 표시
      - 아무 것도 안 뜨면 RELAX 모드(컨텍스트 시드)로 1회 재시도
    """
    texts: List[str] = request.session.get("recognized_texts", [])
    definition: str = request.session.get("symbol_definition", "")
    material: str = request.session.get("material", "")
    stains: List[str] = request.session.get("stains", [])

    if not texts:
        texts = load_latest_recognized_texts_from_output()

    # 이미 업로드 단계에서 분석했지만, 세션이 비어있을 수도 있어 안전망 유지
    relax_flag = request.GET.get("relax") == "1" or settings.DEBUG is True
    instructions = request.session.get("instructions")
    used_relax = False
    if not instructions:
        instructions, used_relax = _analyze_with_fallback(texts, use_relax=relax_flag)
        request.session["instructions"] = instructions

    rule_keywords = request.session.get("rule_keywords")
    if instructions and not rule_keywords:
        rule_keywords = extract_rule_keywords(texts)
        request.session["rule_keywords"] = rule_keywords

    # 디버 출력
    debug = rules_debug_snapshot()
    print("[ResultView] OCR 텍스트:", texts)
    print("[ResultView] 지시문 매칭(RELAX=%s): %s" % (used_relax, instructions))
    print("[TextRules DEBUG]", debug)

    rules_load_warning = None if debug.get("loaded_count", 0) > 0 else (
        "세탁 지시문 규칙(JSON)을 불러오지 못했습니다. "
        "BASE_DIR/laundry_manager/json_data/text_rules.json 경로와 형식을 확인하세요."
    )

    return render(
        request,
        "laundry_manager/result.html",
        {
            "recognized_texts": texts,
            "rule_keywords": rule_keywords or [],
            "symbol_definition": definition,
            "materials": [material] if material else [],
            "stains": stains,
            "instructions": instructions or [],
            "used_relax": used_relax,
            "rules_load_warning": rules_load_warning,
        },
    )


@require_http_methods(["GET", "POST"])
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
