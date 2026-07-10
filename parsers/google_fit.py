import streamlit as st
import requests
from datetime import datetime, timedelta

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_FIT_BASE = "https://www.googleapis.com/fitness/v1/users/me"
REDIRECT_URI = "https://treino-bruno.streamlit.app"
SCOPES = " ".join([
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.body.read",
])


def get_client_id() -> str:
    try:
        return st.secrets["GOOGLE_CLIENT_ID"]
    except Exception:
        return ""


def get_client_secret() -> str:
    try:
        return st.secrets["GOOGLE_CLIENT_SECRET"]
    except Exception:
        return ""


def get_auth_url() -> str:
    client_id = get_client_id()
    import urllib.parse
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": "googlefit",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(code: str) -> dict:
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    })
    return resp.json()


def refresh_token(refresh_tok: str) -> dict:
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "refresh_token": refresh_tok,
        "grant_type": "refresh_token",
    })
    return resp.json()


def get_valid_token(state: dict, save_fn) -> str:
    gfit = state.get("gfit_tokens", {})
    if not gfit:
        return ""
    expires_at = gfit.get("expires_at", 0)
    now = int(datetime.now().timestamp())
    if now >= expires_at - 60:
        new = refresh_token(gfit["refresh_token"])
        if "access_token" in new:
            state["gfit_tokens"] = {
                "access_token": new["access_token"],
                "refresh_token": gfit["refresh_token"],
                "expires_at": int(datetime.now().timestamp()) + new.get("expires_in", 3600),
            }
            save_fn(state)
            return new["access_token"]
        return ""
    return gfit.get("access_token", "")


def is_connected(state: dict) -> bool:
    return bool(state.get("gfit_tokens", {}).get("access_token"))


def _ms_to_ts(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000)


def _midnight_local(days_ago: int = 0) -> int:
    """Retorna meia-noite local de N dias atrás em milissegundos."""
    from datetime import date
    d = date.today() - timedelta(days=days_ago)
    dt = datetime(d.year, d.month, d.day, 0, 0, 0)
    return int(dt.timestamp() * 1000)


def _now_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


def _days_ago_ms(days: int) -> int:
    return _midnight_local(days)


def fetch_steps(token: str, days: int = 7) -> list[dict]:
    """Retorna passos diários dos últimos N dias."""
    body = {
        "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": _days_ago_ms(days),
        "endTimeMillis": _now_ms(),
    }
    resp = requests.post(
        f"{GOOGLE_FIT_BASE}/dataset:aggregate",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    if resp.status_code != 200:
        return []
    results = []
    for bucket in resp.json().get("bucket", []):
        start_ms = int(bucket.get("startTimeMillis", 0))
        date_str = _ms_to_ts(start_ms).strftime("%Y-%m-%d")
        steps = 0
        for ds in bucket.get("dataset", []):
            for pt in ds.get("point", []):
                for val in pt.get("value", []):
                    steps += val.get("intVal", 0)
        results.append({"data": date_str, "passos": steps})
    return results


def fetch_calories(token: str, days: int = 7) -> list[dict]:
    """Retorna calorias ativas diárias dos últimos N dias."""
    body = {
        "aggregateBy": [{"dataTypeName": "com.google.calories.expended"}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": _days_ago_ms(days),
        "endTimeMillis": _now_ms(),
    }
    resp = requests.post(
        f"{GOOGLE_FIT_BASE}/dataset:aggregate",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    if resp.status_code != 200:
        return []
    results = []
    for bucket in resp.json().get("bucket", []):
        start_ms = int(bucket.get("startTimeMillis", 0))
        date_str = _ms_to_ts(start_ms).strftime("%Y-%m-%d")
        cals = 0.0
        for ds in bucket.get("dataset", []):
            for pt in ds.get("point", []):
                for val in pt.get("value", []):
                    cals += val.get("fpVal", 0)
        results.append({"data": date_str, "calorias": round(cals)})
    return results


def fetch_resting_hr(token: str, days: int = 7) -> list[dict]:
    """Retorna FC de repouso diária dos últimos N dias."""
    body = {
        "aggregateBy": [{"dataTypeName": "com.google.heart_rate.bpm"}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": _days_ago_ms(days),
        "endTimeMillis": _now_ms(),
    }
    resp = requests.post(
        f"{GOOGLE_FIT_BASE}/dataset:aggregate",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    if resp.status_code != 200:
        return []
    results = []
    for bucket in resp.json().get("bucket", []):
        start_ms = int(bucket.get("startTimeMillis", 0))
        date_str = _ms_to_ts(start_ms).strftime("%Y-%m-%d")
        hr_min = None
        for ds in bucket.get("dataset", []):
            for pt in ds.get("point", []):
                for val in pt.get("value", []):
                    v = val.get("fpVal")
                    if v and (hr_min is None or v < hr_min):
                        hr_min = v
        if hr_min:
            results.append({"data": date_str, "fc_repouso": round(hr_min)})
    return results


def fetch_sleep(token: str, days: int = 7) -> list[dict]:
    """Retorna duração de sono (horas) dos últimos N dias."""
    body = {
        "aggregateBy": [{"dataTypeName": "com.google.sleep.segment"}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": _days_ago_ms(days),
        "endTimeMillis": _now_ms(),
    }
    resp = requests.post(
        f"{GOOGLE_FIT_BASE}/dataset:aggregate",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    if resp.status_code != 200:
        return []
    results = []
    for bucket in resp.json().get("bucket", []):
        start_ms = int(bucket.get("startTimeMillis", 0))
        date_str = _ms_to_ts(start_ms).strftime("%Y-%m-%d")
        sleep_ms = 0
        for ds in bucket.get("dataset", []):
            for pt in ds.get("point", []):
                # type 1 = light, 2 = deep, 3 = REM, 4 = awake
                sleep_type = 0
                for val in pt.get("value", []):
                    sleep_type = val.get("intVal", 0)
                if sleep_type in (1, 2, 3):
                    end_ns = int(pt.get("endTimeNanos", 0))
                    start_ns = int(pt.get("startTimeNanos", 0))
                    sleep_ms += (end_ns - start_ns) / 1_000_000
        hours = round(sleep_ms / 3_600_000, 1)
        if hours > 0:
            results.append({"data": date_str, "sono_horas": hours})
    return results


def fetch_all(token: str, days: int = 7) -> dict:
    """Busca todos os dados do Google Fit de uma vez."""
    return {
        "steps": fetch_steps(token, days),
        "calories": fetch_calories(token, days),
        "resting_hr": fetch_resting_hr(token, days),
        "sleep": fetch_sleep(token, days),
    }
