import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from logic.running import (
    get_current_distance, get_progression_table,
    RUNNING_DAYS, REST_DAYS, EQUIPMENT_REMINDER, get_day_label,
)
from parsers.strava import get_runs, get_weekly_run_volume
from parsers.health import get_run_workouts


def render_corrida(state: dict, strava_df, health_data):
    distance = get_current_distance(state)

    st.markdown(f"### 🏃 Corrida — Meta desta sessão: **{distance:.1f} km**")
    st.info(EQUIPMENT_REMINDER)
    st.markdown("---")

    # Semana visual
    _render_weekly_calendar()
    st.markdown("---")

    # Progressão
    st.subheader("📈 Progressão de Volume (10%/semana)")
    _render_progression_chart(state)
    st.markdown("---")

    # Histórico de corridas
    st.subheader("📋 Últimas Corridas")
    _render_run_history(strava_df, health_data)


def _render_weekly_calendar():
    st.subheader("📅 Semana Atual")
    today = date.today()
    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())

    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        weekday = d.weekday()
        name = get_day_label(d)
        is_today = d == today

        if weekday in REST_DAYS:
            icon = "🚫"
            label = "Descanso"
            color = "#2D2D2D"
        elif weekday in RUNNING_DAYS:
            icon = "🏃"
            label = "Corrida + 🏋️"
            color = "#1A3A1A"
        else:
            icon = "🏋️"
            label = "Musculação"
            color = "#1A1A3A"

        border = "2px solid #FF6B35" if is_today else "1px solid #444"
        days.append((d, name, icon, label, color, border))

    cols = st.columns(7)
    for col, (d, name, icon, label, color, border) in zip(cols, days):
        with col:
            st.markdown(
                f"""<div style="background:{color};border:{border};border-radius:8px;
                padding:8px;text-align:center;font-size:12px">
                <b>{name}</b><br>{d.strftime('%d/%m')}<br>{icon}<br>
                <span style="font-size:10px;color:#AAA">{label}</span></div>""",
                unsafe_allow_html=True,
            )


def _render_progression_chart(state: dict):
    rows = get_progression_table(state, num_weeks=12)
    df = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Semana"].astype(str),
        y=df["Distância (km)"],
        marker_color=[
            "#FF6B35" if row["Atual"] else "#4A90D9"
            for _, row in df.iterrows()
        ],
        text=df["Distância (km)"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FAFAFA"},
        xaxis_title="Semana",
        yaxis_title="km por sessão",
        showlegend=False,
        height=300,
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df[["Semana", "Início", "Distância (km)", "Volume semanal (km)"]],
        use_container_width=True,
        hide_index=True,
    )


def _render_run_history(strava_df, health_data):
    runs_strava = []
    runs_health = []

    if strava_df is not None:
        df = get_runs(strava_df)
        if not df.empty:
            cols = ["data", "distancia_km"]
            if "fc_media" in df.columns:
                cols.append("fc_media")
            if "pace_min_km" in df.columns:
                cols.append("pace_min_km")
            runs_strava = df[cols].head(15).to_dict("records")

    if health_data:
        runs_health = [
            r for r in get_run_workouts(health_data)
            if r.get("distancia_km")
        ][:15]

    if runs_strava:
        st.markdown("**Strava**")
        display = []
        for r in runs_strava:
            row = {
                "Data": r["data"].strftime("%d/%m/%Y") if hasattr(r["data"], "strftime") else str(r["data"])[:10],
                "Distância": f"{r.get('distancia_km', 0):.2f} km",
            }
            if "fc_media" in r and r["fc_media"]:
                row["FC Média"] = f"{int(r['fc_media'])} bpm"
            if "pace_min_km" in r and r["pace_min_km"]:
                pace = r["pace_min_km"]
                mins = int(pace)
                secs = int((pace - mins) * 60)
                row["Pace"] = f"{mins}:{secs:02d} /km"
            display.append(row)
        st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)

    elif runs_health:
        st.markdown("**Apple Health**")
        display = [
            {"Data": r["data"], "Distância": f"{r['distancia_km']:.2f} km",
             "Duração": f"{r['duracao_min']:.0f} min" if r.get("duracao_min") else "—"}
            for r in runs_health
        ]
        st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)

    else:
        st.info("Faça upload do Strava CSV ou Apple Health XML na sidebar para ver seu histórico de corridas.")
