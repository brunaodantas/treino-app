import streamlit as st
import requests
from datetime import datetime

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"
REDIRECT_URI = "https://treino-bruno.streamlit.app"
SCOPE = "activity:read_all,activity:write"


def get_client_id() -> str:
    try:
        return st.secrets["STRAVA_CLIENT_ID"]
    except Exception:
        return ""


def get_client_secret() -> str:
    try:
        return st.secrets["STRAVA_CLIENT_SECRET"]
    except Exception:
        return ""


def get_auth_url() -> str:
    client_id = get_client_id()
    params = (
        f"client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPE}"
        f"&approval_prompt=auto"
    )
    return f"{STRAVA_AUTH_URL}?{params}"


def exchange_code(code: str) -> dict:
    resp = requests.post(STRAVA_TOKEN_URL, data={
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "code": code,
        "grant_type": "authorization_code",
    })
    return resp.json()


def refresh_token(refresh_tok: str) -> dict:
    resp = requests.post(STRAVA_TOKEN_URL, data={
        "client_id": get_client_id(),
        "client_secret": get_client_secret(),
        "refresh_token": refresh_tok,
        "grant_type": "refresh_token",
    })
    return resp.json()


def get_valid_token(state: dict, save_fn) -> str:
    """Returns a valid access token, refreshing if expired."""
    strava = state.get("strava_tokens", {})
    if not strava:
        return ""

    expires_at = strava.get("expires_at", 0)
    now = int(datetime.now().timestamp())

    if now >= expires_at - 60:
        new = refresh_token(strava["refresh_token"])
        if "access_token" in new:
            state["strava_tokens"] = {
                "access_token": new["access_token"],
                "refresh_token": new.get("refresh_token", strava["refresh_token"]),
                "expires_at": new["expires_at"],
                "athlete": strava.get("athlete", {}),
            }
            save_fn(state)
            return new["access_token"]
        return ""

    return strava.get("access_token", "")


def fetch_recent_activities(token: str, per_page: int = 50) -> list:
    """Fetch recent activities from Strava API."""
    resp = requests.get(
        f"{STRAVA_API_BASE}/athlete/activities",
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": per_page, "page": 1},
    )
    if resp.status_code == 200:
        return resp.json()
    return []


def create_activity(token: str, name: str, sport_type: str, start_date_local: str,
                    elapsed_time: int, description: str = "") -> dict:
    """POST a new activity to Strava. Returns the created activity dict or error dict."""
    resp = requests.post(
        f"{STRAVA_API_BASE}/activities",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "sport_type": sport_type,
            "start_date_local": start_date_local,
            "elapsed_time": elapsed_time,
            "description": description,
            "trainer": 1,
        },
    )
    return resp.json()


def is_connected(state: dict) -> bool:
    return bool(state.get("strava_tokens", {}).get("access_token"))
