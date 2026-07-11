from __future__ import annotations
import json
import streamlit as st
from datetime import date, datetime
from pathlib import Path

from logic.schedule import (
    get_next_workout, check_72h_conflict, mark_workout_done,
    get_scheduled_workout, get_week_schedule, get_next_scheduled,
    WORKOUT_LABELS, WORKOUT_SEQUENCE, DAY_NAMES,
)
from logic.running import (
    is_running_day, is_rest_day, is_optional_run_day, get_run_info,
    get_day_label, get_current_distance, EQUIPMENT_REMINDER,
)
from logic.adaptation import (
    is_adaptation_phase, get_adaptation_week, get_workouts_in_current_week,
    get_current_phase, ADAPTATION_MESSAGE, ADAPTATION_WEEKS, WORKOUTS_PER_WEEK,
)


def _get_latest_hrv() -> float | None:
    log_path = Path(__file__).parent.parent / "data" / "health_log.json"
    if not log_path.exists():
        return None
    try:
        with open(log_path) as f:
            data = json.load(f)
        for entry in data:
            if entry.get("hrv"):
                return float(entry["hrv"])
    except Exception:
        pass
    return None


def render_dashboard(state: dict, save_fn):
    today = date.today()
    today_str = today.isoformat()
    day_name = get_day_label(today)
    weekday = today.weekday()

    st.markdown(f"### {today.strftime('%d/%m/%Y')} — {day_name}")
    st.markdown("---")

    hrv = _get_latest_hrv()

    # ── Check-in matinal ───────────────────────────────────────────────────────
    checkin_data = state.setdefault("checkin", {})
    today_checkin = checkin_data.get(today_str, {})

    with st.expander("📋 Check-in de hoje", expanded=not today_checkin):
        sono_val = today_checkin.get("sono", 7)
        apetite_val = today_checkin.get("apetite", 7)
        estresse_val = today_checkin.get("estresse", 3)

        sono = st.slider("Qualidade do sono (1-10)", 1, 10, sono_val, key="ci_sono")
        apetite = st.slider("Apetite (1-10)", 1, 10, apetite_val, key="ci_apetite")
        estresse = st.slider("Nível de estresse (1-10)", 1, 10, estresse_val, key="ci_estresse")

        if st.button("Salvar check-in", use_container_width=True):
            checkin_data[today_str] = {"sono": sono, "apetite": apetite, "estresse": estresse}
            state["checkin"] = checkin_data
            save_fn(state)
            st.success("Check-in salvo!")
            st.rerun()

        hrv_baixo = hrv is not None and hrv < 27
        if hrv_baixo and sono < 6 and apetite < 4:
            st.warning("⚠️ Múltiplos indicadores de fadiga. Considere descanso ou treino leve hoje.")

    st.markdown("---")

    # ── Agenda semanal ─────────────────────────────────────────────────────────
    week_sched = get_week_schedule(state)
    today_workout = get_scheduled_workout(state)
    next_date, next_workout = get_next_scheduled(state)

    st.markdown("**Agenda desta semana:**")
    cols = st.columns(3)
    for col, slot in zip(cols, week_sched):
        label = WORKOUT_LABELS.get(slot["treino"], slot["treino"])
        short = f"Treino {slot['treino']}" if slot["treino"] else "—"
        date_str = slot["data"].strftime("%d/%m")
        if slot["hoje"]:
            col.markdown(f"**🔵 {slot['dia']} {date_str}**  \n**{short}**")
        else:
            col.markdown(f"{slot['dia']} {date_str}  \n{short}")

    if today_workout:
        st.info(f"🏋️ **Hoje:** {WORKOUT_LABELS.get(today_workout, today_workout)}")
    elif next_date and next_workout:
        days_until = (next_date - today).days
        day_label = DAY_NAMES.get(next_date.weekday(), next_date.strftime("%A"))
        when = "amanhã" if days_until == 1 else f"em {days_until} dias"
        st.info(f"📅 **Próximo:** {WORKOUT_LABELS.get(next_workout, next_workout)} — {day_label} {next_date.strftime('%d/%m')} ({when})")

    st.markdown("---")

    # ── Informativo de corrida ─────────────────────────────────────────────────
    running = is_running_day(today)
    rest = is_rest_day(today)
    optional_run = is_optional_run_day(today)
    run_info = get_run_info(today)
    distance = get_current_distance(state)

    if rest and not today_workout:
        st.info("💤 Dia de descanso sugerido.")
    if running and run_info:
        st.info(f"🏃 {run_info['descricao']} · **{distance:.1f} km** · {EQUIPMENT_REMINDER}")
    elif optional_run and run_info:
        hrv_ok = hrv is None or hrv >= 27
        if hrv_ok:
            hrv_str = f" — HRV {hrv:.1f}" if hrv else ""
            st.info(f"🏃 {run_info['descricao']}{hrv_str}")
        else:
            st.warning(f"🚶 Corrida opcional cancelada — HRV {hrv:.1f} (< 27).")

    # Alerta HRV na sexta (treino reduzido)
    if weekday == 4 and hrv is not None and hrv < 27:
        from logic.schedule import EXERCISES_C_REDUCED
        st.warning(
            f"⚠️ HRV {hrv:.1f} (< 27). Recomendação: treino reduzido de pernas — "
            f"**Leg Press** + **Adução Quadril** apenas."
        )
        with st.expander("Ver treino reduzido"):
            for ex in EXERCISES_C_REDUCED:
                st.markdown(f"- **{ex['nome']}** — {ex['series']}×{ex['reps']} · {ex['peso_atual']} kg")

    st.markdown("---")

    # ── Periodização ──────────────────────────────────────────────────────────
    phase = get_current_phase(state)
    week = phase["semana_global"]
    phase_week = phase["semana_na_fase"]
    phase_start, phase_end = phase["semanas"]
    phase_duration = phase_end - phase_start + 1

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{phase['nome']} — Semana {phase_week} de {phase_duration}** (semana {week} no total)")
        st.progress(min(phase_week / phase_duration, 1.0))
        st.caption(phase["descricao"])
        if is_adaptation_phase(state):
            done_in_week = get_workouts_in_current_week(state)
            st.caption(f"{done_in_week}/{WORKOUTS_PER_WEEK} treinos desta semana")
            st.warning(ADAPTATION_MESSAGE)
    with col2:
        week_override = st.number_input(
            "Ajustar semana", min_value=1, max_value=20,
            value=week, step=1, key="week_override",
            help="Ajuste manual da semana de periodização"
        )
        if week_override != week:
            state["adaptation_week_override"] = week_override
            save_fn(state)
            st.rerun()

    st.markdown("---")

    # ── Botões de ação ─────────────────────────────────────────────────────────
    workout_to_mark = today_workout or get_next_workout(state)
    conflict, conflict_msg = check_72h_conflict(state, workout_to_mark)
    if conflict:
        st.warning(conflict_msg)

    col_a, col_b = st.columns(2)

    with col_a:
        if today_workout:
            label = f"✅ Concluir **{WORKOUT_LABELS.get(today_workout, today_workout)}**"
        else:
            label = f"✅ Marcar **Treino {workout_to_mark}** como Concluído"
        if st.button(label, type="primary", use_container_width=True):
            state = mark_workout_done(state, workout=workout_to_mark)
            save_fn(state)
            _, prox = get_next_scheduled(state)
            st.success(f"Treino registrado! Próximo: {prox or '—'}")
            st.rerun()

    with col_b:
        e_conflict, e_msg = check_72h_conflict(state, "E")
        if state.get("use_e_next"):
            if st.button("❌ Cancelar Treino E", use_container_width=True):
                state["use_e_next"] = False
                save_fn(state)
                st.rerun()
        else:
            if st.button("⚡ Inserir Treino E (Curinga)", disabled=e_conflict, use_container_width=True):
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
    for col, h in zip(cols, ["Data", "Treino", "Horário", ""]):
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
