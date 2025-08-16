# laundry_manager/views/history.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from ..models import LaundryHistory, UploadedImage
from ..forms import WashingUploadForm

User = get_user_model()


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
    return render(request, 'laundry_manager/laundry_history_detail.html', {"record": record})

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


@login_required
@require_http_methods(["POST"])
def save_current_result_as_history_view(request):
    """
    업로드 없이, 이미 세션에 들어있는 결과를 바로 기록으로 저장하고 싶을 때 사용
    """
    payload = _build_history_payload_from_session(request)
    if not _has_any_payload(payload):
        return HttpResponse("세션에 저장된 결과가 없습니다.", status=400)

    record = LaundryHistory.objects.create(user=request.user, **payload)
    messages.success(request, "현재 결과를 기록으로 저장했습니다.")
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
