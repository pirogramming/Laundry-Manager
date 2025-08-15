# laundry_manager/views/contact.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..forms import InquiryForm 
@require_POST 
def contact_submit_view(request):
    """
    문의하기 폼 제출을 비동기(AJAX/Fetch)로 처리하는 뷰입니다.
    """
    form = InquiryForm(request.POST)

    if form.is_valid():
        form.save()
        
        return JsonResponse({'status': 'success', 'message': '문의가 성공적으로 제출되었습니다.'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)