import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import date
from utils import today_br

DATA_PATH = Path(__file__).parent.parent / "data" / "health_log.json"
HRV_BASELINE = 29.0
HRV_ALERT = 27.0


def _load_log() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    with open(DATA_PATH) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data")
    return df


def _chart_hrv(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=HRV_ALERT, fillcolor="red", opacity=0.07, line_width=0)
    fig.add_hrect(y0=HRV_ALERT, y1=HRV_BASELINE, fillcolor="orange", opacity=0.07, line_width=0)
    fig.add_hrect(y0=HRV_BASELINE, y1=50, fillcolor="green", opacity=0.07, line_width=0)
    fig.add_hline(y=HRV_BASELINE, line_dash="dot", line_color="#aaa", line_width=1,
                  annotation_text="baseline 29", annotation_position="right")
    fig.add_trace(go.Scatter(
        x=df["data"], y=df["hrv"],
        mode="lines+markers", name="HRV",
        line=dict(color="#4A90D9", width=2),
        marker=dict(size=5),
        connectgaps=False,
    ))
    fig.update_layout(
        title="HRV diário", height=260,
        margin=dict(l=0, r=0, t=36, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="ms", gridcolor="#333"),
        xaxis=dict(gridcolor="#333"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


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


def render_saude():
    st.markdown("### 📈 Saúde & Evolução")

    df = _load_log()
    if df.empty:
        st.info("Nenhum dado de saúde registrado ainda. A rotina diária das 9h vai preencher automaticamente.")
        return

    # Resumo hoje
    hoje = df[df["data"] == pd.Timestamp(today_br())]
    if not hoje.empty:
        r = hoje.iloc[0]
        hrv = r.get("hrv")
        tsb = r.get("tsb")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            icon = "🟢" if hrv and hrv >= HRV_BASELINE else "🟡" if hrv and hrv >= HRV_ALERT else "🔴"
            st.metric("HRV hoje", f"{hrv:.1f}" if hrv else "—", f"{icon}")
        with col2:
            fc = r.get("fc_repouso")
            st.metric("FC Repouso", f"{fc} bpm" if fc else "—")
        with col3:
            sono = r.get("sono_horas")
            st.metric("Sono", f"{sono}h" if sono else "—")
        with col4:
            st.metric("TSB", f"{tsb:+.1f}" if tsb else "—", help="Frescor: >0 descansado, <-15 sobrecarregado")
        st.markdown("---")

    # Filtro de período
    periodo = st.radio("Período", ["2 semanas", "1 mês", "Tudo"], horizontal=True, index=0)
    if periodo == "2 semanas":
        df = df[df["data"] >= pd.Timestamp(today_br()) - pd.Timedelta(days=14)]
    elif periodo == "1 mês":
        df = df[df["data"] >= pd.Timestamp(today_br()) - pd.Timedelta(days=30)]

    df_hrv = df[df["hrv"].notna()]
    if not df_hrv.empty:
        _chart_hrv(df_hrv)

    _chart_carga(df[df["ctl"].notna()])
    _chart_sono(df[df["sono_horas"].notna()])
    _chart_peso(df)

    # Tabela
    with st.expander("Ver dados completos"):
        st.dataframe(
            df[["data", "hrv", "fc_repouso", "sono_horas", "peso_kg", "ctl", "atl", "tsb"]]
            .rename(columns={"data": "Data", "hrv": "HRV", "fc_repouso": "FC Rep.",
                             "sono_horas": "Sono (h)", "peso_kg": "Peso (kg)",
                             "ctl": "CTL", "atl": "ATL", "tsb": "TSB"})
            .sort_values("Data", ascending=False)
            .reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )
