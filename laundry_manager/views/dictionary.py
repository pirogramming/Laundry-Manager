import os, json
from django.conf import settings
from django.shortcuts import render

def _load_dictionary_data():
    try:
        p = os.path.join(settings.BASE_DIR, 'laundry_manager', 'json_data', 'dictionary.json')
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def dictionary_view(request):
    data = _load_dictionary_data()
    query = request.GET.get('query')
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
        i['json_data'] = json.dumps(item, ensure_ascii=False)
        return i

    if query:
        if query in category_list:
            key = next((k for k, v in category_map.items() if v == query), None)
            if key and key in data:
                processed[query] = [prep(i) for i in data[key]]
        else:
            for key, display in category_map.items():
                items = data.get(key, [])
                filtered = []
                for item in items:
                    s = (
                        item.get("title", "") +
                        item.get("description", "") +
                        json.dumps(item.get("content",""), ensure_ascii=False) +
                        json.dumps(item.get("Washing_Steps", []), ensure_ascii=False) +
                        json.dumps(item.get("tip", []), ensure_ascii=False) +
                        json.dumps(item.get("not_to_do", []), ensure_ascii=False) +
                        json.dumps(item.get("Other_Information", []), ensure_ascii=False)
                    ).lower()
                    if query.lower() in s:
                        filtered.append(prep(item))
                if filtered:
                    processed[display] = filtered
    else:
        for key, display in category_map.items():
            processed[display] = [prep(i) for i in data.get(key, [])]

    context = {
        'query': query,
        'is_category_query': query in category_list if query else False,
        'category_list': category_list,
        'dictionary_data': processed,
        'frequent_searches': [],
    }
    return render(request, 'laundry_manager/dictionary.html', context)
