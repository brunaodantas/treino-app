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


def _load_health_log() -> list:
    log_path = Path(__file__).parent.parent / "data" / "health_log.json"
    if not log_path.exists():
        return []
    try:
        with open(log_path) as f:
            return json.load(f)
    except Exception:
        return []


def _get_latest_hrv() -> float | None:
    data = _load_health_log()
    for entry in data:
        if entry.get("hrv"):
            return float(entry["hrv"])
    return None


def _avg(entries: list, key: str) -> float | None:
    vals = [e[key] for e in entries if e.get(key) is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def _health_summary(log: list) -> dict:
    """Retorna today + médias 3d/7d/15d para HRV, FC, sono, TSB, CTL, ATL."""
    today_str = date.today().isoformat()
    today_entry = next((e for e in log if e.get("data") == today_str), None)

    past = [e for e in log if e.get("data") < today_str]

    def stats(n):
        subset = past[:n]
        return {
            "hrv": _avg(subset, "hrv"),
            "fc": _avg(subset, "fc_repouso"),
            "sono": _avg(subset, "sono_horas"),
            "tsb": _avg(subset, "tsb"),
        }

    return {
        "today": today_entry or {},
        "d3": stats(3),
        "d7": stats(7),
        "d15": stats(15),
    }


def _delta_str(current, ref) -> str | None:
    if current is None or ref is None:
        return None
    diff = current - ref
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.1f}"


def _render_estado_atual(log: list):
    if not log:
        return

    s = _health_summary(log)
    today = s["today"]

    hrv_hoje = today.get("hrv")
    fc_hoje = today.get("fc_repouso")
    sono_hoje = today.get("sono_horas")
    tsb_hoje = today.get("tsb")
    ctl_hoje = today.get("ctl")
    atl_hoje = today.get("atl")

    # Ícone de estado geral
    if hrv_hoje is not None:
        if hrv_hoje >= 31:
            estado_icon, estado_txt, estado_cor = "🟢", "Recuperado", "#4CAF50"
        elif hrv_hoje >= 27:
            estado_icon, estado_txt, estado_cor = "🟡", "Moderado", "#FFC107"
        else:
            estado_icon, estado_txt, estado_cor = "🔴", "Fadigado", "#F44336"
    elif tsb_hoje is not None:
        if tsb_hoje > -10:
            estado_icon, estado_txt, estado_cor = "🟢", "Recuperado", "#4CAF50"
        elif tsb_hoje > -20:
            estado_icon, estado_txt, estado_cor = "🟡", "Moderado", "#FFC107"
        else:
            estado_icon, estado_txt, estado_cor = "🔴", "Fadigado", "#F44336"
    else:
        return  # sem dados suficientes

    st.markdown(
        f"<div style='background:{estado_cor}22;border-left:4px solid {estado_cor};"
        f"padding:10px 14px;border-radius:8px;font-size:1rem;font-weight:600;margin-bottom:8px'>"
        f"{estado_icon} Estado hoje: {estado_txt}</div>",
        unsafe_allow_html=True,
    )

    # Métricas com delta vs 7d
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        delta = _delta_str(hrv_hoje, s["d7"]["hrv"])
        st.metric("HRV", f"{hrv_hoje:.0f}" if hrv_hoje else "—", delta)
    with c2:
        delta = _delta_str(fc_hoje, s["d7"]["fc"])
        st.metric("FC rep.", f"{fc_hoje}" if fc_hoje else "—", delta,
                  delta_color="inverse")
    with c3:
        delta = _delta_str(sono_hoje, s["d7"]["sono"])
        st.metric("Sono", f"{sono_hoje:.1f}h" if sono_hoje else "—", delta)
    with c4:
        delta = _delta_str(tsb_hoje, s["d7"]["tsb"])
        st.metric("TSB", f"{tsb_hoje:+.1f}" if tsb_hoje is not None else "—", delta,
                  delta_color="inverse")

    # Tabela 3d/7d/15d
    with st.expander("📊 Comparativo 3d / 7d / 15d"):
        rows = []
        for label, key_d, key_fc, key_s, key_t in [
            ("3 dias", "d3", "d3", "d3", "d3"),
            ("7 dias", "d7", "d7", "d7", "d7"),
            ("15 dias", "d15", "d15", "d15", "d15"),
        ]:
            d = s[key_d]
            rows.append({
                "Período": f"Últimos {label}",
                "HRV": f"{d['hrv']:.1f}" if d["hrv"] else "—",
                "FC rep.": f"{d['fc']}" if d["fc"] else "—",
                "Sono": f"{d['sono']:.1f}h" if d["sono"] else "—",
                "TSB": f"{d['tsb']:+.1f}" if d["tsb"] is not None else "—",
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_dashboard(state: dict, save_fn):
    today = date.today()
    today_str = today.isoformat()
    day_name = get_day_label(today)
    weekday = today.weekday()

    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.markdown(f"### {today.strftime('%d/%m/%Y')} — {day_name}")
    with col_refresh:
        if st.button("🔄", help="Recarregar app"):
            import streamlit.components.v1 as _cv1
            _cv1.html("<script>window.parent.location.reload();</script>", height=0)
    st.markdown("---")

    _log = _load_health_log()
    hrv = _get_latest_hrv()

    # ── Estado de recuperação ──────────────────────────────────────────────────
    _render_estado_atual(_log)

    st.markdown("---")

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

    # Ajuste de ciclo: qual treino começa na próxima Terça
    from datetime import timedelta as _td
    _monday = today - _td(days=today.weekday())
    _this_tue = _monday + _td(days=1)
    # Se a Terça desta semana já passou, aponta para a próxima
    _ref_tue = _this_tue if _this_tue >= today else _monday + _td(days=8)
    _current_tue_wk = get_scheduled_workout(state, _ref_tue) or "A"
    _opcoes = ["A", "B", "C", "D"]
    _idx_atual = _opcoes.index(_current_tue_wk) if _current_tue_wk in _opcoes else 0
    _label_tue = _ref_tue.strftime("%d/%m")
    _escolha = st.selectbox(f"Terça {_label_tue} começa com:", _opcoes, index=_idx_atual, key="ciclo_sel")
    if _escolha != _current_tue_wk:
        from logic.schedule import get_cycle_week as _gcw, _schedule_origin as _so
        _raw = max(0, (_ref_tue - _so(state)).days // 7)
        _novo_offset = (_opcoes.index(_escolha) - _raw) % 4
        state["schedule_week_offset"] = _novo_offset
        save_fn(state)
        st.rerun()

    if today_workout:
        st.info(f"🏋️ **Hoje:** {WORKOUT_LABELS.get(today_workout, today_workout)}")

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
        st.info(f"🏃 {run_info['descricao']} · **{distance:.1f} km**")
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
