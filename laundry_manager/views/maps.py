import os, json
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render
from pyproj import Transformer

def map_test_view(request):
    return render(request, 'laundry_manager/map-test.html', {
        'NAVER_MAP_CLIENT_KEY': settings.NAVER_MAP_CLIENT_KEY
    })

def _in_seoul(lat, lng):
    return 37.3 <= lat <= 37.75 and 126.7 <= lng <= 127.2

_T_2097 = Transformer.from_crs("EPSG:2097", "EPSG:4326", always_xy=True)
_T_5179 = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)

def _to_wgs84(x, y):
    try:
        lng, lat = _T_2097.transform(float(x), float(y))
        if _in_seoul(lat, lng): return lat, lng
    except: pass
    try:
        lng, lat = _T_5179.transform(float(x), float(y))
        if _in_seoul(lat, lng): return lat, lng
    except: pass
    return None

def shops_mapo(request):
    data_path = os.path.join(settings.BASE_DIR, "data", "서울시 마포구 세탁업 인허가 정보.json")
    with open(data_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    rows = raw.get("DATA", [])
    out = []
    for r in rows:
        if r.get("trdstatenm") != "영업/정상":
            continue
        x, y = (r.get("x","").strip(), r.get("y","").strip())
        if not x or not y: continue
        ll = _to_wgs84(x, y)
        if not ll: continue
        lat, lng = ll
        out.append({
            "name": r.get("bplcnm"),
            "addr": r.get("rdnwhladdr") or r.get("sitewhladdr"),
            "lat": lat,
            "lng": lng,
        })
    return JsonResponse(out, safe=False)
