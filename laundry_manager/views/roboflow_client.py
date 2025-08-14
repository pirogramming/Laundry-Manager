# laundry_manager/utils/roboflow_client.py
import io
import os
import logging
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings

logger = logging.getLogger(__name__)

_ROBOFLOW_BASE = "https://classify.roboflow.com"

def _session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"])
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def _endpoint() -> str:
    model = settings.RF_CLASSIFY_MODEL
    version = str(settings.RF_CLASSIFY_VERSION)
    return f"{_ROBOFLOW_BASE}/{model}/{version}"

def classify_file(file_path: str) -> Dict[str, Any]:
    """
    로컬 파일 경로를 Roboflow 분류 API로 전송.
    반환: {"ok": bool, "label": Optional[str], "confidence": Optional[float], "raw": dict, "error": Optional[str]}
    """
    if not settings.RF_ENABLED:
        return {"ok": False, "label": None, "confidence": None, "raw": {}, "error": "RF_DISABLED"}

    if not os.path.exists(file_path):
        return {"ok": False, "label": None, "confidence": None, "raw": {}, "error": "FILE_NOT_FOUND"}

    url = _endpoint()
    params = {
        "api_key": settings.ROBOFLOW_API_KEY,
        # Roboflow 분류엔진은 confidence 파라미터를 허용(모델별 상이할 수 있어 서버에서 필터도 한 번 더 함)
        "confidence": settings.RF_CLASSIFY_THRESHOLD
    }

    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            resp = _session().post(url, params=params, files=files, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        label, conf = _extract_label_confidence(data, settings.RF_CLASSIFY_THRESHOLD)
        return {"ok": True if label is not None else False,
                "label": label, "confidence": conf, "raw": data, "error": None}
    except requests.RequestException as e:
        logger.exception("Roboflow request failed")
        return {"ok": False, "label": None, "confidence": None, "raw": {}, "error": str(e)}
    except ValueError as e:
        # json decode 등
        logger.exception("Roboflow response parse failed")
        return {"ok": False, "label": None, "confidence": None, "raw": {}, "error": f"PARSE_ERROR: {e}"}

def _extract_label_confidence(data: Dict[str, Any], threshold: float) -> (Optional[str], Optional[float]):
    """
    Roboflow 분류 응답의 다양한 포맷을 안전하게 파싱.
    알려진 형태 예:
      {"predictions":[{"class":"washing","confidence":0.92}]}
      또는 {"top":"washing","confidences":{"washing":0.92,"dry":0.03,...}}
    """
    if not isinstance(data, dict):
        return None, None

    # 1) predictions 리스트 우선
    preds = data.get("predictions")
    if isinstance(preds, list) and preds:
        p0 = preds[0]
        cls = p0.get("class") or p0.get("label") or p0.get("top")
        conf = p0.get("confidence") or p0.get("score")
        try:
            conf = float(conf) if conf is not None else None
        except (TypeError, ValueError):
            conf = None
        if cls and (conf is None or conf >= threshold):
            return cls, conf

    # 2) confidences 딕셔너리
    confs = data.get("confidences") or (preds and isinstance(preds, dict) and preds.get("confidences"))
    if isinstance(confs, dict) and confs:
        # 최대 확률 라벨 선택
        top_label = max(confs, key=lambda k: confs[k])
        top_conf = confs[top_label]
        try:
            top_conf = float(top_conf)
        except (TypeError, ValueError):
            top_conf = None
        if top_conf is None or top_conf >= threshold:
            return top_label, top_conf

    # 3) top 필드만 존재
    if data.get("top"):
        return data.get("top"), None

    return None, None
