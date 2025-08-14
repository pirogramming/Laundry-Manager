# views/pages.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount

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

    # 3) 연결된 소셜 계정 1개만 사용 (복수일 경우 첫 번째)
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


# --- (2) 모든 뷰에서 공통으로 쓸 컨텍스트 빌더 ---
def base_context(request, extra=None):
    """
    모든 템플릿에서 공통으로 접근 가능한 컨텍스트를 구성.
    - display_name, profile_image
    - (선택) 최근 세탁 기록 3개
    """
    name, image = _social_name_and_image(getattr(request, "user", None))

    ctx = {
        "display_name": name,
        "profile_image": image,
    }

    # 최근 기록은 메인에서만 필요하면 main_page에서 추가해도 OK
    if extra:
        ctx.update(extra)
    return ctx


# --- (3) 페이지 뷰들 ---
def main_page(request):
    recent_records = []
    if request.user.is_authenticated and LaundryHistory:
        recent_records = LaundryHistory.objects.filter(user=request.user).order_by("-id")[:3]

    ctx = base_context(request, extra={
        "records": recent_records,
    })
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


def dictionary_page(request):
    return render(request, "laundry_manager/dictionary.html", base_context(request))
def dictionary_detail_page(request):
    return render(request, "laundry_manager/dictionary-detail.html", base_context(request))


def main2_page(request):
    return render(request, "laundry_manager/main2.html", base_context(request))


def profile_page(request):
    return render(request, "laundry_manager/profile.html", base_context(request))


def settings_page(request):
    # settings 템플릿에서도 그대로 display_name/profile_image 사용 가능
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


def record_settings_page(request):
    return render(request, "laundry_manager/record-settings.html", base_context(request))
