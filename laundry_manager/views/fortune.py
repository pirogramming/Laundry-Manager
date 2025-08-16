# views/fortune.py
import hashlib, datetime, random
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

FORTUNES = [
    "오늘은 새로운 시도를 해보면 좋아요.",
    "작은 정성이 큰 결과로 돌아옵니다.",
    "정리정돈부터 시작해 보세요. 흐름이 트여요.",
    "친구의 도움 요청을 들어주면 행운이 와요.",
    "평소 미뤄둔 일을 끝내기 좋은 날!",
    "가벼운 산책이 좋은 아이디어를 불러와요.",
]

def _today_str():
    return datetime.date.today().isoformat()

def _today_cookie_key():
    return f"fortune_shown_{_today_str()}"

def _seed_from_request(request):
    today = _today_str()
    if getattr(request, "user", None) and request.user.is_authenticated:
        base = f"{today}:{request.user.id}"
    else:
        sess = getattr(request, "session", None)
        key = getattr(sess, "session_key", "") or request.META.get("REMOTE_ADDR", "")
        base = f"{today}:{key}"
    h = hashlib.sha256(base.encode()).hexdigest()
    return int(h[:8], 16)

def fortune_today_view(request):
    """
    오늘의 운세 조회.
    - 이미 닫았으면 show=False 로 응답
    - 아니면 fortune 과 함께 show=True
    """
    today = _today_str()
    cookie_key = _today_cookie_key()

    # 이미 닫았는지 확인 (쿠키 또는 세션)
    if request.COOKIES.get(cookie_key) == "1" or request.session.get(cookie_key):
        return JsonResponse({"date": today, "show": False})

    seed = _seed_from_request(request)
    rnd = random.Random(seed)
    fortune = rnd.choice(FORTUNES)
    return JsonResponse({"date": today, "show": True, "fortune": fortune})

@require_http_methods(["POST"])
@csrf_exempt  # CSRF 토큰을 붙여 호출할 거면 이 줄 제거
def fortune_dismiss_view(request):
    """
    X 버튼 눌렀을 때 호출.
    - 오늘 날짜 키로 쿠키/세션에 '봤다' 표시를 저장.
    """
    cookie_key = _today_cookie_key()

    # 세션에도 기록(선택)
    request.session[cookie_key] = True

    resp = JsonResponse({"ok": True})
    # 1일 동안만 유지(자정 지나면 새 운세 띄우게)
    resp.set_cookie(cookie_key, "1", max_age=60*60*24, samesite="Lax")
    return resp
