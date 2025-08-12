# views/pages.py (또는 main_page 뷰)
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
from django.shortcuts import render

def _social_name_and_image(user):
    """
    allauth SocialAccount.extra_data에서
    Google/Kakao 공통으로 이름, 프로필 이미지 URL을 추출
    """
    social = SocialAccount.objects.filter(user=user).first()
    if not social:
        return (user.get_full_name() or user.username, None)

    data = social.extra_data
    provider = social.provider

    # Google
    if provider == "google":
        name = data.get("name") or user.get_full_name() or user.username
        image = data.get("picture")

    # Kakao
    elif provider == "kakao":
        # 신규 스키마
        kakao_account = data.get("kakao_account", {}) or {}
        profile = kakao_account.get("profile", {}) or {}
        # 구 스키마 호환 (properties)
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
    display_name, profile_image = _social_name_and_image(request.user)

    # 기존 records 로직 유지
    records = []  # 실제 쿼리로 대체

    return render(
        request,
        "laundry_manager/main.html",
        {
            "records": records,
            "display_name": display_name,
            "profile_image": profile_image,
        },
    )



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
