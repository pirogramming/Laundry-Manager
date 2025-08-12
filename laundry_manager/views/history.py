# laundry_manager/views/history.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse

# 같은 앱(models.py)에 있다면 점 하나(.) 사용
from models import LaundryHistory, Recommendation  # 필요하면 Clothing, Stain 등도 추가

User = get_user_model()

@login_required
def laundry_history_detail_view(request, history_id):
    """
    특정 세탁 기록(pk=history_id)의 상세 정보를 보여주는 뷰
    """
    # get_object_or_404: 객체를 찾되, 없으면 404 에러를 냄
    # user=request.user: 다른 사람이 내 기록을 보지 못하도록 현재 로그인한 유저의 기록만 조회
    record = get_object_or_404(LaundryHistory, pk=history_id, user=request.user)

    context = {
        'record': record
    }
    return render(request, 'laundry_manager/laundry_history_detail.html', context)


# 사용자 기록 리스트 뷰 
'''사용자 기록들 records리스트로 반환'''


############ 1번째 방법 -> 함수가 조금 문제가 생기면 기록 보는거까지 안나올 수 있음 살짝 틀어지면 결과 인니옴######

#@login_required
# def record_list_view(request):
#     '''User = get_user_model()
#     temp_user = User.objects.get(username='sje')
#     records = Recommendation.objects.filter(clothing__user=temp_user)
#     #records = Recommendation.objects.filter(clothing__user=request.user).order_by('-created_at')[:2]
#     return render(request, 'main.html', {
#         'records': records
#     })'''
#     try:
#         temp_user = User.objects.get(name="sje")
#     except User.DoesNotExist:
#         temp_user = None

#     # temp_user가 있으면 해당 유저의 기록만 가져오고, 없으면 빈 쿼리셋 반환
#     if temp_user:
#         records = Recommendation.objects.filter(clothing__user=temp_user).order_by('-created_at')[:3]
#     else:
#         records = []

#     return render(request, 'laundry_manager/main.html', {'records': records})

#사용자 기록 디테일 뷰
# #@login_required
# def record_detail_view(request, pk):
#     '''record = get_object_or_404(Recommendation, pk=pk, clothing__user=request.user)
#     return render(request, 'laundry_manager/laundry-info.html', {
#         'record': record
#     })'''
#     try:
#         temp_user = User.objects.get(name="sje")  # 임시 유저
#     except User.DoesNotExist:
#         temp_user = None

#     if not temp_user:
#         return HttpResponse("User not found", status=404)

#     record = get_object_or_404(Recommendation, pk=pk, clothing__user=temp_user)

#     # record 안에 연결된 모든 foreign key 객체들 꺼냄
#     clothing = record.clothing
#     stain = record.stain
#     laundry = record.laundry
#     course = record.course
#     mode = record.mode

#     # symbols = laundry.description + image_url 정도로 구성
#     symbols = []
#     if laundry.description:
#         symbols.append(laundry.description)
#     if laundry.image_url:
#         symbols.append(f"관련 이미지 URL: {laundry.image_url}")

#     # info = 정리된 내용들
#     info = {
#         "stains": f"{stain.category} 계열 얼룩",
#         "material": f"{clothing.fabric} 소재로 분류"
#     }

#     return render(request, 'laundry_manager/laundry-info.html', {
#         "material_name": clothing.name or "이름 없는 의류",
#         "stains": [stain.name],
#         "material": clothing,
#         "stain": stain,
#         "symbols": symbols,
#         "info": info,
#         "record": record,
#     })
# #임시 프로필창 뷰
# def profile_view(request):
#     #return render(request, 'laundry_manager/profile.html')
#     try:
#         temp_user = User.objects.get(name="sje")  # ← 로그인 기능 전이라서
#     except User.DoesNotExist:
#         temp_user = None

#     if temp_user:
#         records = Recommendation.objects.filter(clothing__user=temp_user).order_by('-created_at')[:10]
#     else:
#         records = []

#     return render(request, 'laundry_manager/profile.html', {'records': records})

# ############ 1번째 방법 -> 함수가 조금 문제가 생기면 기록 보는거까지 안나올 수 있음 살짝 틀어지면 결과 인니옴######