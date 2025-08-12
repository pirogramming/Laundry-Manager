# views/pages.py (또는 main_page 뷰)
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
from django.shortcuts import render
from ..models import LaundryHistory

def _social_name_and_image(user):
    # 1) 로그인 안 되어 있으면 안전하게 빠르게 종료
    if not getattr(user, "is_authenticated", False):
        # 원하는 기본 표시 이름/이미지
        return ("손님", None)

    # 2) 로그인된 경우만 소셜 계정 조회 (FK는 객체로 비교!)
    social = SocialAccount.objects.filter(user=user).first()
    if not social:
        # 일반 회원(소셜 연결 없음)
        name = user.get_full_name() or user.first_name or user.username or "사용자"
        return (name, None)

    data = social.extra_data or {}
    provider = social.provider

    # Google
    if provider == "google":
        name = data.get("name") or user.get_full_name() or user.username
        image = data.get("picture")

    # Kakao
    elif provider == "kakao":
        kakao_account = data.get("kakao_account", {}) or {}
        profile = kakao_account.get("profile", {}) or {}
        properties = data.get("properties", {}) or {}
        name = (
            profile.get("nickname")
            or properties.get("nickname")
            or user.get_full_name()
            or user.username
        )
        image = (
            profile.get("profile_image_url")
            or properties.get("profile_image")
        )

    else:
        name = user.get_full_name() or user.username
        image = None

    return name, image


def main_page(request):
    profile_image = None
    display_name = request.user.username if request.user.is_authenticated else '' # 기본값

    if request.user.is_authenticated:
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            extra_data = social_account.extra_data
            profile_image = extra_data.get('picture')   # 구글 프로필 사진 URL
            display_name = extra_data.get('name', request.user.username)
        except SocialAccount.DoesNotExist:
            pass  # 일반 로그인 유저일 경우

    records = []  # 필요 시 DB 조회
    # 로그인한 사용자일 경우에만 DB에서 최근 기록 3개를 조회합니다.
    if request.user.is_authenticated:
        records = LaundryHistory.objects.filter(user=request.user)[:3]
    return render(request, 'laundry_manager/main.html', {
        'records': records,
        'profile_image': profile_image,
        'display_name': display_name
    })



def laundry_upload_page(request):
    return render(request, "laundry_manager/laundry-upload.html")

def stain_upload_page(request):
    return render(request, "laundry_manager/stain-upload.html")

def result_page(request):
    return render(request, "laundry_manager/result.html")

def laundry_info_page(request):
    return render(request, "laundry_manager/laundry-info.html")

def stain_info_page(request):
    return render(request, "laundry_manager/stain-info.html")

def stain_guide_page(request):
    return render(request, "laundry_manager/stain_guide.html")

def stain_detail_page(request):
    return render(request, "laundry_manager/stain_detail.html")


def login_page(request):
    return render(request, "laundry_manager/login.html")
def dictionary_page(request):
    return render(request, "laundry_manager/dictionary.html")
def main2_page(request):
    return render(request, "laundry_manager/main2.html")
def profile_page(request):
    return render(request, "laundry_manager/profile.html")
def settings_page(request):
    return render(request, "laundry_manager/settings.html")

def settings_developer_page(request):
    return render(request, "laundry_manager/settings-developer.html")
def settings_faq_page(request):
    return render(request, "laundry_manager/settings-faq.html")
def settings_opensource_page(request):
    return render(request, "laundry_manager/settings-opensource.html")
def settings_terms_page(request):
    return render(request, "laundry_manager/settings-terms.html")
def settings_privacy_page(request):
    return render(request, "laundry_manager/settings-privacy.html")

def account_settings_page(request):
    return render(request, "laundry_manager/account-settings.html")
def contact_settings_page(request):
    return render(request, "laundry_manager/contact-settings.html")
def record_settings_page(request):
    return render(request, "laundry_manager/record-settings.html")
