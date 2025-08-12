# laundry_manager/urls.py
from django.urls import path
from .views import pages, ocr, stains, info_flow, maps, history
import laundry_manager.views.dictionary as dictionary_views  # 이전 이슈 피하려고 모듈 임포트

urlpatterns = [
    path('', pages.main_page, name='main'),

    # ✅ 예전 이름 복구 (템플릿 호환)
    path('laundry-upload/', ocr.upload_view, name='laundry-upload'),

    # (페이지 전용 라우트는 계속 유지하고 싶다면 별도 경로 사용)
    path('laundry-upload-page/', pages.laundry_upload_page, name='laundry-upload-page'),
    path('stain-upload/', stains.stain_guide_view, name='stain-upload'),
    path('result/', ocr.result_view, name='result'),
    path('laundry-info/', pages.laundry_info_page, name='laundry-info'),

    path("upload/", ocr.upload_and_classify, name="upload"),
    path("uploadimage/", ocr.upload_view, name="upload_image"),
    path("stain-guide/", stains.stain_guide_view, name="stain-guide"),
    path("stain_detail/<str:slug>/", stains.stain_detail_view, name="stain_detail"),
    path("laundry/", info_flow.laundry_result_view, name="laundry_view"),
    path('laundry-info-v1/', info_flow.laundry_info_view1, name='laundry-info-v1'),
    path('first-info/', info_flow.first_info_view, name='first_info'),
    path('final-info/', info_flow.final_info_view, name='final_info'),
    path('dictionary/', dictionary_views.dictionary_view, name='dictionary'),  # 함수명 바꿨다면 _view
    path('map-test/', maps.map_test_view, name='map-test'),
    path("api/shops/mapo/", maps.shops_mapo, name="shops-mapo"),
    # path('laundry-upload/', views.upload_and_classify, name='laundry-upload'),
    path("stain-info/", pages.stain_info_page, name="stain-info"),
    # path('stain-upload/', views.stain_upload_page, name='stain-upload'),
    path('laundry-info/', pages.laundry_info_page, name='laundry-info'),  
    path('stain-info/', pages.stain_info_page, name='stain-info'),
    path('login/', pages.login_page, name='login'),  
    path('dictionary/', pages.dictionary_page, name='dictionary'), 
    path('main2/', pages.main2_page, name='main2'), 
    path('profile/', pages.profile_page, name='profile'), 
    path('settings/', pages.settings_page, name='settings'), 
    path('settings-developer/', pages.settings_developer_page, name='settings-developer'), 
    path('settings-faq/', pages.settings_faq_page, name='settings-faq'), 
    path('settings-opensource/', pages.settings_opensource_page, name='settings-opensource'), 
    path('settings-terms/', pages.settings_terms_page, name='settings-terms'), 
    path('settings-privacy/', pages.settings_privacy_page, name='settings-privacy'), 
        
    path('account-settings/', pages.account_settings_page, name='acount-settings'), 
    
    path('contact-settings/', pages.contact_settings_page, name='contact-settings'), 
    
    path('record-settings/', history.record_settings_page, name='record-settings'), 
    path('history/<int:history_id>/', history.laundry_history_detail_view, name='laundry_history_detail'),
    
]
