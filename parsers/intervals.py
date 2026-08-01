import requests
import streamlit as st
from datetime import date, timedelta

INTERVALS_BASE = "https://intervals.icu/api/v1"


def _get_credentials():
    # Tenta secrets do Streamlit primeiro
    try:
        athlete_id = st.secrets["INTERVALS_ATHLETE_ID"]
        api_key = st.secrets["INTERVALS_API_KEY"]
        if athlete_id and api_key:
            return athlete_id, api_key
    except Exception:
        pass
    # Fallback: credenciais salvas no state pelo usuário
    try:
        creds = st.session_state.app_state.get("intervals_credentials", {})
        aid = creds.get("athlete_id")
        key = creds.get("api_key")
        if aid and key:
            return aid, key
    except Exception:
        pass
    return None, None


def is_configured() -> bool:
    aid, key = _get_credentials()
    return bool(aid and key)


def _auth(api_key: str):
    return ("API_KEY", api_key)


import json
import os

_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "intervals_cache.json",
)


def _read_cache() -> list[dict]:
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_cache(data: list[dict]):
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


class IntervalsStale(Exception):
    """API falhou; devolve cache antigo. O chamador decide se aceita ou avisa."""
    def __init__(self, motivo: str, cached: list[dict]):
        self.motivo = motivo
        self.cached = cached
        super().__init__(motivo)


def fetch_wellness(days: int = 7, timeout: int = 8, allow_cache_fallback: bool = True) -> list[dict]:
    """Retorna dados de wellness (HRV, FC repouso, sono, peso) dos últimos N dias.

    Em caso de falha, se allow_cache_fallback=True (uso no boot, não pode travar
    a página), devolve o cache local — que pode estar bem desatualizado.
    Se allow_cache_fallback=False (sync manual, o usuário está esperando um
    resultado de verdade), levanta IntervalsStale em vez de mentir "sucesso"
    com dado velho.
    """
    athlete_id, api_key = _get_credentials()
    if not athlete_id or not api_key:
        return []

    oldest = str(date.today() - timedelta(days=days))
    newest = str(date.today())

    def _fallback(motivo: str):
        cached = _read_cache()
        if not allow_cache_fallback:
            raise IntervalsStale(motivo, cached)
        if cached:
            return cached
        raise RuntimeError(f"{motivo} e sem cache em {_CACHE_PATH}")

    try:
        resp = requests.get(
            f"{INTERVALS_BASE}/athlete/{athlete_id}/wellness",
            auth=_auth(api_key),
            params={"oldest": oldest, "newest": newest},
            timeout=timeout,
        )
    except requests.exceptions.RequestException as e:
        return _fallback(f"{type(e).__name__} ({timeout}s)")
    if resp.status_code == 401:
        return _fallback("credencial do Intervals inválida — reconecte na aba ⚙️ "
                         "(API key em intervals.icu → Settings → Developer)")
    if resp.status_code == 403:
        return _fallback("athlete ID incorreto — deve começar com 'i' (ex.: i607029)")
    if resp.status_code != 200:
        return _fallback(f"HTTP {resp.status_code} ({resp.text[:80]})")

    results = []
    for entry in resp.json():
        d = entry.get("id", "")
        if not d:
            continue
        sleep_secs = entry.get("sleepSecs") or 0
        ctl = entry.get("ctl")
        atl = entry.get("atl")
        # A API não devolve tsb no endpoint de wellness — sempre vem null.
        # Frescor é CTL − ATL por definição; calcular aqui, senão o card
        # "Frescor (TSB)" fica em "—" mesmo com carga disponível.
        tsb = entry.get("tsb")
        if tsb is None and ctl is not None and atl is not None:
            tsb = round(ctl - atl, 1)
        results.append({
            "data": d,
            "hrv": entry.get("hrv"),
            "fc_repouso": entry.get("restingHR"),
            "sono_horas": round(sleep_secs / 3600, 1) if sleep_secs else None,
            "peso": entry.get("weight"),
            "ctl": ctl,   # fitness (forma)
            "atl": atl,   # fadiga
            "tsb": tsb,   # frescor (form)
        })
    results = sorted(results, key=lambda x: x["data"], reverse=True)
    if results:
        _write_cache(results)
    return results


def fetch_today_form() -> dict | None:
    """Retorna CTL/ATL/TSB de hoje para o score de recuperação."""
    wellness = fetch_wellness(days=1)
    today = str(date.today())
    for w in wellness:
        if w["data"] == today:
            return w
    return wellness[0] if wellness else None
