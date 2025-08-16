# views/pages.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from . import maps

# allauth가 없는 환경에서도 터지지 않도록 안전 임포트
try:
    from allauth.socialaccount.models import SocialAccount
except Exception:
    SocialAccount = None

# LaundryHistory가 없을 수도 있어 안전하게 임포트
try:
    from ..models import LaundryHistory
except Exception:
    LaundryHistory = None


# --- (1) 소셜/일반 공통 이름·이미지 유틸 ---
def _social_name_and_image(user):
    """
    로그인 종류(일반/구글/카카오)에 상관없이
    표시 이름(display_name)과 프로필 이미지(profile_image) URL을 반환.
    """
    # 1) 로그인 안 되었을 때
    if not getattr(user, "is_authenticated", False):
        return ("손님", None)

    # 2) 기본 폴백: User 객체
    base_name = (getattr(user, "get_full_name", lambda: "")()
                 or getattr(user, "first_name", "") or user.username or "사용자")
    profile_image = None

    # 3) allauth 미설치/미사용 시 바로 반환
    if SocialAccount is None:
        return (base_name, profile_image)

    # 4) 연결된 소셜 계정 1개만 사용 (복수일 경우 첫 번째)
    social = SocialAccount.objects.filter(user=user).first()
    if not social:
        return (base_name, profile_image)

    data = social.extra_data or {}
    provider = social.provider

    if provider == "google":
        name = data.get("name") or base_name
        image = data.get("picture") or None
        return (name, image)

    elif provider == "kakao":
        kakao_account = data.get("kakao_account") or {}
        profile = kakao_account.get("profile") or {}
        properties = data.get("properties") or {}

        name = (
            profile.get("nickname")
            or properties.get("nickname")
            or base_name
        )
        image = (
            profile.get("profile_image_url")
            or profile.get("thumbnail_image_url")
            or properties.get("profile_image")
            or None
        )
        return (name, image)

    # 그 외 프로바이더는 기본값
    return (base_name, profile_image)


# --- (2) 공통 컨텍스트 빌더 ---
def base_context(request, extra=None):
    """
    모든 템플릿에서 공통으로 접근 가능한 컨텍스트.
    - display_name, profile_image
    """
    name, image = _social_name_and_image(getattr(request, "user", None))

    ctx = {
        "display_name": name,
        "profile_image": image,
    }
    if extra:
        ctx.update(extra)
    return ctx


# --- (3) 헬퍼: 최근 기록 / 전체 기록 ---
def _recent_records(user, limit=3):
    if not (getattr(user, "is_authenticated", False) and LaundryHistory):
        return []
    return list(LaundryHistory.objects.filter(user=user).order_by("-created_at")[:limit])

def _all_records(user):
    if not (getattr(user, "is_authenticated", False) and LaundryHistory):
        return []
    return list(LaundryHistory.objects.filter(user=user).order_by("-created_at"))


# --- (4) 페이지 뷰들 ---
def main_page(request):
    # 메인 화면: 최근 기록 3건 노출 (템플릿: {% for record in records %} ...)
    recent_records = _recent_records(request.user, limit=3)
    ctx = base_context(request, extra={"records": recent_records})
    return render(request, "laundry_manager/main.html", ctx)


def laundry_upload_page(request):
    return render(request, "laundry_manager/laundry-upload.html", base_context(request))


def stain_upload_page(request):
    return render(request, "laundry_manager/stain-upload.html", base_context(request))


def result_page(request):
    return render(request, "laundry_manager/result.html", base_context(request))


def laundry_info_page(request):
    return render(request, "laundry_manager/laundry-info.html", base_context(request))


def stain_info_page(request):
    return render(request, "laundry_manager/stain-info.html", base_context(request))


def stain_guide_page(request):
    return render(request, "laundry_manager/stain_guide.html", base_context(request))


def stain_detail_page(request):
    return render(request, "laundry_manager/stain_detail.html", base_context(request))


def login_page(request):
    return render(request, "laundry_manager/login.html", base_context(request))


def login_test_page(request):
    return render(request, "laundry_manager/login-test.html", base_context(request))


def dictionary_page(request):
    return render(request, "laundry_manager/dictionary.html", base_context(request))


def dictionary_detail_page(request):
    return render(request, "laundry_manager/dictionary-detail.html", base_context(request))


def main2_page(request):
    # 보조 메인: 최근 기록 5건
    recent_records = _recent_records(request.user, limit=5)
    return render(request, "laundry_manager/main2.html", base_context(request, extra={"records": recent_records}))


def profile_page(request):
    # 프로필 화면: 최근 기록 10건 정도 노출(원하면 조절)
    recent_records = _recent_records(request.user, limit=10)
    return render(request, "laundry_manager/profile.html", base_context(request, extra={"records": recent_records}))





def map_page(request):
    map_data = maps.get_map_data()
    context = base_context(request, extra=map_data)
    return render(request, "laundry_manager/map.html", context)

def settings_page(request):
    return render(request, "laundry_manager/settings.html", base_context(request))


def settings_developer_page(request):
    return render(request, "laundry_manager/settings-developer.html", base_context(request))


def settings_faq_page(request):
    return render(request, "laundry_manager/settings-faq.html", base_context(request))


def settings_opensource_page(request):
    return render(request, "laundry_manager/settings-opensource.html", base_context(request))


def settings_terms_page(request):
    return render(request, "laundry_manager/settings-terms.html", base_context(request))


def settings_privacy_page(request):
    return render(request, "laundry_manager/settings-privacy.html", base_context(request))


def account_settings_page(request):
    return render(request, "laundry_manager/account-settings.html", base_context(request))


def contact_settings_page(request):
    return render(request, "laundry_manager/contact-settings.html", base_context(request))


@login_required
def record_settings_page(request):
    # 기록 설정: 로그인 사용자 전체 기록 전달
    all_records = _all_records(request.user)
    return render(request, "laundry_manager/record-settings.html", base_context(request, extra={"records": all_records}))
