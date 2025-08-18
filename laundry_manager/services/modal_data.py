# laundry_manager/services/modal_data.py
import json, re, os
from pathlib import Path
from functools import lru_cache
from django.conf import settings

MATERIALS_JSON = Path(settings.BASE_DIR) / "laundry_manager" / "json_data" / "blackup.json"
STAINS_JSON    = Path(settings.BASE_DIR) / "laundry_manager" / "json_data" / "persil_v2.json"

@lru_cache(maxsize=1)
def load_stain_titles():
    try:
        with open(STAINS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and k.lower() == "title" and isinstance(v, str):
                    yield v.strip()
                else:
                    yield from walk(v)
        elif isinstance(node, list):
            for it in node:
                yield from walk(it)

    seen, out = set(), []
    for t in walk(data):
        if t and t not in seen:
            seen.add(t); out.append(t)
    return out

@lru_cache(maxsize=1)
def load_material_items():
    try:
        with open(MATERIALS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    items = data.get("material_washing_tips") or []
    result, seen = [], set()
    for row in items:
        raw = (row.get("material") or "").strip()
        if not raw:
            continue
        m = re.match(r"^\s*([^()]+?)\s*(?:\(([^)]+)\))?\s*$", raw)
        kor = (m.group(1).strip() if m else raw)
        eng = m.group(2).strip() if (m and m.group(2)) else ""
        if kor in seen:
            continue
        seen.add(kor)
        result.append({
            "kor": kor,
            "eng": eng,
            "raw": raw,
            "description": (row.get("description") or "").strip(),
            "warning": (row.get("warning") or "").strip(),
        })
    return result
