import requests
import streamlit as st
from datetime import date, timedelta

INTERVALS_BASE = "https://intervals.icu/api/v1"


def _get_credentials():
    try:
        athlete_id = st.secrets["INTERVALS_ATHLETE_ID"]
        api_key = st.secrets["INTERVALS_API_KEY"]
        return athlete_id, api_key
    except Exception:
        return None, None


def is_configured() -> bool:
    aid, key = _get_credentials()
    return bool(aid and key)


def _auth(api_key: str):
    return ("API_KEY", api_key)


def fetch_wellness(days: int = 7) -> list[dict]:
    """Retorna dados de wellness (HRV, FC repouso, sono, peso) dos últimos N dias."""
    athlete_id, api_key = _get_credentials()
    if not athlete_id or not api_key:
        return []

    oldest = str(date.today() - timedelta(days=days))
    newest = str(date.today())

    resp = requests.get(
        f"{INTERVALS_BASE}/athlete/{athlete_id}/wellness",
        auth=_auth(api_key),
        params={"oldest": oldest, "newest": newest},
        timeout=10,
    )
    if resp.status_code != 200:
        return []

    results = []
    for entry in resp.json():
        d = entry.get("id", "")
        if not d:
            continue
        sleep_secs = entry.get("sleepSecs") or 0
        results.append({
            "data": d,
            "hrv": entry.get("hrv"),
            "fc_repouso": entry.get("restingHR"),
            "sono_horas": round(sleep_secs / 3600, 1) if sleep_secs else None,
            "peso": entry.get("weight"),
            "ctl": entry.get("ctl"),   # fitness (forma)
            "atl": entry.get("atl"),   # fadiga
            "tsb": entry.get("tsb"),   # frescor (form)
        })
    return sorted(results, key=lambda x: x["data"], reverse=True)


def fetch_today_form() -> dict | None:
    """Retorna CTL/ATL/TSB de hoje para o score de recuperação."""
    wellness = fetch_wellness(days=1)
    today = str(date.today())
    for w in wellness:
        if w["data"] == today:
            return w
    return wellness[0] if wellness else None
