import streamlit as st
from datetime import date, timedelta


def _status_color(val, ok, warn):
    """Retorna 🟢 / 🟡 / 🔴 baseado em thresholds."""
    if val is None:
        return "⚪"
    if val <= ok:
        return "🟢"
    if val <= warn:
        return "🟡"
    return "🔴"


def _hr_status(fc):
    if fc is None:
        return "⚪", "Sem dados"
    if fc <= 60:
        return "🟢", "Excelente"
    if fc <= 70:
        return "🟡", "Normal"
    return "🔴", "Elevada — descanse"


def _sleep_status(horas):
    if horas is None:
        return "⚪", "Sem dados"
    if horas >= 7.5:
        return "🟢", "Boa"
    if horas >= 6:
        return "🟡", "Razoável"
    return "🔴", "Insuficiente"


def _recovery_score(fc, sleep_h):
    score = 0
    total = 0
    if fc is not None:
        total += 1
        if fc <= 60:
            score += 1
        elif fc <= 70:
            score += 0.5
    if sleep_h is not None:
        total += 1
        if sleep_h >= 7.5:
            score += 1
        elif sleep_h >= 6:
            score += 0.5
    if total == 0:
        return None
    return score / total


def render_recuperacao(state: dict, gfit_data: dict | None):
    st.markdown("### 💤 Recuperação")

    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))

    # Extrai dados do Google Fit
    fc_hoje = None
    sono_ontem = None
    passos_hoje = None
    calorias_hoje = None

    if gfit_data:
        for entry in gfit_data.get("resting_hr", []):
            if entry["data"] == today:
                fc_hoje = entry["fc_repouso"]
                break

        for entry in gfit_data.get("sleep", []):
            if entry["data"] in (today, yesterday):
                sono_ontem = entry["sono_horas"]
                break

        for entry in gfit_data.get("steps", []):
            if entry["data"] == today:
                passos_hoje = entry["passos"]
                break

        for entry in gfit_data.get("calories", []):
            if entry["data"] == today:
                calorias_hoje = entry["calorias"]
                break

    # Score de recuperação
    score = _recovery_score(fc_hoje, sono_ontem)

    if score is None:
        rec_label = "⚪ Conecte o Google Fit para ver recuperação"
        rec_color = "#888"
    elif score >= 0.8:
        rec_label = "🟢 Bom para treinar hoje"
        rec_color = "#4CAF50"
    elif score >= 0.5:
        rec_label = "🟡 Treine com moderação"
        rec_color = "#FFC107"
    else:
        rec_label = "🔴 Priorize descanso hoje"
        rec_color = "#F44336"

    st.markdown(
        f"<div style='background:{rec_color}22;border-left:4px solid {rec_color};"
        f"padding:12px 16px;border-radius:8px;font-size:1.1rem;font-weight:600'>"
        f"{rec_label}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")

    # Cards de métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        icon, label = _hr_status(fc_hoje)
        st.metric("FC Repouso", f"{fc_hoje} bpm" if fc_hoje else "—", label)
        st.markdown(icon)

    with col2:
        icon, label = _sleep_status(sono_ontem)
        st.metric("Sono", f"{sono_ontem}h" if sono_ontem else "—", label)
        st.markdown(icon)

    with col3:
        p_str = f"{passos_hoje:,}".replace(",", ".") if passos_hoje else "—"
        st.metric("Passos hoje", p_str)

    with col4:
        c_str = f"{calorias_hoje} kcal" if calorias_hoje else "—"
        st.metric("Calorias", c_str)

    st.markdown("---")

    # Alerta de proteção articular
    st.markdown("### 🦵 Proteção Articular")
    st.warning(
        "⚠️ **JOELHO:** Sem agachamento livre pesado. "
        "Use sempre Leg Press 45°, Cadeira Extensora e Adutora — nunca agachamento livre com carga.",
        icon=None,
    )

    # Histórico 7 dias (Google Fit)
    if gfit_data:
        st.markdown("#### Últimos 7 dias")

        rhr_map = {e["data"]: e["fc_repouso"] for e in gfit_data.get("resting_hr", [])}
        sleep_map = {e["data"]: e["sono_horas"] for e in gfit_data.get("sleep", [])}
        steps_map = {e["data"]: e["passos"] for e in gfit_data.get("steps", [])}

        rows = []
        for i in range(7):
            d = str(date.today() - timedelta(days=i))
            rows.append({
                "Data": d,
                "FC Repouso": f"{rhr_map[d]} bpm" if d in rhr_map else "—",
                "Sono": f"{sleep_map[d]}h" if d in sleep_map else "—",
                "Passos": f"{steps_map[d]:,}".replace(",", ".") if d in steps_map else "—",
            })

        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Conecte o Google Fit na aba ⚙️ para ver dados de recuperação.")
