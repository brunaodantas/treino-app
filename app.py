import streamlit as st
import streamlit.components.v1 as _components
import json
import os
from datetime import date, timedelta
from streamlit_javascript import st_javascript

_LS_KEY = "treino_hub_state"

st.set_page_config(
    page_title="Treino Hub",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* Esconde barra superior e rodapé do Streamlit */
header[data-testid="stHeader"] { display: none; }
footer { display: none; }
#MainMenu { display: none; }
/* Botões maiores para toque */
.stButton > button {
    min-height: 3rem;
    font-size: 1rem;
    border-radius: 10px;
}
/* Inputs numéricos maiores */
.stNumberInput input {
    font-size: 1.1rem;
    height: 2.8rem;
}
/* Tabs roláveis em tela pequena */
.stTabs [data-baseweb="tab-list"] {
    overflow-x: auto;
    flex-wrap: nowrap;
}
/* Expanders com padding confortável */
.streamlit-expanderHeader {
    font-size: 1rem;
    padding: 0.6rem 0;
}
/* Remove padding lateral excessivo no mobile */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")

# ── Default state ──────────────────────────────────────────────────────────────
def _last_monday() -> str:
    today = date.today()
    return str(today - timedelta(days=today.weekday()))

DEFAULT_STATE = {
    "current_index": 0,
    "adaptation_week_override": None,
    "workout_log": [],
    "workout_history": [],
    "app_start_date": str(date.today()),
    "running_week_start": _last_monday(),
    "running_base_km": 3.0,
    "use_e_next": False,
}

# ── State persistence ──────────────────────────────────────────────────────────
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            # Merge with defaults so new keys always exist
            merged = {**DEFAULT_STATE, **saved}
            return merged
        except Exception:
            pass
    return DEFAULT_STATE.copy()


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # Persist to browser localStorage so state survives server restarts
    payload = json.dumps(state, ensure_ascii=False)
    _components.html(
        f"<script>localStorage.setItem('{_LS_KEY}', {json.dumps(payload)});</script>",
        height=0,
    )


# ── Session state bootstrap ────────────────────────────────────────────────────
if "app_state" not in st.session_state:
    _ls_raw = st_javascript(f"localStorage.getItem('{_LS_KEY}')")
    if _ls_raw == 0:
        # JS pending on first render — load from file and rerun to get localStorage value
        st.session_state.app_state = load_state()
        st.rerun()
    elif isinstance(_ls_raw, str):
        try:
            st.session_state.app_state = {**DEFAULT_STATE, **json.loads(_ls_raw)}
        except Exception:
            st.session_state.app_state = load_state()
    else:
        st.session_state.app_state = load_state()

STRAVA_CACHE = os.path.join(BASE_DIR, "data", "strava_cache.json")
HEALTH_CACHE = os.path.join(BASE_DIR, "data", "health_cache.json")

if "strava_df" not in st.session_state:
    if os.path.exists(STRAVA_CACHE):
        import pandas as pd, json as _json
        with open(STRAVA_CACHE, encoding="utf-8") as _f:
            _records = _json.load(_f)
        _df = pd.DataFrame(_records)
        if "data" in _df.columns:
            _df["data"] = pd.to_datetime(_df["data"], errors="coerce")
        st.session_state.strava_df = _df
    else:
        st.session_state.strava_df = None

if "health_data" not in st.session_state:
    if os.path.exists(HEALTH_CACHE):
        import json as _json
        from collections import defaultdict
        with open(HEALTH_CACHE, encoding="utf-8") as _f:
            _hd = _json.load(_f)
        _hd["daily_steps"] = defaultdict(float, _hd.get("daily_steps", {}))
        _hd["daily_calories"] = defaultdict(float, _hd.get("daily_calories", {}))
        _hd["daily_resting_hr"] = defaultdict(list, {k: [v] for k, v in _hd.get("daily_resting_hr", {}).items()})
        st.session_state.health_data = _hd
    else:
        st.session_state.health_data = None

if "hevy_df" not in st.session_state:
    st.session_state.hevy_df = None


# Sidebar vazia — conteúdo movido para aba ⚙️


# ── Strava OAuth callback ──────────────────────────────────────────────────────
_params = st.query_params
if "code" in _params and not st.session_state.app_state.get("strava_tokens"):
    from parsers.strava_api import exchange_code
    _code = _params["code"]
    _token_data = exchange_code(_code)
    if "access_token" in _token_data:
        st.session_state.app_state["strava_tokens"] = {
            "access_token": _token_data["access_token"],
            "refresh_token": _token_data["refresh_token"],
            "expires_at": _token_data["expires_at"],
            "athlete": _token_data.get("athlete", {}),
        }
        save_state(st.session_state.app_state)
        st.query_params.clear()
        st.toast("✅ Strava conectado!", icon="🏃")
        st.rerun()


# ── Navigation ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🏋️ Musculação",
    "🏃 Corrida",
    "📈 Analytics",
    "⚙️",
])

state = st.session_state.app_state

with tab1:
    from views.dashboard import render_dashboard
    render_dashboard(state, save_state)

with tab2:
    from views.musculacao import render_musculacao
    render_musculacao(state, st.session_state.hevy_df, save_state)

with tab3:
    from views.corrida import render_corrida
    render_corrida(state, st.session_state.strava_df, st.session_state.health_data)

with tab4:
    from views.analytics import render_analytics
    render_analytics(st.session_state.strava_df, st.session_state.health_data)

with tab5:
    st.markdown("### ⚙️ Configurações")

    st.subheader("💾 Backup")
    state_json = json.dumps(st.session_state.app_state, ensure_ascii=False, indent=2)
    st.download_button(
        "⬇️ Baixar backup",
        data=state_json,
        file_name="state.json",
        mime="application/json",
        use_container_width=True,
    )
    state_restore = st.file_uploader(
        "⬆️ Restaurar backup", type=["json"], key="state_restore",
    )
    if state_restore is not None:
        try:
            uploaded = json.load(state_restore)
            merged = {**DEFAULT_STATE, **uploaded}
            st.session_state.app_state = merged
            save_state(merged)
            st.success("✅ Backup restaurado!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao restaurar: {e}")

    st.markdown("---")

    from parsers.strava_api import get_auth_url, is_connected, get_client_id
    if get_client_id():
        st.subheader("🏃 Strava")
        _s = st.session_state.app_state
        if is_connected(_s):
            athlete = _s.get("strava_tokens", {}).get("athlete", {})
            _name = athlete.get("firstname", "Conectado")
            st.success(f"✅ Conectado como {_name}")
            if st.button("Desconectar Strava", use_container_width=True):
                _s.pop("strava_tokens", None)
                save_state(_s)
                st.rerun()
        else:
            st.link_button("🔗 Conectar Strava", get_auth_url(), use_container_width=True)

    st.markdown("---")
    st.caption("v1.3 · treino-bruno.streamlit.app")
