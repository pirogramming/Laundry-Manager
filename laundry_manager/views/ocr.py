# laundry_manager/views/ocr.py
import os
import uuid
import json
from typing import List, Dict, Any, Optional
import logging
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from ..services.modal_data import load_material_items, load_stain_titles

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

logger = logging.getLogger(__name__)

logger.info("WASHING_SYMBOLS_DEFINITIONS loaded: %s items",
            len(WASHING_SYMBOLS_DEFINITIONS or []))

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


# @login_required
@require_http_methods(["GET", "POST"])
def upload_view(request):
    """
    이미지 업로드 → OCR → 정의/텍스트 추출 → 룰엔진 분석 → 세션 저장 → ★기록 생성★ → result로 이동
    - rule_keywords: 항상 추출 시도(룰 매칭 실패해도), 비면 OCR 텍스트로 폴백
    - 디버그: trace_id로 업로드~결과까지 추적
    """
    logger = logging.getLogger(__name__)

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

    # --- trace id (업로드~결과까지 같은 세션으로 추적) ---
    trace_id = request.session.get("trace_id") or uuid.uuid4().hex[:8]
    request.session["trace_id"] = trace_id
    logger.info("[UPL:%s] upload start", trace_id)

    # POST
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        logger.warning("[UPL:%s] invalid form errors=%s", trace_id, form.errors)
        context["form"] = form
        messages.error(request, "이미지를 업로드해 주세요.")
        return render(request, "laundry_manager/laundry-upload.html", context)

    # 1) 업로드 저장
    uploaded_instance = form.save()
    messages.success(request, "사진이 업로드 됐습니다!")
    image_path = uploaded_instance.image.path
    context["uploaded_image_url"] = uploaded_instance.image.url
    context["uploaded_image_name"] = uploaded_instance.image.name
    logger.info("[UPL:%s] saved image name=%s path=%s",
                trace_id, uploaded_instance.image.name, image_path)

    # 2) OCR
    ocr_result = perform_ocr(image_path)
    if ocr_result.get("error"):
        logger.error("[UPL:%s] OCR error: %s", trace_id, ocr_result)
        context["error_message"] = ocr_result.get("message", "OCR 오류가 발생했습니다.")
        return render(request, "laundry_manager/laundry-upload.html", context)

    # 3) OCR 결과 → 세탁 기호 설명 / 인식 텍스트
    definition, texts = get_washing_symbol_definition(
        ocr_result, WASHING_SYMBOLS_DEFINITIONS
    )
    logger.debug("[UPL:%s] texts(len=%d)=%s", trace_id, len(texts or []), texts)
    logger.debug("[UPL:%s] definition(snippet)=%s", trace_id, (definition or "")[:120])

    # 4) 폼에서 넘어온 수동 입력 파싱
    material = (request.POST.get("material") or "").strip()
    stains_csv = (request.POST.get("stains") or "").strip()  # hidden 하나(CSV)
    stains_list = [x.strip() for x in stains_csv.split(",") if x.strip()]
    logger.debug("[UPL:%s] material=%s stains=%s", trace_id, material, stains_list)

    # 5) 룰엔진 분석 (+RELAX: DEBUG일 때 허용)
    relax_flag = request.GET.get("relax") == "1" or settings.DEBUG is True
    instructions, used_relax = _analyze_with_fallback(texts or [], use_relax=relax_flag)
    logger.debug("[UPL:%s] instructions(len=%d) used_relax=%s",
                trace_id, len(instructions or []), used_relax)

    # 🔧 핵심: 매칭 여부와 무관하게 키워드 추출 + 폴백
    rk = extract_rule_keywords(texts or []) or []               # list[str]
    symbols_for_display = rk if rk else (texts or [])           # 화면 표시용
    logger.info("[UPL:%s] rule_keywords(len=%d)=%s",
                trace_id, len(rk), rk if rk else "<empty>")
    if not rk:
        logger.warning("[UPL:%s] rule_keywords empty -> fallback to OCR texts", trace_id)

    # 6) 세션 저장 (결과/기록 공용 키)
    s = request.session
    s["recognized_texts"] = texts or []
    s["symbol_definition"] = definition or ""
    if material:
        s["material"] = material
        s["materials"] = material  # 기록 저장 호환
    s["stains"] = stains_list
    s["instructions"] = instructions or []                     # list[dict]
    s["rule_keywords"] = rk                                     # 템플릿 1순위
    s["symbols"] = symbols_for_display                          # 폴백 포함
    s["recommendation_result"] = (
        _coerce_csv(instructions) if isinstance(instructions, (list, tuple))
        else (instructions or "")
    )
    logger.debug(
        "[UPL:%s] session set: %s",
        trace_id,
        {k: bool(s.get(k)) for k in
        ["recognized_texts","symbol_definition","material","stains","instructions","rule_keywords","symbols"]}
    )

    # 7) 디버깅용 결과 JSON 저장
    save_result_json(image_path, texts, definition, ocr_result)

    # 8) ★ 기록 생성 ★
    try:
        record = save_history_from_session(request, image_file=None)
        logger.info("[UPL:%s] history saved id=%s", trace_id, getattr(record, "id", None))
    except Exception as e:
        logger.warning("[UPL:%s] save history failed: %s", trace_id, e)
        messages.warning(request, f"기록 저장에 실패했습니다: {e}")

    # 9) 결과 페이지로 이동
    logger.info("[UPL:%s] redirect -> result", trace_id)
    return redirect("result")


def result_view(request):
    trace_id = request.session.get("trace_id", "no-trace")
    texts = request.session.get("recognized_texts", [])
    definition = request.session.get("symbol_definition", "")
    material = request.session.get("material", "")
    stains = request.session.get("stains", [])

    if not texts:
        texts = load_latest_recognized_texts_from_output()
        logger.info("[RES:%s] texts loaded from output folder: %d", trace_id, len(texts or []))

    relax_flag = request.GET.get("relax") == "1" or settings.DEBUG is True
    instructions = request.session.get("instructions")
    used_relax = False
    if not instructions:
        instructions, used_relax = _analyze_with_fallback(texts, use_relax=relax_flag)
        request.session["instructions"] = instructions

    rule_keywords = request.session.get("rule_keywords") or []
    if not rule_keywords:
        from django.utils.html import escape
        rule_keywords = extract_rule_keywords(texts or []) or []
        request.session["rule_keywords"] = rule_keywords
        logger.warning("[RES:%s] rule_keywords was empty, re-extracted -> len=%d", trace_id, len(rule_keywords))

    # 최종 표시용
    symbols = request.session.get("symbols") or (rule_keywords if rule_keywords else (texts or []))
    request.session["symbols"] = symbols

    debug = rules_debug_snapshot()
    logger.info("[RES:%s] ctx: texts=%d, rk=%d, symbols=%d, instructions=%d, used_relax=%s, rules_loaded=%d",
                trace_id, len(texts or []), len(rule_keywords or []), len(symbols or []),
                len(instructions or []), used_relax, debug.get("loaded_count", 0))
    if not debug.get("loaded_count", 0):
        logger.error("[RES:%s] text_rules.json not loaded", trace_id)

    # 템플릿에서 바로 펼쳐볼 수 있게 JSON 문자열 전달(디버그 전용)
    import json as _json
    debug_dump = {
        "trace_id": trace_id,
        "recognized_texts": texts,
        "rule_keywords": rule_keywords,
        "symbols": symbols,
        "materials": [material] if material else [],
        "stains": stains,
        "instructions_len": len(instructions or []),
        "rules_loaded_count": debug.get("loaded_count", 0),
    }
    debug_json = _json.dumps(debug_dump, ensure_ascii=False, indent=2)

    material_items = load_material_items()
    stain_titles   = load_stain_titles()

    return render(
        request,
        "laundry_manager/result.html",
        {
            "recognized_texts": texts,
            "rule_keywords": rule_keywords or [],
            "symbols": request.session.get("symbols") or (rule_keywords if rule_keywords else (texts or [])),
            "symbol_definition": definition,
            "materials": [material] if material else [],
            "stains": stains,
            "instructions": instructions or [],
            "used_relax": used_relax,
            # ⬇️ 모달 칩 데이터
            "material_items": material_items,
            "stain_titles": stain_titles,
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

@require_POST
def clear_result(request):
    """
    결과 화면에서 누르면 세션에 저장된 인식 결과를 비우고 업로드 화면으로 이동.
    옵션(delete_output=1)일 때 output 폴더의 *_result.json도 함께 삭제.
    """
    # 1) 세션 키 제거
    for key in ("recognized_texts", "symbol_definition", "material", "stains"):
        request.session.pop(key, None)

    # 2) output/*.json 삭제 (선택)
    if request.POST.get("delete_output") == "1":
        try:
            output_dir = os.path.join(settings.BASE_DIR, "output")
            if os.path.isdir(output_dir):
                for fname in os.listdir(output_dir):
                    if fname.endswith("_result.json"):
                        try:
                            os.remove(os.path.join(output_dir, fname))
                        except OSError:
                            pass
            messages.success(request, "세션 기록과 저장된 결과 파일을 삭제했어요.")
        except Exception as e:
            messages.warning(request, f"파일 삭제 중 오류가 발생했어요: {e}")
    else:
        messages.success(request, "세션 기록을 삭제했어요.")

    # 원하는 곳으로 리다이렉트 (업로드 화면으로 복귀)
    return redirect("laundry-upload")