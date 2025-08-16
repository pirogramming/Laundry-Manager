# laundry_manager/views/contact.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings      # 👈 settings.py의 설정을 가져오기 위해 import
from django.core.mail import send_mail  # 👈 이메일 발송 함수 import
from ..forms import InquiryForm

@require_POST
def contact_submit_view(request):
    """
    문의하기 폼 제출을 DB에 저장하고, 관리자에게 이메일로 알림을 보냅니다.
    """
    form = InquiryForm(request.POST)

    if form.is_valid():
        # 1. 폼 데이터가 유효하면, 먼저 DB에 저장합니다.
        inquiry = form.save()
        
        # --- 👇 [신규] 이메일 발송 로직 추가 ---
        try:
            # 2. 이메일 제목과 내용을 구성합니다.
            subject = f"[세탁 매니저 문의] {inquiry.subject}"
            
            message = f"""
            새로운 문의가 접수되었습니다.

            - 작성자: {inquiry.name}
            - 회신 이메일: {inquiry.email}
            - 문의 유형: {inquiry.inquiry_type}
            
            - 제목:
            {inquiry.subject}
            
            - 내용:
            {inquiry.message}
            """
            
            # 3. 이메일을 발송합니다.
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,  # 보내는 사람 (settings.py에 설정된 값)
                recipient_list=['setakmanager@gmail.com'], # 👈 [중요] 문의를 받을 관리자 이메일 주소를 입력하세요.
                fail_silently=False, # 발송 실패 시 에러를 발생시킴
            )
        except Exception as e:
            # 이메일 발송에 실패하더라도, DB 저장은 성공했으므로
            # 서버 로그에만 에러를 기록하고 사용자에게는 영향을 주지 않습니다.
            print(f"Email sending failed: {e}")
        # --- 이메일 발송 로직 끝 ---
        
        return JsonResponse({'status': 'success', 'message': '문의가 성공적으로 제출되었습니다.'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)