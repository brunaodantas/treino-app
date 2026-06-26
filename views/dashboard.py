import streamlit as st
from datetime import date, datetime
from logic.schedule import (
    get_next_workout, check_72h_conflict, mark_workout_done,
    WORKOUT_LABELS, WORKOUT_SEQUENCE,
)
from logic.running import (
    is_running_day, is_rest_day, get_day_label, get_current_distance,
    EQUIPMENT_REMINDER,
)
from logic.adaptation import (
    is_adaptation_phase, get_adaptation_week, get_workouts_in_current_week,
    ADAPTATION_MESSAGE, ADAPTATION_WEEKS, WORKOUTS_PER_WEEK,
)


def render_dashboard(state: dict, save_fn):
    today = date.today()
    day_name = get_day_label(today)

    st.markdown(f"### {today.strftime('%d/%m/%Y')} — {day_name}")
    st.markdown("---")

    # Informativo do dia (não bloqueia acesso a treinos)
    running = is_running_day(today)
    rest = is_rest_day(today)
    distance = get_current_distance(state)
    next_wk = get_next_workout(state)

    if rest:
        st.info(f"💤 Dia de descanso sugerido — mas você decide se treina ou não.")
    elif running:
        st.info(f"🏃 Corrida sugerida hoje — **{distance:.1f} km** · {EQUIPMENT_REMINDER}")

    st.markdown("---")

    # Fase de adaptação
    week = get_adaptation_week(state)
    in_adaptation = is_adaptation_phase(state)
    col1, col2 = st.columns([2, 1])
    with col1:
        if in_adaptation:
            done_in_week = get_workouts_in_current_week(state)
            st.markdown(f"**Fase de Adaptação — Semana {week} de {ADAPTATION_WEEKS}**")
            st.progress(min(week / ADAPTATION_WEEKS, 1.0))
            st.caption(f"{done_in_week}/{WORKOUTS_PER_WEEK} treinos desta semana — faltam {WORKOUTS_PER_WEEK - done_in_week} para avançar")
            st.warning(ADAPTATION_MESSAGE)
        else:
            st.success(f"✅ Fase de Adaptação concluída")
    with col2:
        week_override = st.number_input(
            "Ajustar semana", min_value=1, max_value=20,
            value=week, step=1, key="week_override",
            help="Ajuste manual da semana de adaptação"
        )
        if week_override != week:
            state["adaptation_week_override"] = week_override
            save_fn(state)
            st.rerun()

    st.markdown("---")

    # Botões de ação
    col_a, col_b = st.columns(2)

    with col_a:
        conflict, conflict_msg = check_72h_conflict(state, next_wk)
        if conflict:
            st.warning(conflict_msg)
        label = f"✅ Marcar **Treino {next_wk}** como Concluído"
        if st.button(label, type="primary", use_container_width=True):
            state = mark_workout_done(state)
            save_fn(state)
            st.success(f"Treino {next_wk} registrado! Próximo: {WORKOUT_SEQUENCE[state['current_index'] % 4]}")
            st.rerun()

    with col_b:
        e_conflict, e_msg = check_72h_conflict(state, "E")
        e_label = "⚡ Inserir Treino E (Curinga)"
        if state.get("use_e_next"):
            if st.button("❌ Cancelar Treino E", use_container_width=True):
                state["use_e_next"] = False
                save_fn(state)
                st.rerun()
        else:
            if st.button(e_label, disabled=e_conflict, use_container_width=True):
                state["use_e_next"] = True
                save_fn(state)
                st.rerun()
            if e_conflict:
                st.caption(e_msg)

    st.markdown("---")
    _render_workout_log(state)


def _render_workout_log(state: dict):
    log = state.get("workout_log", [])
    if not log:
        return
    st.markdown("#### Histórico recente")
    cols = st.columns(4)
    headers = ["Data", "Treino", "Horário", ""]
    for col, h in zip(cols, headers):
        col.markdown(f"**{h}**")

    for entry in log[:8]:
        c1, c2, c3, c4 = st.columns(4)
        c1.write(entry.get("date", ""))
        c2.write(WORKOUT_LABELS.get(entry.get("workout", ""), entry.get("workout", "")))
        ts = entry.get("completed_at", "")
        try:
            time_str = datetime.fromisoformat(ts).strftime("%H:%M")
        except Exception:
            time_str = ts[:16]
        c3.write(time_str)
        c4.write("✅")
