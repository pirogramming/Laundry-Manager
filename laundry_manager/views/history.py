# laundry_manager/views/history.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from ..models import LaundryHistory, UploadedImage
from ..forms import WashingUploadForm

User = get_user_model()

# --- 추가 import ---
import os, json
from django.conf import settings
import logging

# --- 캐시 ---
_MATERIALS_JSON = None
_STAINS_JSON = None
_SYMBOLS_JSON = None
logger = logging.getLogger(__name__)


def _json_path(*names):
    """
    BASE_DIR / laundry_manager / json_data / <names...>
    """
    return os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", *names)


def _load_json_safely(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _norm_material_name(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # '면(Cotton)' -> '면'
    return s.split("(", 1)[0].strip() or s


def _get_material_obj(material_name: str) -> dict:
    """
    blackup.json을 읽어 어떤 스키마든 다음 형태로 정규화:
      [{"material": "...", "description": "...", "warning": "..."}]
    """
    global _MATERIALS_JSON
    if _MATERIALS_JSON is None:
        data = _load_json_safely(_json_path("blackup.json"), {})
        raw = data.get("material_washing_tips")
        if raw is None:
            raw = data.get("materials")

        normalized = []
        if isinstance(raw, dict):
            # 예: {"면(Cotton)": {"description":"..","warning":".."}, ...}
            for label, val in raw.items():
                row = {"material": str(label).strip(), "description": None, "warning": None}
                if isinstance(val, dict):
                    row["description"] = val.get("description")
                    row["warning"] = val.get("warning")
                else:
                    # 값이 그냥 문자열이면 description으로 사용
                    row["description"] = str(val).strip()
                normalized.append(row)

        elif isinstance(raw, list):
            # 예: [{"material":"면(Cotton)","description":".."}, "폴리(Poly)", ...]
            for val in raw:
                if isinstance(val, dict):
                    normalized.append({
                        "material": (val.get("material") or val.get("name") or "").strip(),
                        "description": val.get("description"),
                        "warning": val.get("warning"),
                    })
                elif isinstance(val, str):
                    normalized.append({"material": val.strip(), "description": None, "warning": None})

        else:
            normalized = []  # 알 수 없는 구조

        _MATERIALS_JSON = normalized

    target = _norm_material_name(material_name)

    # 1) 완전 일치(정규화 기준)
    for row in _MATERIALS_JSON:
        label = (row.get("material") or row.get("name") or "").strip()
        if _norm_material_name(label) == target and target:
            return {
                "name": material_name or label,
                "description": row.get("description"),
                "warning": row.get("warning"),
            }

    # 2) 부분 일치(정규화 기준)
    for row in _MATERIALS_JSON:
        label = (row.get("material") or row.get("name") or "").strip()
        nlabel = _norm_material_name(label)
        if target and (target in nlabel or nlabel in target):
            return {
                "name": material_name or label,
                "description": row.get("description"),
                "warning": row.get("warning"),
            }

    # 3) 폴백
    return {"name": material_name or "", "description": None, "warning": None}


def _get_stain_obj(stain_title: str) -> dict:
    """
    persil_v2.json 예시 스키마:
    { "washing_tips_categories":[
        {"title":"혈흔","Washing_Steps":[...],"Not_to__do":[...]}, ...
      ]
    }
    """
    global _STAINS_JSON
    if _STAINS_JSON is None:
        data = _load_json_safely(_json_path("persil_v2.json"), {})
        _STAINS_JSON = data.get("washing_tips_categories", [])

    stain_title = (stain_title or "").strip()
    for row in _STAINS_JSON:
        if row.get("title") == stain_title:
            return {
                "Washing_Steps": row.get("Washing_Steps") or [],
                # 템플릿 호환(대소/언더스코어 차이 모두 대응)
                "not_to_do": row.get("not_to_do") or row.get("Not_to_do") or row.get("Not_to__do"),
                "Not_to__do": row.get("Not_to__do") or row.get("Not_to_do") or row.get("not_to_do"),
            }
    return {"Washing_Steps": [], "not_to_do": None, "Not_to__do": None}


def _load_symbols_json():
    """
    washing_symbol.json 스키마가 dict 또는 list일 수 있어 둘 다 대응.
    - dict: { "1": {...}, "2": {...} }
    - list: [ {"id":1,"meaning_kr":"...", "type":"wash|dry"}, ... ]
    """
    global _SYMBOLS_JSON
    if _SYMBOLS_JSON is None:
        _SYMBOLS_JSON = _load_json_safely(_json_path("washing_symbol.json"), {})
    return _SYMBOLS_JSON


def _symbol_meta_from_id(symbols_json, sid):
    """
    sid(int/str)에 해당하는 메타 반환. 없으면 None.
    """
    if isinstance(symbols_json, dict):
        return symbols_json.get(str(sid)) or symbols_json.get(int(sid)) if isinstance(sid, int) else None
    if isinstance(symbols_json, list):
        for it in symbols_json:
            if str(it.get("id")) == str(sid):
                return it
    return None


def _split_symbol_descriptions(symbols_csv_or_list):
    """
    symbols: CSV 또는 리스트.
    반환: (washing_descriptions, drying_descriptions, all_symbol_texts)
    """
    symbols_json = _load_symbols_json()

    washing, drying, all_texts = [], [], []
    for raw in _as_list(symbols_csv_or_list):
        # 숫자 id로 보이면 JSON에서 찾아보고, 아니면 그대로 텍스트로 취급
        text = None
        typ = ""

        is_digit = raw.isdigit()
        meta = _symbol_meta_from_id(symbols_json, int(raw)) if is_digit else None
        if isinstance(meta, dict):
            text = (meta.get("meaning_kr") or meta.get("desc") or meta.get("text") or "").strip()
            typ = (meta.get("type") or "").lower()
        else:
            text = raw

        if not text:
            continue

        all_texts.append(text)
        # 간단 분류 규칙: 타입이 dry 이거나 텍스트에 '건조' 포함이면 drying
        if ("dry" in typ) or ("건조" in text):
            drying.append(text)
        else:
            washing.append(text)

    return washing, drying, all_texts

def _as_list(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, (tuple, set)):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        parts = [p.strip() for p in v.split(",")]
        return [p for p in parts if p]
    return [str(v).strip()]


@login_required
@require_POST
def delete_laundry_history(request, history_id: int):
    """
    기록 상세 화면에서 호출: 해당 LaundryHistory를 삭제 후 메인으로 이동.
    필요하면 소유자 검증 추가.
    """
    obj = get_object_or_404(LaundryHistory, pk=history_id)

    # (선택) 로그인 사용자 소유 검증
    # if request.user.is_authenticated and obj.user_id != request.user.id:
    #     messages.error(request, "삭제 권한이 없습니다.")
    #     return redirect("laundry_history_detail", history_id=history_id)

    obj.delete()
    messages.success(request, "기록을 삭제했습니다.")
    return redirect("main")


@login_required
def laundry_history_detail_view(request, history_id):
    record = get_object_or_404(LaundryHistory, pk=history_id, user=request.user)

    # 모델 필드가 CSV 문자열이므로 리스트로 변환
    materials_list = _as_list(getattr(record, "materials", ""))
    stains_list    = _as_list(getattr(record, "stains", ""))
    symbols_list   = _as_list(getattr(record, "symbols", ""))

    material_name = materials_list[0] if materials_list else ""
    stain_first   = stains_list[0] if stains_list else ""

    # 템플릿이 기대하는 키 채우기
    info = {
        "material": material_name,
        "stains": stain_first,
    }
    material_obj = _get_material_obj(material_name)           # {name, description, warning}
    stain_obj    = _get_stain_obj(stain_first)                # {Washing_Steps, not_to_do, Not_to__do}
    washing_descs, drying_descs, symbol_texts = _split_symbol_descriptions(symbols_list)

    # 요약(summary)은 없으면 템플릿이 폴백하므로 None 둬도 OK.
    # 만약 record.recommendation_result(HTML 스냅샷)에서 요약을 파싱하고 싶으면 별도 로직 추가 가능.
    summary = None

    context = {
        "record": record,
        "info": info,
        "material": material_obj,
        "stain": stain_obj,
        "washing_descriptions": washing_descs,
        "drying_descriptions": drying_descs,
        "symbols": symbol_texts,
        "summary": summary,
    }
    return render(request, "laundry_manager/laundry_history_detail.html", context)


@login_required
def record_settings_page(request):
    all_records = LaundryHistory.objects.filter(user=request.user)
    return render(request, "laundry_manager/record-settings.html", {"records": all_records})


# ---------------------------
# 업로드 → 세션 채우기 → History 저장
# ---------------------------

@login_required
@require_http_methods(["GET", "POST"])
def upload_and_save_history_view(request):
    """
    1) 사용자가 세탁 기호 이미지를 업로드
    2) (파이프라인) OCR/분류/룰엔진 → 세션에 결과 적재
    3) 세션 기반으로 LaundryHistory 레코드 생성
    """
    if request.method == "GET":
        form = WashingUploadForm()
        return render(request, "laundry_manager/upload.html", {"form": form})

    form = WashingUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "이미지를 업로드해 주세요.")
        return render(request, "laundry_manager/upload.html", {"form": form})

    image_file = form.cleaned_data["image"]

    try:
        with transaction.atomic():
            # 1) 업로드 파일 저장(참고용). 현재 모델 구조상 History와 직접 연결하진 않음.
            uploaded = UploadedImage.objects.create(image=image_file)

            # 2) 너희 파이프라인 실행해서 세션 채우기
            _run_pipeline_and_fill_session(request, uploaded)

            # 3) 세션 → History 저장
            payload = _build_history_payload_from_session(request)
            if not _has_any_payload(payload):
                return HttpResponse("분석 결과가 비어 있어 기록을 만들 수 없습니다.", status=400)

            record = LaundryHistory.objects.create(user=request.user, **payload)

    except Exception as e:
        messages.error(request, f"기록 저장 중 오류: {e}")
        return render(request, "laundry_manager/upload.html", {"form": form})

    messages.success(request, "세탁 기록이 저장되었습니다.")
    return redirect("laundry_history_detail", history_id=record.pk)

from django.template import TemplateDoesNotExist

@login_required
@require_http_methods(["POST"])
def save_current_result_as_history_view(request):
    """
    세션의 결과를 laundry-info 본문 형태의 HTML 스냅샷으로 렌더해
    LaundryHistory.recommendation_result 에 저장한다.
    """
    s = request.session
    payload = _build_history_payload_from_session(request)

    # 기본값 보정(메타 표시용)
    if not payload.get("materials"):
        payload["materials"] = (
            s.get("material")
            or (s.get("materials")[0] if s.get("materials") else "(소재 미선택)")
        )
    if not payload.get("stains"):
        payload["stains"] = ", ".join(s.get("stains") or []) or "(얼룩 미선택)"

    # 1) 레코드 먼저 생성
    record = LaundryHistory.objects.create(user=request.user, **payload)

    # 2) 스냅샷 컨텍스트 구성
    stain_obj = s.get("stain_obj") or {}
    if not isinstance(stain_obj, dict):
        stain_obj = {}
    # 템플릿 안전 사용을 위해 미리 병합
    stain_todo = stain_obj.get("not_to_do") or stain_obj.get("Not_to__do")

    ctx = {
        "summary":  s.get("summary") or {},
        "material": s.get("material_obj") or {},                 # {name, description, warning}
        "stain":    stain_obj,                                   # {Washing_Steps, ...}
        "stain_todo": stain_todo,                                # ✅ 템플릿에서 바로 사용
        "washing_descriptions": s.get("washing_descriptions") or [],
        "drying_descriptions":  s.get("drying_descriptions") or [],
        "symbols":  s.get("symbol_descriptions") or s.get("symbols") or [],
        "info": {
            "material": s.get("material") or (s.get("materials")[0] if s.get("materials") else ""),
            "stains": ", ".join(s.get("stains") or []),
        },
    }

    # 3) HTML 스냅샷 렌더
    try:
        snapshot_html = render_to_string(
            "laundry_manager/partials/_laundry_info_snapshot.html",  # ← 템플릿 경로 일치 확인
            ctx,
            request=request,  # static/url 태그 처리
        ).strip()
    except TemplateDoesNotExist:
        snapshot_html = ""

    # 4) 스냅샷이 비면 폴백(기존 텍스트) + 디버그 마커
    if not snapshot_html:
        fb = payload.get("recommendation_result") or ""
        snapshot_html = f"<!-- SNAPSHOT_EMPTY_FALLBACK -->{fb}"

    # 5) 저장
    record.recommendation_result = snapshot_html
    record.save(update_fields=["recommendation_result"])

    messages.success(request, f"기록 저장 완료 (len={len(snapshot_html)})")
    return redirect("laundry_history_detail", history_id=record.pk)

# ---------------------------
# 내부 유틸/훅
# ---------------------------

def _run_pipeline_and_fill_session(request, uploaded: UploadedImage):
    session = request.session

    # 기존/파이프라인 값들을 전부 리스트로 정규화
    materials = _as_list(session.get("materials", session.get("material", "")))
    stains    = _as_list(session.get("stains", session.get("stain", [])))
    symbols   = _as_list(session.get("symbols", session.get("rule_keywords", session.get("recognized_texts", []))))

    # 세션 표준화(항상 리스트 보관, 단일 키도 유지)
    session["materials"] = materials
    session["material"]  = materials[0] if materials else ""
    session["stains"]    = stains
    session["symbols"]   = symbols

    # 요약 텍스트 기본값 보정
    session["recommendation_result"] = str(
        session.get("recommendation_result") or session.get("instructions") or ""
    ).strip()

    session.modified = True

def _coerce_to_commasep(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, set)):
        return ", ".join([str(v).strip() for v in value if str(v).strip()])
    return str(value).strip()


def _build_history_payload_from_session(request):
    s = request.session
    materials = _as_list(s.get("materials") or s.get("material") or "")
    stains    = _as_list(s.get("stains") or "")
    symbols   = _as_list(s.get("symbols") or s.get("rule_keywords") or s.get("recognized_texts") or "")
    recommendation = (s.get("recommendation_result") or s.get("instructions") or "").strip()

    return {
        "materials": ", ".join(materials),
        "stains": ", ".join(stains),
        "symbols": ", ".join(symbols),
        "recommendation_result": recommendation,
    }



def _has_any_payload(payload: dict) -> bool:
    return any(bool(v) for v in payload.values())

# 세션 → LaundryHistory 저장 유틸 (뷰/다른 모듈에서 재사용)
def save_history_from_session(request, image_file=None):
    """
    세션에 적재된 결과를 현재 로그인 사용자 기록으로 저장하고,
    생성된 LaundryHistory 인스턴스를 반환한다.

    - 현재 스키마에는 image 필드가 없으므로 image_file은 무시된다.
    - 필요한 세션 키가 없다면 빈 문자열/CSV로 보정한다.
    """
    if not request.user.is_authenticated:
        raise ValueError("로그인한 사용자만 기록을 저장할 수 있습니다.")

    payload = _build_history_payload_from_session(request)
    if not _has_any_payload(payload):
        raise ValueError("세션에 저장된 결과가 없어 기록을 만들 수 없습니다.")

    record = LaundryHistory.objects.create(user=request.user, **payload)
    return record
