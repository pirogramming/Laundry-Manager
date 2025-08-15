# laundry_manager/urls.py
from django.urls import path
from .views import pages, ocr, stains, info_flow, maps, history, classify
import laundry_manager.views.dictionary as dictionary_views  # 이전 이슈 피하려고 모듈 임포트
## 테스트를 위한 import들 ##
from django.views.generic import TemplateView
from .views import laundry_res  # 이미 guide_from_result 추가해놨던 파일


urlpatterns = [
    path("", pages.main_page, name="main"),
    path("laundry-upload/", ocr.upload_view, name="laundry-upload"),
    # (페이지 전용 라우트는 계속 유지하고 싶다면 별도 경로 사용)
    path("laundry-upload-page/", pages.laundry_upload_page, name="laundry-upload-page"),
    path("stain-upload/", stains.stain_guide_view, name="stain-upload"),
    path("result/", ocr.result_view, name="result"),
    # path("history/<int:pk>/update/", info_flow.update_history_field, name="lh_update"),
    path("result/update-selection/", info_flow.update_selection_view, name="update_selection"),

    path("laundry-info/", pages.laundry_info_page, name="laundry-info"),
    path("upload/", ocr.upload_and_classify, name="upload"),
    path("uploadimage/", ocr.upload_view, name="upload_image"),
    path("stain-guide/", stains.stain_guide_view, name="stain-guide"),
    path("stain_detail/<str:slug>/", stains.stain_detail_view, name="stain_detail"),
    path("laundry/", info_flow.laundry_result_view, name="laundry_view"),
    path("laundry-info-v1/", info_flow.laundry_info_view1, name="laundry-info-v1"),
    path("first-info/", info_flow.first_info_view, name="first_info"),
    path("final-info/", info_flow.final_info_view, name="final_info"),
    path("dictionary/", dictionary_views.dictionary_view, name="dictionary"),
    path("dictionary/<path:item_title>/", dictionary_views.dictionary_detail, name="dictionary_detail"),
    path("map-test/", maps.map_test_view, name="map-test"),
    # path("api/shops/mapo/", maps.shops_mapo, name="shops-mapo"),
    # path('laundry-upload/', views.upload_and_classify, name='laundry-upload'),
    path("stain-info/", pages.stain_info_page, name="stain-info"),
    # path('stain-upload/', views.stain_upload_page, name='stain-upload'),
    path("laundry-info/", pages.laundry_info_page, name="laundry-info"),
    path("stain-info/", pages.stain_info_page, name="stain-info"),
    path("login/", pages.login_page, name="login"),
    path("login-test/", pages.login_test_page, name="login-test"),
    path("dictionary/", pages.dictionary_page, name="dictionary"),
    path("dictionary-detail/", pages.dictionary_detail_page, name="dictionary-detail"),
    
    path("main2/", pages.main2_page, name="main2"),
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
    path("record-settings/", history.record_settings_page, name="record-settings"),
    path(
        "history/<int:history_id>/",
        history.laundry_history_detail_view,
        name="laundry_history_detail",
    ),
    path("classify/", classify.classify_symbol_view, name="classify"),


    # ... 기존 라우트들 ...
    path("guide/from-result/", laundry_res.guide_from_result, name="guide_from_result"),
]
