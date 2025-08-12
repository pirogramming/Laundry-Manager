from django.shortcuts import render

def main_page(request):
    return render(request, "laundry_manager/main.html")

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
