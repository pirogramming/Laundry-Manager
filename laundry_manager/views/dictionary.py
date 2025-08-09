# laundry_manager/views/dictionary.py
import os, json, logging
from datetime import date
import requests
from django.conf import settings
from django.shortcuts import render
from decouple import config

logger = logging.getLogger(__name__)

NAVER_CLIENT_ID = config("NAVER_CLIENT_ID", default="")
NAVER_CLIENT_SECRET = config("NAVER_CLIENT_SECRET", default="")

def _load_dictionary_data():
    try:
        p = os.path.join(settings.BASE_DIR, "laundry_manager", "json_data", "dictionary.json")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("dictionary.json 로드 실패: %s", e)
        return {}

def _ymd(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def _start_end_for_months(months_back: int = 18):
    today = date.today()
    total = today.year * 12 + (today.month - 1) - months_back
    sy, sm = divmod(total, 12)
    sm += 1
    start = date(sy, sm, 1)
    return _ymd(start), _ymd(today)

def get_naver_trend_data(keywords, months_back=18, time_unit="month", max_keywords=5):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return []
    url = "https://naveropenapi.apigw.ntruss.com/datalab/v1/search"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json",
    }
    start, end = _start_end_for_months(months_back)
    kw = [k.strip() for k in (keywords or []) if isinstance(k, str) and k.strip()][:max_keywords]
    if not kw:
        return []
    body = {
        "startDate": start,
        "endDate": end,
        "timeUnit": time_unit,
        "keywordGroups": [{"groupName": "인기 검색어", "keywords": kw}],
    }
    try:
        r = requests.post(url, data=json.dumps(body), headers=headers, timeout=10)
        if r.status_code != 200:
            logger.warning("Naver Datalab 실패 status=%s text=%s", r.status_code, r.text[:200])
            return []
        # 그래프 데이터가 필요하면 r.json()["results"][0]["data"] 사용
        return kw
    except requests.RequestException as e:
        logger.warning("Naver Datalab 예외: %s", e)
        return []

def dictionary_view(request):
    data = _load_dictionary_data()
    query = request.GET.get("query")

    category_map = {
        "how_to_use_machine": "세탁 방법",
        "dry_method": "건조 방법",
        "storage_method": "보관 방법",
        "removal_smell": "냄새 제거 방법",
        "words": "용어 사전",
    }
    category_list = list(category_map.values())
    processed = {}

    def prep(item):
        i = item.copy()
        i["json_data"] = json.dumps(item, ensure_ascii=False)
        return i

    if query:
        if query in category_list:
            key = next((k for k, v in category_map.items() if v == query), None)
            if key and key in data:
                processed[query] = [prep(i) for i in data[key]]
        else:
            for key, display in category_map.items():
                items = data.get(key, [])
                filt = []
                for item in items:
                    s = (
                        item.get("title", "")
                        + item.get("description", "")
                        + json.dumps(item.get("content", ""), ensure_ascii=False)
                        + json.dumps(item.get("Washing_Steps", []), ensure_ascii=False)
                        + json.dumps(item.get("tip", []), ensure_ascii=False)
                        + json.dumps(item.get("not_to_do", []), ensure_ascii=False)
                        + json.dumps(item.get("Other_Information", []), ensure_ascii=False)
                    ).lower()
                    if query.lower() in s:
                        filt.append(prep(item))
                if filt:
                    processed[display] = filt
    else:
        for key, display in category_map.items():
            processed[display] = [prep(i) for i in data.get(key, [])]

    # 인기 검색어(제목 기반 상위 5개만)
    titles = []
    for key in data:
        for item in data.get(key, []):
            t = item.get("title")
            if t:
                titles.append(t.strip())
    uniq_titles = list(dict.fromkeys(titles))[:5]
    frequent_searches = get_naver_trend_data(uniq_titles)

    ctx = {
        "query": query,
        "is_category_query": (query in category_list) if query else False,
        "category_list": category_list,
        "dictionary_data": processed,
        "frequent_searches": frequent_searches,
    }
    return render(request, "laundry_manager/dictionary.html", ctx)

# 과거 호환용 별칭
dictionary = dictionary_view
