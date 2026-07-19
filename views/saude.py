import json
import streamlit as st
import streamlit.components.v1 as _components
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import date
from utils import today_br
from views.recuperacao import (
    _merge_daily, _render_trends, _recovery_score, _hr_status, _sleep_status,
)

DATA_PATH = Path(__file__).parent.parent / "data" / "health_log.json"


def _load_log() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    with open(DATA_PATH) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data")
    return df


def _latest_data_date() -> str | None:
    """Data (YYYY-MM-DD) do registro mais recente com FC ou carga no health_log."""
    df = _load_log()
    if df.empty:
        return None
    mask = df["fc_repouso"].notna() | df["ctl"].notna()
    valid = df[mask]
    if valid.empty:
        return None
    return valid["data"].max().strftime("%Y-%m-%d")


# ── Cartão de estado compacto ───────────────────────────────────────────────────
_ICON_COLOR = {"🟢": "#4CAF50", "🟡": "#FFC107", "🔴": "#F44336", "⚪": "#6B7280"}


def _tsb_status(tsb):
    if tsb is None:
        return "#6B7280", "—"
    if tsb > -10:
        return "#4CAF50", "Descansado"
    if tsb > -20:
        return "#FFC107", "Moderado"
    return "#F44336", "Fadigado"


def _tile(label, value, unit="", status_color=None, status_text="", sub=""):
    """Um bloco compacto: rótulo pequeno, valor, e um sinal de status (ou sublegenda)."""
    unit_html = (f"<span style='font-size:.8rem;color:#9CA3AF;font-weight:500'> {unit}</span>"
                 if unit else "")
    if status_color and status_text:
        dot = (f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
               f"background:{status_color};margin-right:5px;vertical-align:middle'></span>")
        foot = (f"<div style='font-size:.72rem;color:{status_color};margin-top:3px'>"
                f"{dot}{status_text}</div>")
    elif sub:
        foot = f"<div style='font-size:.72rem;color:#9CA3AF;margin-top:3px'>{sub}</div>"
    else:
        foot = "<div style='height:3px'></div>"
    return (
        "<div style='flex:1 1 96px;min-width:96px;background:#161A23;"
        "border:1px solid #262B36;border-radius:12px;padding:10px 12px'>"
        f"<div style='color:#9CA3AF;font-size:.68rem;letter-spacing:.4px;"
        f"text-transform:uppercase;margin-bottom:3px'>{label}</div>"
        f"<div style='color:#FAFAFA;font-size:1.45rem;font-weight:700;line-height:1.05'>"
        f"{value}{unit_html}</div>"
        f"{foot}</div>"
    )


def _render_state_card(ref_date, today, fc, sono, tsb, ctl, atl, passos, calorias):
    # Cabeçalho honesto: "Hoje" só quando o dado é de hoje.
    if ref_date == today:
        st.markdown("#### Estado de hoje")
    else:
        from datetime import date as _date
        _fmt = _date.fromisoformat(ref_date).strftime("%d/%m")
        st.markdown(f"#### Estado — último registro ({_fmt})")
        st.caption("Ainda sem dados de hoje. A rotina das 9h preenche automaticamente.")

    tiles = []
    # Primárias (com sinal de status)
    fc_icon, fc_lbl = _hr_status(fc)
    tiles.append(_tile("FC Repouso", fc if fc else "—", "bpm" if fc else "",
                       _ICON_COLOR.get(fc_icon), fc_lbl))
    sono_icon, sono_lbl = _sleep_status(sono)
    tiles.append(_tile("Sono", f"{sono}" if sono else "—", "h" if sono else "",
                       _ICON_COLOR.get(sono_icon), sono_lbl))
    tsb_c, tsb_lbl = _tsb_status(tsb)
    tiles.append(_tile("Frescor (TSB)", f"{tsb:+.1f}" if tsb is not None else "—", "",
                       tsb_c, tsb_lbl))
    # Carga (neutras)
    if ctl is not None:
        tiles.append(_tile("Forma", f"{ctl:.1f}", "", sub="CTL · 42 dias"))
    if atl is not None:
        tiles.append(_tile("Fadiga", f"{atl:.1f}", "", sub="ATL · 7 dias"))
    # Atividade (só quando há dado, pra não deixar buraco)
    if passos:
        tiles.append(_tile("Passos", f"{passos:,}".replace(",", "."), "", sub="hoje"))
    if calorias:
        tiles.append(_tile("Calorias", f"{calorias}", "kcal", sub="hoje"))

    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;gap:8px'>" + "".join(tiles) + "</div>",
        unsafe_allow_html=True,
    )


def _chart_carga(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["data"], y=df["ctl"], name="CTL (forma)",
                             line=dict(color="#4CAF50", width=2), fill=None))
    fig.add_trace(go.Scatter(x=df["data"], y=df["atl"], name="ATL (fadiga)",
                             line=dict(color="#F44336", width=2)))
    fig.add_trace(go.Bar(x=df["data"], y=df["tsb"], name="TSB (frescor)",
                         marker_color=df["tsb"].apply(
                             lambda v: "#4CAF50" if v and v > 0 else "#F44336" if v and v < -15 else "#FFC107"
                         )))
    fig.update_layout(
        title="Carga de treino (CTL / ATL / TSB)", height=280,
        margin=dict(l=0, r=0, t=36, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#333"),
        xaxis=dict(gridcolor="#333"),
        legend=dict(orientation="h", y=-0.2),
        barmode="overlay",
    )
    st.plotly_chart(fig, use_container_width=True)


def _chart_sono(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_hrect(y0=7.5, y1=12, fillcolor="green", opacity=0.07, line_width=0)
    fig.add_hrect(y0=6, y1=7.5, fillcolor="orange", opacity=0.07, line_width=0)
    fig.add_hrect(y0=0, y1=6, fillcolor="red", opacity=0.07, line_width=0)
    fig.add_trace(go.Bar(
        x=df["data"], y=df["sono_horas"], name="Sono",
        marker_color=df["sono_horas"].apply(
            lambda v: "#4CAF50" if v and v >= 7.5 else "#FFC107" if v and v >= 6 else "#F44336"
        ),
    ))
    fig.update_layout(
        title="Sono (horas)", height=220,
        margin=dict(l=0, r=0, t=36, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#333"),
        xaxis=dict(gridcolor="#333"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _chart_peso(df: pd.DataFrame):
    df_p = df[df["peso_kg"].notna()]
    if df_p.empty:
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_p["data"], y=df_p["peso_kg"],
        mode="lines+markers", name="Peso",
        line=dict(color="#9C27B0", width=2),
        marker=dict(size=6),
    ))
    fig.update_layout(
        title="Peso (kg)", height=200,
        margin=dict(l=0, r=0, t=36, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#333"),
        xaxis=dict(gridcolor="#333"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_checkin(state: dict, save_fn):
    """Check-in matinal (sono/apetite/estresse) — migrado do antigo Dashboard."""
    if state is None:
        return
    today_str = today_br()
    checkin_data = state.setdefault("checkin", {})
    today_checkin = checkin_data.get(today_str, {})

    with st.expander("📋 Check-in de hoje", expanded=not today_checkin):
        sono = st.slider("Qualidade do sono (1-10)", 1, 10,
                         today_checkin.get("sono", 7), key="ci_sono")
        apetite = st.slider("Apetite (1-10)", 1, 10,
                            today_checkin.get("apetite", 7), key="ci_apetite")
        estresse = st.slider("Nível de estresse (1-10)", 1, 10,
                             today_checkin.get("estresse", 3), key="ci_estresse")

        if st.button("Salvar check-in", use_container_width=True):
            checkin_data[today_str] = {"sono": sono, "apetite": apetite, "estresse": estresse}
            state["checkin"] = checkin_data
            if save_fn:
                save_fn(state)
            st.success("Check-in salvo!")
            st.rerun()

        if sono < 6 and apetite < 4:
            st.warning("⚠️ Múltiplos indicadores de fadiga. Considere descanso ou treino leve hoje.")


def render_saude(state: dict = None, save_fn=None,
                 gfit_data=None, health_data=None, intervals_data=None):
    col_title, col_ref = st.columns([5, 1])
    with col_title:
        st.markdown("### 📈 Saúde & Recuperação")
    with col_ref:
        if st.button("🔄", help="Recarregar", key="refresh_saude"):
            _components.html("<script>window.parent.location.reload();</script>", height=0)

    today = today_br()
    ref_date = today
    fc, sono, passos, calorias, ctl, atl, tsb = _merge_daily(
        gfit_data, health_data, intervals_data, today
    )
    # Se ainda não há dado de hoje (rotina das 9h ainda não rodou), usa o
    # registro mais recente para a aba não ficar vazia de madrugada.
    if fc is None and sono is None and ctl is None:
        _recent = _latest_data_date()
        if _recent and _recent != today:
            ref_date = _recent
            fc, sono, passos, calorias, ctl, atl, tsb = _merge_daily(
                gfit_data, health_data, intervals_data, _recent
            )

    # ── Recomendação de recuperação ─────────────────────────────────────────────
    from datetime import date as _date
    quando = "hoje" if ref_date == today else f"(base {_date.fromisoformat(ref_date).strftime('%d/%m')})"
    score = _recovery_score(fc, sono)
    if score is None:
        rec_label = "⚪ Conecte o Google Fit ou o Intervals para avaliar a recuperação"
        rec_color = "#888"
    elif score >= 0.8:
        rec_label, rec_color = f"🟢 Bom para treinar {quando}", "#4CAF50"
    elif score >= 0.5:
        rec_label, rec_color = f"🟡 Treine com moderação {quando}", "#FFC107"
    else:
        rec_color = "#F44336"
        _sono_baixo = sono is not None and sono < 6.5
        _fcr_alta = fc is not None and fc >= 80  # alerta só a partir de 80
        if _sono_baixo and not _fcr_alta:
            rec_label = "🛌 Durma mais esta noite"
        elif _fcr_alta and not _sono_baixo:
            rec_label = f"🔴 Pegue leve {quando} — FC de repouso elevada"
        elif _fcr_alta and _sono_baixo:
            rec_label = f"🛌 Durma mais — e pegue leve {quando}"
        else:
            rec_label = f"🔴 Pegue leve {quando}"

    st.markdown(
        f"<div style='background:{rec_color}18;border:1.5px solid {rec_color}50;"
        f"padding:12px 16px;border-radius:10px;font-size:1.05rem;font-weight:600'>"
        f"{rec_label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    # ── Check-in de hoje ────────────────────────────────────────────────────────
    _render_checkin(state, save_fn)

    # ── Cartão de estado (hoje ou último registro) ──────────────────────────────
    _render_state_card(ref_date, today, fc, sono, tsb, ctl, atl, passos, calorias)

    # ── Tendências 14 dias ──────────────────────────────────────────────────────
    if gfit_data or health_data or intervals_data:
        st.markdown("---")
        _render_trends(gfit_data, health_data, intervals_data)

    # ── Evolução histórica (health_log.json) ────────────────────────────────────
    df = _load_log()
    if df.empty:
        st.markdown("---")
        st.info("Nenhum dado de saúde registrado ainda. A rotina diária das 9h preenche automaticamente.")
        return

    st.markdown("---")
    with st.expander("📉 Evolução (histórico completo)"):
        periodo = st.radio("Período", ["2 semanas", "1 mês", "Tudo"],
                           horizontal=True, index=0, key="saude_periodo")
        dff = df
        if periodo == "2 semanas":
            dff = df[df["data"] >= pd.Timestamp(today_br()) - pd.Timedelta(days=14)]
        elif periodo == "1 mês":
            dff = df[df["data"] >= pd.Timestamp(today_br()) - pd.Timedelta(days=30)]

        _chart_carga(dff[dff["ctl"].notna()])
        _chart_sono(dff[dff["sono_horas"].notna()])
        _chart_peso(dff)

        st.dataframe(
            dff[["data", "fc_repouso", "sono_horas", "peso_kg", "ctl", "atl", "tsb"]]
            .rename(columns={"data": "Data", "fc_repouso": "FC Rep.",
                             "sono_horas": "Sono (h)", "peso_kg": "Peso (kg)",
                             "ctl": "CTL", "atl": "ATL", "tsb": "TSB"})
            .sort_values("Data", ascending=False)
            .reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )
