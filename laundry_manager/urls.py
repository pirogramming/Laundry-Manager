# laundry_manager/urls.py
from django.urls import path
from .views import pages, ocr, stains, info_flow, maps, history, classify, contact, fortune, result, dictionary
import laundry_manager.views.dictionary as dictionary_views
## 테스트를 위한 import들 ##
from django.views.generic import TemplateView
from .views import laundry_res  # 이미 guide_from_result 추가해놨던 파일
from .views.result_router import result_router_view  # ⬅️ 새로 만들 라우터


urlpatterns = [
    path("", pages.login_page, name="login"),
    path("main/", pages.main_page, name="main"),
    path("guest-enter/", pages.guest_enter, name="guest_enter"),
    path("guest-exit/", pages.guest_exit, name="guest_exit"),
    path("laundry-upload/", result.laundry_upload_page, name="laundry-upload"),
    path("stain-upload/", stains.stain_guide_view, name="stain-upload"),
    path("result/", result_router_view, name="result"),         # ✅ 고정 진입점
    path("result-ocr/", ocr.result_view, name="result-ocr"),    # 직접 접근(디버그/호출용)
    path("result-modal/", result.result_view, name="result-modal"),  # 기존 뷰도 보존
    path("result/update-selection/", info_flow.update_selection_view, name="update_selection"),


    # path("laundry-info/", pages.laundry_info_page, name="laundry-info"),
    path("upload/", ocr.upload_and_classify, name="upload"),
    path("uploadimage/", ocr.upload_view, name="upload_image"),
    path("stain-guide/", stains.stain_guide_view, name="stain-guide"),
    path("stain_detail/<str:slug>/", stains.stain_detail_view, name="stain_detail"),
    path("laundry/", info_flow.laundry_result_view, name="laundry_view"),
    path("laundry-info-v1/", info_flow.laundry_info_view1, name="laundry-info-v1"),
    path("first-info/", info_flow.first_info_view, name="first_info"),
    path("final-info/", info_flow.final_info_view, name="final_info"),
    path("dictionary/", dictionary_views.dictionary_view, name="dictionary"),
    path("dictionary/<path:item_title>/", dictionary.dictionary_detail, name="dictionary_detail"),
    path("stain-info/", pages.stain_info_page, name="stain-info"),
    path("login-test/", pages.login_test_page, name="login-test"),
    path("dictionary/", pages.dictionary_page, name="dictionary"),
    path("dictionary-detail/", pages.dictionary_detail_page, name="dictionary-detail"),
    
    path("profile/", pages.profile_page, name="profile"),
    
    path("map/", pages.map_page, name="map"),
    
    path("settings/", pages.settings_page, name="settings"),
    path(
        "settings-developer/", pages.settings_developer_page, name="settings-developer"
    ),
    path("settings-faq/", pages.settings_faq_page, name="settings-faq"),
    path(
        "settings-opensource/",
        pages.settings_opensource_page,
        name="settings-opensource",
    ),
    path("settings-terms/", pages.settings_terms_page, name="settings-terms"),
    path("settings-privacy/", pages.settings_privacy_page, name="settings-privacy"),
    path("account-settings/", pages.account_settings_page, name="account-settings"),
    path("contact-settings/", pages.contact_settings_page, name="contact-settings"),
    # 기록(History)
    path("record-settings/", history.record_settings_page, name="record-settings"),
    path("history/<int:history_id>/", history.laundry_history_detail_view, name="laundry_history_detail"),
    path("history/<int:history_id>/delete/", history.delete_laundry_history, name="laundry_history_delete"),
    path("history/upload/", history.upload_and_save_history_view, name="upload_history"),
    path("history/save-current/", history.save_current_result_as_history_view, name="save_current_history"),
    path("laundry-info/", laundry_res.guide_from_result, name="guide_from_result"),
    
    #문의하기 처리
    path('contact/submit/', contact.contact_submit_view, name='contact_submit'),

    # 오늘의 운세
    path("api/fortune/today/", fortune.fortune_today_view, name="fortune_today"),
    path("api/fortune/dismiss/", fortune.fortune_dismiss_view, name="fortune_dismiss"),

]
