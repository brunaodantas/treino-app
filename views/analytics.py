import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from parsers.strava import get_runs, get_weekly_run_volume
from parsers.health import get_daily_steps_df, get_daily_calories_df, get_run_workouts


def render_analytics(strava_df, health_data):
    has_strava = strava_df is not None
    has_health = bool(health_data)

    if not has_strava and not has_health:
        st.info("📂 Faça upload do **Strava CSV** e/ou **Apple Health XML** na sidebar para ver os gráficos.")
        return

    # --- Volume de corrida ---
    st.subheader("🏃 Volume Semanal de Corrida")
    _render_run_volume(strava_df, health_data)
    st.markdown("---")

    if has_strava:
        # --- Distribuição de atividades ---
        st.subheader("📊 Distribuição de Atividades (Strava)")
        _render_activity_distribution(strava_df)
        st.markdown("---")

    if has_health:
        # --- Passos diários ---
        st.subheader("👣 Passos Diários (Apple Health — últimos 90 dias)")
        _render_daily_steps(health_data)
        st.markdown("---")

        # --- Calorias ativas ---
        st.subheader("🔥 Calorias Ativas Diárias (Apple Health — últimos 90 dias)")
        _render_daily_calories(health_data)


def _render_run_volume(strava_df, health_data):
    frames = []

    if strava_df is not None:
        weekly = get_weekly_run_volume(strava_df)
        if not weekly.empty:
            weekly["Fonte"] = "Strava"
            frames.append(weekly)

    if health_data:
        runs = get_run_workouts(health_data)
        if runs:
            df_h = pd.DataFrame(runs).dropna(subset=["data", "distancia_km"])
            df_h["data"] = pd.to_datetime(df_h["data"])
            df_h["Semana"] = df_h["data"].dt.to_period("W").apply(lambda p: p.start_time)
            weekly_h = df_h.groupby("Semana")["distancia_km"].sum().reset_index()
            weekly_h.columns = ["Semana", "Distância (km)"]
            weekly_h["Fonte"] = "Apple Health"
            frames.append(weekly_h)

    if not frames:
        st.info("Nenhum dado de corrida disponível.")
        return

    df = pd.concat(frames).sort_values("Semana")
    # Keep last 26 weeks
    if not df.empty:
        cutoff = df["Semana"].max() - pd.Timedelta(weeks=26)
        df = df[df["Semana"] >= cutoff]

    fig = px.bar(
        df, x="Semana", y="Distância (km)", color="Fonte",
        barmode="overlay",
        color_discrete_map={"Strava": "#FF6B35", "Apple Health": "#4A90D9"},
    )
    _apply_dark_layout(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_activity_distribution(strava_df):
    if "tipo" not in strava_df.columns:
        st.info("Coluna de tipo não encontrada.")
        return
    counts = strava_df["tipo"].value_counts().reset_index()
    counts.columns = ["Tipo", "Quantidade"]
    fig = px.pie(counts, names="Tipo", values="Quantidade", hole=0.4)
    _apply_dark_layout(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_daily_steps(health_data):
    df = get_daily_steps_df(health_data)
    if df.empty:
        st.info("Nenhum dado de passos disponível.")
        return
    fig = px.bar(df, x="Data", y="Passos", color_discrete_sequence=["#4A90D9"])
    fig.add_hline(y=8000, line_dash="dash", line_color="#FF6B35", annotation_text="Meta: 8.000 passos")
    _apply_dark_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    avg = int(df["Passos"].mean())
    st.caption(f"Média diária: **{avg:,}** passos")


def _render_daily_calories(health_data):
    df = get_daily_calories_df(health_data)
    if df.empty:
        st.info("Nenhum dado de calorias disponível.")
        return
    fig = px.area(df, x="Data", y="Calorias", color_discrete_sequence=["#FF6B35"])
    _apply_dark_layout(fig)
    st.plotly_chart(fig, use_container_width=True)
    avg = int(df["Calorias"].mean())
    st.caption(f"Média diária: **{avg:,}** kcal ativas")


def _apply_dark_layout(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FAFAFA"},
        height=350,
        margin=dict(t=20, b=20),
    )
