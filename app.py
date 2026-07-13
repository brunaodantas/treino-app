import streamlit as st
import streamlit.components.v1 as _components
import json
import os
from datetime import date, timedelta
from streamlit_javascript import st_javascript

_LS_KEY = "treino_hub_state"
EXPORT_FILE = None  # definido após BASE_DIR

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
EXPORT_FILE = os.path.join(BASE_DIR, "dados-treino.json")

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
    "checkin": {},
    "schedule_week_offset": 0,
}

# ── State persistence ──────────────────────────────────────────────────────────
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            merged = {**DEFAULT_STATE, **saved}
            return merged
        except Exception:
            pass
    return DEFAULT_STATE.copy()


def export_dados_treino(state: dict):
    """Exporta snapshot dos dados de treino para dados-treino.json."""
    from logic.schedule import get_next_workout, WORKOUT_LABELS

    cutoff = str(date.today() - timedelta(days=30))

    next_wk = get_next_workout(state)
    fila = {
        "sequencia": ["A", "B", "C", "D"],
        "indice_atual": state.get("current_index", 0),
        "proximo": next_wk,
        "descricao_proximo": WORKOUT_LABELS.get(next_wk, ""),
        "treino_E_ativo": state.get("use_e_next", False),
    }

    historico = []
    volume_map = {}
    for entry in state.get("workout_history", []):
        if entry.get("date", "") >= cutoff:
            key = (entry.get("date"), entry.get("workout"))
            volume_map[key] = entry.get("volume_total", 0)

    for entry in state.get("workout_log", []):
        d = entry.get("date", "")
        if d >= cutoff:
            wk = entry.get("workout", "")
            historico.append({
                "data": d,
                "treino": wk,
                "tipo": "musculacao",
                "concluido_em": entry.get("completed_at", ""),
                "volume_kg": volume_map.get((d, wk), None),
            })

    try:
        sdf = st.session_state.get("strava_df")
        if sdf is not None and not sdf.empty and "data" in sdf.columns:
            import pandas as pd
            cutoff_dt = pd.Timestamp(cutoff)
            runs = sdf[
                (sdf["data"] >= cutoff_dt) &
                (sdf.get("tipo", pd.Series(dtype=str)).str.lower().str.contains("corrida|run", na=False))
            ] if "tipo" in sdf.columns else sdf[sdf["data"] >= cutoff_dt]
            for _, row in runs.iterrows():
                historico.append({
                    "data": str(row["data"])[:10],
                    "treino": row.get("nome", "Corrida"),
                    "tipo": "corrida",
                    "distancia_km": row.get("distancia_km"),
                    "pace_min_km": row.get("pace_min_km"),
                    "fc_media": row.get("fc_media"),
                })
    except Exception:
        pass

    historico.sort(key=lambda x: x["data"], reverse=True)

    export = {
        "gerado_em": str(date.today()),
        "fila_treinos": fila,
        "historico_30_dias": historico,
        "metricas": state.get("metricas", {}),
    }

    try:
        with open(EXPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(export, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    export_dados_treino(state)
    payload = json.dumps(state, ensure_ascii=False)
    _components.html(
        f"<script>localStorage.setItem('{_LS_KEY}', {json.dumps(payload)});</script>",
        height=0,
    )


# ── Session state bootstrap ────────────────────────────────────────────────────
if "app_state" not in st.session_state:
    _ls_raw = st_javascript(f"localStorage.getItem('{_LS_KEY}')")
    if _ls_raw == 0:
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

# Força reset do cache se vier ?sync=1 na URL
if st.query_params.get("sync") == "1":
    st.session_state.pop("strava_df", None)
    st.query_params.clear()
    st.rerun()

if "strava_df" not in st.session_state:
    import pandas as pd, json as _json
    _base_records = []
    if os.path.exists(STRAVA_CACHE):
        with open(STRAVA_CACHE, encoding="utf-8") as _f:
            _base_records = _json.load(_f)

    _api_records = []
    _s = st.session_state.app_state
    if _s.get("strava_tokens"):
        try:
            from parsers.strava_api import get_valid_token, fetch_recent_activities
            _tok = get_valid_token(_s, save_state)
            if _tok:
                _raw = fetch_recent_activities(_tok, per_page=50)
                for a in _raw:
                    dist_km = a.get("distance", 0) / 1000
                    mov_s   = a.get("moving_time", 0)
                    pace    = (mov_s / 60 / dist_km) if dist_km > 0 else None
                    _api_records.append({
                        "data":         a.get("start_date_local", "")[:10],
                        "nome":         a.get("name", ""),
                        "tipo":         a.get("sport_type") or a.get("type", ""),
                        "distancia_km": round(dist_km, 2),
                        "duracao_min":  round(mov_s / 60, 1),
                        "pace_min_km":  round(pace, 2) if pace else None,
                        "fc_media":     a.get("average_heartrate"),
                        "fc_max":       a.get("max_heartrate"),
                        "strava_id":    a.get("id"),
                    })
        except Exception:
            pass

    if _api_records:
        _api_ids = {r["strava_id"] for r in _api_records if r.get("strava_id")}
        _filtered_base = [
            r for r in _base_records
            if r.get("strava_id") not in _api_ids
        ]
        _all = _api_records + _filtered_base
        # Persiste atividades novas no cache para não perder entre reinícios do servidor
        try:
            with open(STRAVA_CACHE, "w", encoding="utf-8") as _f:
                _json.dump(_all, _f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    else:
        _all = _base_records

    if _all:
        _df = pd.DataFrame(_all)
        if "data" in _df.columns:
            _df["data"] = pd.to_datetime(_df["data"], errors="coerce")
        _df = _df.sort_values("data", ascending=False).reset_index(drop=True)
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

# ── Google Fit data (carrega se conectado) ─────────────────────────────────────
if "gfit_data" not in st.session_state:
    _s = st.session_state.app_state
    if _s.get("gfit_tokens"):
        try:
            from parsers.google_fit import get_valid_token as gfit_token, fetch_all
            _tok = gfit_token(_s, save_state)
            if _tok:
                st.session_state.gfit_data = fetch_all(_tok, days=7)
            else:
                st.session_state.gfit_data = None
        except Exception:
            st.session_state.gfit_data = None
    else:
        st.session_state.gfit_data = None

# ── Intervals.icu data ─────────────────────────────────────────────────────────
if "intervals_data" not in st.session_state:
    try:
        from parsers.intervals import is_configured, fetch_wellness
        if is_configured():
            st.session_state.intervals_data = fetch_wellness(days=14)
        else:
            st.session_state.intervals_data = None
    except Exception:
        st.session_state.intervals_data = None

# Fallback: health_log.json local (mesma estrutura que intervals_data)
if "health_log_data" not in st.session_state:
    _hlog_path = os.path.join(BASE_DIR, "data", "health_log.json")
    if os.path.exists(_hlog_path):
        try:
            import json as _json
            with open(_hlog_path, encoding="utf-8") as _f:
                st.session_state.health_log_data = _json.load(_f)
        except Exception:
            st.session_state.health_log_data = None
    else:
        st.session_state.health_log_data = None

export_dados_treino(st.session_state.app_state)

# ── OAuth callbacks ────────────────────────────────────────────────────────────
_params = st.query_params

# Strava callback
if "code" in _params and _params.get("state", "") != "googlefit" and not st.session_state.app_state.get("strava_tokens"):
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

# Google Fit callback
if "code" in _params and _params.get("state", "") == "googlefit" and not st.session_state.app_state.get("gfit_tokens"):
    from parsers.google_fit import exchange_code as gfit_exchange
    from datetime import datetime
    _code = _params["code"]
    _token_data = gfit_exchange(_code)
    if "access_token" in _token_data:
        st.session_state.app_state["gfit_tokens"] = {
            "access_token": _token_data["access_token"],
            "refresh_token": _token_data.get("refresh_token", ""),
            "expires_at": int(datetime.now().timestamp()) + _token_data.get("expires_in", 3600),
        }
        save_state(st.session_state.app_state)
        st.query_params.clear()
        st.toast("✅ Google Fit conectado!", icon="❤️")
        st.rerun()


# ── Navigation ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "🥗 Cardápio",
    "🏋️ Musculação",
    "🏃 Corrida",
    "💤 Recuperação",
    "📈 Saúde",
    "⚙️",
])

state = st.session_state.app_state

with tab1:
    try:
        from views.dashboard import render_dashboard
        render_dashboard(state, save_state)
    except Exception as _dash_err:
        import traceback
        st.error(f"Erro no dashboard: {_dash_err}")
        st.code(traceback.format_exc())

with tab2:
    from views.cardapio import render_cardapio
    render_cardapio(state, save_state)

with tab3:
    from views.musculacao import render_musculacao
    render_musculacao(state, st.session_state.hevy_df, save_state)

with tab4:
    from views.corrida import render_corrida
    render_corrida(state, st.session_state.strava_df, st.session_state.health_data)

with tab5:
    from views.recuperacao import render_recuperacao
    render_recuperacao(
        state,
        st.session_state.gfit_data,
        st.session_state.health_data,
        st.session_state.intervals_data or st.session_state.get("health_log_data"),
    )

with tab6:
    from views.saude import render_saude
    render_saude()

with tab7:
    col_cfg, col_ref7 = st.columns([5, 1])
    with col_cfg:
        st.markdown("### ⚙️ Configurações")
    with col_ref7:
        if st.button("🔄", help="Recarregar", key="refresh_cfg"):
            _components.html("<script>window.parent.location.reload();</script>", height=0)

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

    # Strava
    from parsers.strava_api import get_auth_url, is_connected, get_client_id
    if get_client_id():
        st.subheader("🏃 Strava")
        _s = st.session_state.app_state
        if st.button("🔴 Forçar desconexão do Strava", use_container_width=True):
            _s.pop("strava_tokens", None)
            _components.html(f"""
<script>
try {{
  const s = JSON.parse(localStorage.getItem('{_LS_KEY}') || '{{}}');
  delete s.strava_tokens;
  localStorage.setItem('{_LS_KEY}', JSON.stringify(s));
  window.parent.location.reload();
}} catch(e) {{ window.parent.location.reload(); }}
</script>
""", height=0)
        if is_connected(_s):
            athlete = _s.get("strava_tokens", {}).get("athlete", {})
            _name = athlete.get("firstname", "Conectado")
            st.success(f"✅ Conectado como {_name}")
            col_sync_s, col_disc_s = st.columns(2)
            with col_sync_s:
                if st.button("🔄 Sincronizar Strava", use_container_width=True):
                    with st.spinner("Buscando atividades..."):
                        st.session_state.pop("strava_df", None)
                    st.toast("✅ Strava sincronizado!", icon="🏃")
                    st.rerun()
            with col_disc_s:
                if st.button("Desconectar Strava", use_container_width=True):
                    _s.pop("strava_tokens", None)
                    save_state(_s)
                    st.rerun()
        else:
            st.link_button("🔗 Conectar Strava", get_auth_url(), use_container_width=True)

    st.markdown("---")

    # Google Fit
    from parsers.google_fit import get_auth_url as gfit_auth_url, get_client_id as gfit_client_id, is_connected as gfit_connected
    st.subheader("❤️ Google Fit")
    _s = st.session_state.app_state
    if gfit_connected(_s):
        st.success("✅ Google Fit conectado")
        col_sync, col_disc = st.columns(2)
        with col_sync:
            if st.button("🔄 Sincronizar agora", use_container_width=True):
                st.session_state.pop("gfit_data", None)
                st.rerun()
        with col_disc:
            if st.button("Desconectar", use_container_width=True):
                _s.pop("gfit_tokens", None)
                st.session_state.gfit_data = None
                _components.html(f"""
<script>
try {{
  const s = JSON.parse(localStorage.getItem('{_LS_KEY}') || '{{}}');
  delete s.gfit_tokens;
  localStorage.setItem('{_LS_KEY}', JSON.stringify(s));
  window.parent.location.reload();
}} catch(e) {{ window.parent.location.reload(); }}
</script>
""", height=0)
    elif gfit_client_id():
        st.link_button("🔗 Conectar Google Fit", gfit_auth_url(), use_container_width=True)
    else:
        st.info("Configure GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET nos Secrets do Streamlit para ativar o Google Fit.")

    st.markdown("---")

    # Intervals.icu
    st.subheader("📊 Intervals.icu")
    _s = st.session_state.app_state
    _iv_creds = _s.get("intervals_credentials", {})
    _iv_connected = bool(_iv_creds.get("athlete_id") and _iv_creds.get("api_key"))
    if _iv_connected:
        st.success("✅ Intervals.icu conectado")
        col_sync_iv, col_disc_iv = st.columns(2)
        with col_sync_iv:
            if st.button("🔄 Sincronizar Intervals", use_container_width=True):
                st.session_state.pop("intervals_data", None)
                st.rerun()
        with col_disc_iv:
            if st.button("Desconectar Intervals", use_container_width=True):
                _s.pop("intervals_credentials", None)
                st.session_state.intervals_data = None
                save_state(_s)
                st.rerun()
    else:
        st.markdown("Entre com suas credenciais do Intervals.icu:")
        with st.form("intervals_form"):
            _aid_input = st.text_input("Athlete ID", placeholder="iXXXXXXX")
            _key_input = st.text_input("API Key", type="password", placeholder="sua chave API")
            if st.form_submit_button("💾 Conectar Intervals", use_container_width=True):
                if _aid_input.strip() and _key_input.strip():
                    _s["intervals_credentials"] = {
                        "athlete_id": _aid_input.strip(),
                        "api_key": _key_input.strip(),
                    }
                    save_state(_s)
                    st.session_state.pop("intervals_data", None)
                    st.toast("✅ Intervals.icu conectado!", icon="📊")
                    st.rerun()
                else:
                    st.error("Preencha o Athlete ID e a API Key.")

    st.markdown("---")
    st.caption("v1.5 · treino-bruno.streamlit.app")
