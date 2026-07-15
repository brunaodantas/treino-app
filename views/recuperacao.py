import streamlit as st
from datetime import date, timedelta
from utils import today_br

_SURFACE = "rgba(0,0,0,0)"
_GRID    = "rgba(255,255,255,0.07)"
_INK     = "#9CA3AF"


def _chart_layout(title, show_legend=False):
    leg = dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0,
               font=dict(size=11, color=_INK), bgcolor="rgba(0,0,0,0)") if show_legend else {}
    return dict(
        title=dict(text=title, font=dict(size=12, color=_INK), x=0, xanchor="left"),
        paper_bgcolor=_SURFACE, plot_bgcolor=_SURFACE,
        margin=dict(l=0, r=4, t=32, b=0), height=190,
        showlegend=show_legend, legend=leg,
        xaxis=dict(showgrid=False, zeroline=False,
                   tickfont=dict(size=9, color=_INK), tickangle=-30, fixedrange=True),
        yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=False,
                   tickfont=dict(size=9, color=_INK), fixedrange=True),
        hoverlabel=dict(bgcolor="#1E2130", font_size=12, font_color="#FAFAFA",
                        bordercolor="rgba(255,255,255,0.1)"),
    )


def _render_trends(gfit_data, health_data, intervals_data):
    from datetime import datetime, timezone, timedelta as _td
    import plotly.graph_objects as go

    _br = datetime.now(timezone(_td(hours=-3))).date()
    dates, fcr_v, ctl_v, atl_v = [], [], [], []
    for i in range(13, -1, -1):
        d = str(_br - _td(days=i))
        fc_d, _, _, _, _, ctl_d, atl_d, _ = _merge_daily(gfit_data, health_data, intervals_data, d)
        dates.append(d[-5:])   # MM-DD
        fcr_v.append(fc_d)
        ctl_v.append(round(ctl_d, 1) if ctl_d is not None else None)
        atl_v.append(round(atl_d, 1) if atl_d is not None else None)

    _cfg = {"displayModeBar": False, "scrollZoom": False}

    # ── FCR 14 dias ──────────────────────────────────────────────────────────
    if any(v is not None for v in fcr_v):
        fig = go.Figure()
        fig.add_hrect(y0=0,  y1=65,  fillcolor="rgba(76,175,80,0.06)",  line_width=0)
        fig.add_hrect(y0=72, y1=130, fillcolor="rgba(244,67,54,0.06)",  line_width=0)
        fig.add_hline(y=65, line_dash="dot", line_color="rgba(76,175,80,0.4)",  line_width=1)
        fig.add_hline(y=72, line_dash="dot", line_color="rgba(244,67,54,0.4)",  line_width=1)
        fig.add_trace(go.Scatter(
            x=dates, y=fcr_v, mode="lines+markers", name="FCR",
            line=dict(color="#FF6B35", width=2),
            marker=dict(size=5, color="#FF6B35", line=dict(color="#0E1117", width=1.5)),
            connectgaps=True,
            hovertemplate="<b>%{x}</b>  %{y} bpm<extra></extra>",
        ))
        fig.update_layout(**_chart_layout("FC Repouso — 14 dias"))
        st.plotly_chart(fig, use_container_width=True, config=_cfg)

    # ── CTL / ATL 14 dias ────────────────────────────────────────────────────
    if any(v is not None for v in ctl_v):
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=dates, y=ctl_v, mode="lines", name="CTL — Forma",
            line=dict(color="#4A90D9", width=2),
            fill="tozeroy", fillcolor="rgba(74,144,217,0.10)",
            connectgaps=True,
            hovertemplate="<b>%{x}</b>  CTL %{y:.1f}<extra></extra>",
        ))
        fig2.add_trace(go.Scatter(
            x=dates, y=atl_v, mode="lines", name="ATL — Fadiga",
            line=dict(color="#E8A838", width=2),
            connectgaps=True,
            hovertemplate="<b>%{x}</b>  ATL %{y:.1f}<extra></extra>",
        ))
        fig2.update_layout(**_chart_layout("Carga — 14 dias", show_legend=True))
        st.plotly_chart(fig2, use_container_width=True, config=_cfg)


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
    col_title, col_ref = st.columns([5, 1])
    with col_title:
        st.markdown("### 💤 Recuperação")
    with col_ref:
        if st.button("🔄", help="Recarregar", key="refresh_rec"):
            import streamlit.components.v1 as _cv1
            _cv1.html("<script>window.parent.location.reload();</script>", height=0)

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

    # Gráficos de tendência
    if gfit_data or health_data or intervals_data:
        _render_trends(gfit_data, health_data, intervals_data)
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
