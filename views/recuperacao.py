import streamlit as st
from datetime import date, timedelta
from utils import today_br


def _hr_status(fc):
    if fc is None:
        return "⚪", "Sem dados"
    if fc <= 60:
        return "🟢", "Excelente"
    if fc <= 70:
        return "🟡", "Normal"
    return "🔴", "Elevada"


def _sleep_status(horas):
    if horas is None:
        return "⚪", "Sem dados"
    if horas >= 7.5:
        return "🟢", "Boa"
    if horas >= 6:
        return "🟡", "Razoável"
    return "🔴", "Insuficiente"


def _hrv_status(hrv):
    if hrv is None:
        return "⚪", "Sem dados"
    if hrv >= 31:
        return "🟢", "Ótimo"
    if hrv >= 27:
        return "🟡", "Normal"
    return "🔴", "Baixo"


def _recovery_score(fc, sleep_h, hrv=None):
    score = 0
    total = 0
    if hrv is not None:
        total += 2  # HRV tem peso maior
        if hrv >= 31:
            score += 2
        elif hrv >= 27:
            score += 1
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


def _get_intervals_day(intervals_data, d):
    if not intervals_data:
        return {}
    for entry in intervals_data:
        if entry.get("data") == d:
            return entry
    return {}


def _merge_daily(gfit_data, health_data, intervals_data, d):
    """
    Retorna (fc, sono, passos, calorias, hrv, ctl, atl, tsb) para a data d.
    Prioridade: Intervals > Google Fit > Apple Health.
    """
    fc = sono = passos = calorias = hrv = ctl = atl = tsb = None

    # Intervals (prioridade máxima)
    iv = _get_intervals_day(intervals_data, d)
    if iv:
        fc = iv.get("fc_repouso")
        hrv = iv.get("hrv")
        ctl = iv.get("ctl")
        atl = iv.get("atl")
        tsb = iv.get("tsb")
        if iv.get("sono_horas"):
            sono = iv["sono_horas"]

    yesterday = str(date.fromisoformat(d) - timedelta(days=1))

    # Google Fit (fallback)
    if gfit_data:
        if fc is None:
            for e in gfit_data.get("resting_hr", []):
                if e["data"] == d:
                    fc = e["fc_repouso"]
                    break
        if sono is None:
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

    # Apple Health (último fallback)
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

    return fc, sono, passos, calorias, hrv, ctl, atl, tsb


def render_recuperacao(state: dict, gfit_data, health_data=None, intervals_data=None):
    st.markdown("### 💤 Recuperação")

    today = today_br()
    fc, sono, passos, calorias, hrv, ctl, atl, tsb = _merge_daily(
        gfit_data, health_data, intervals_data, today
    )

    # Score de recuperação
    score = _recovery_score(fc, sono, hrv)

    if score is None:
        rec_label = "⚪ Conecte o Google Fit ou Intervals para ver recuperação"
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

    # Métricas principais
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        icon, label = _hrv_status(hrv)
        st.metric("HRV", f"{hrv:.0f}" if hrv else "—", label)
        st.markdown(icon)

    with col2:
        icon, label = _hr_status(fc)
        st.metric("FC Repouso", f"{fc} bpm" if fc else "—", label)
        st.markdown(icon)

    with col3:
        icon, label = _sleep_status(sono)
        st.metric("Sono", f"{sono}h" if sono else "—", label)
        st.markdown(icon)

    with col4:
        p_str = f"{passos:,}".replace(",", ".") if passos else "—"
        st.metric("Passos", p_str)

    with col5:
        st.metric("Calorias", f"{calorias} kcal" if calorias else "—")

    # Carga de treino (Intervals)
    if ctl is not None or atl is not None:
        st.markdown("---")
        st.markdown("#### 📊 Carga de Treino")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Forma (CTL)", f"{ctl:.1f}" if ctl else "—",
                      help="Fitness acumulado nos últimos 42 dias")
        with c2:
            st.metric("Fadiga (ATL)", f"{atl:.1f}" if atl else "—",
                      help="Fadiga dos últimos 7 dias")
        with c3:
            tsb_val = round(tsb, 1) if tsb is not None else None
            tsb_color = "normal" if tsb_val is None else ("inverse" if tsb_val < -20 else "normal")
            st.metric("Frescor (TSB)", f"{tsb_val:+.1f}" if tsb_val is not None else "—",
                      delta_color=tsb_color,
                      help="TSB > 0: descansado | TSB < -10: fadigado | TSB < -20: sobrecarga")

    st.markdown("---")

    # Histórico 7 dias
    if gfit_data or health_data or intervals_data:
        st.markdown("#### Últimos 7 dias")
        rows = []
        from datetime import datetime, timezone, timedelta as _td
        _br = datetime.now(timezone(_td(hours=-3))).date()
        for i in range(7):
            d = str(_br - timedelta(days=i))
            fc_d, sono_d, passos_d, cals_d, hrv_d, *_ = _merge_daily(
                gfit_data, health_data, intervals_data, d
            )
            rows.append({
                "Data": d,
                "HRV": f"{hrv_d:.0f}" if hrv_d else "—",
                "FC Repouso": f"{fc_d} bpm" if fc_d else "—",
                "Sono": f"{sono_d}h" if sono_d else "—",
                "Passos": f"{passos_d:,}".replace(",", ".") if passos_d else "—",
                "Calorias": f"{cals_d} kcal" if cals_d else "—",
            })

        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Conecte o Google Fit ou configure o Intervals.icu para ver dados de recuperação.")
