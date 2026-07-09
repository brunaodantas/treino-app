import streamlit as st
from datetime import date, timedelta


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


def _merge_daily(gfit_data, health_data, d):
    """
    Retorna (fc, sono, passos, calorias) para a data d.
    Prioridade: Google Fit > Apple Health.
    """
    fc = None
    sono = None
    passos = None
    calorias = None
    yesterday = str(date.fromisoformat(d) - timedelta(days=1))

    # Google Fit (prioridade)
    if gfit_data:
        for e in gfit_data.get("resting_hr", []):
            if e["data"] == d:
                fc = e["fc_repouso"]
                break
        for e in gfit_data.get("sleep", []):
            if e["data"] in (d, yesterday):
                sono = e["sono_horas"]
                break
        for e in gfit_data.get("steps", []):
            if e["data"] == d:
                passos = e["passos"]
                break
        for e in gfit_data.get("calories", []):
            if e["data"] == d:
                calorias = e["calorias"]
                break

    # Apple Health (fallback quando Google Fit não tem dado)
    if health_data:
        if fc is None:
            hr_list = health_data.get("daily_resting_hr", {}).get(d, [])
            if hr_list:
                fc = round(sum(hr_list) / len(hr_list))

        if passos is None:
            p = health_data.get("daily_steps", {}).get(d)
            if p:
                passos = int(p)

        if calorias is None:
            c = health_data.get("daily_calories", {}).get(d)
            if c:
                calorias = int(c)

    return fc, sono, passos, calorias


def render_recuperacao(state: dict, gfit_data: dict | None, health_data: dict | None = None):
    st.markdown("### 💤 Recuperação")

    today = str(date.today())

    fc_hoje, sono_ontem, passos_hoje, calorias_hoje = _merge_daily(gfit_data, health_data, today)

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

    # Histórico 7 dias
    if gfit_data or health_data:
        st.markdown("#### Últimos 7 dias")
        rows = []
        for i in range(7):
            d = str(date.today() - timedelta(days=i))
            fc, sono, passos, cals = _merge_daily(gfit_data, health_data, d)
            rows.append({
                "Data": d,
                "FC Repouso": f"{fc} bpm" if fc else "—",
                "Sono": f"{sono}h" if sono else "—",
                "Passos": f"{passos:,}".replace(",", ".") if passos else "—",
                "Calorias": f"{cals} kcal" if cals else "—",
            })

        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Conecte o Google Fit na aba ⚙️ para ver dados de recuperação.")
