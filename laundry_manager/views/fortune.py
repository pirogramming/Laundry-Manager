# views/fortune.py
import hashlib, datetime, random
from django.http import JsonResponse

FORTUNES = [
    "오늘은 새로운 시도를 해보면 좋아요.",
    "작은 정성이 큰 결과로 돌아옵니다.",
    "정리정돈부터 시작해 보세요. 흐름이 트여요.",
    "친구의 도움 요청을 들어주면 행운이 와요.",
    "평소 미뤄둔 일을 끝내기 좋은 날!",
    "가벼운 산책이 좋은 아이디어를 불러와요.",
]

def _seed_from_request(request):
    today = datetime.date.today().isoformat()
    if getattr(request, "user", None) and request.user.is_authenticated:
        base = f"{today}:{request.user.id}"
    else:
        sess = getattr(request, "session", None)
        key = getattr(sess, "session_key", "") or request.META.get("REMOTE_ADDR", "")
        base = f"{today}:{key}"
    h = hashlib.sha256(base.encode()).hexdigest()
    # 안정적인(seed 고정) 선택
    return int(h[:8], 16)

def fortune_today_view(request):
    seed = _seed_from_request(request)
    rnd = random.Random(seed)
    fortune = rnd.choice(FORTUNES)
    return JsonResponse({"date": datetime.date.today().isoformat(), "fortune": fortune})
