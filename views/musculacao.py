import streamlit as st
from datetime import datetime
from logic.schedule import EXERCISES, WORKOUT_LABELS, MUSCLE_GROUPS, check_72h_conflict

MUSCLE_EMOJI = {
    "peito": "🫁", "ombro_lat": "💪", "triceps": "💪",
    "costas": "🔙", "ombro_post": "💪", "biceps": "💪",
    "pernas": "🦵", "ombro_full": "💪", "trapezio": "🏔️",
}

WORKOUT_DESC = {
    "A": "Peito · Ombro Lateral · Tríceps",
    "B": "Costas · Ombro Post. · Bíceps",
    "C": "Pernas",
    "D": "Peito · Costas · Braços",
    "E": "Ombros · Trapézio · Braços",
}


def _get_last_sets(exercise_name: str, state: dict) -> list:
    for session in state.get("workout_history", []):
        sets = session.get("sets", {}).get(exercise_name, [])
        if sets:
            return sets
    return []


def _init_session(workout: str, state: dict):
    sets = {}
    for ex in EXERCISES[workout]:
        last = _get_last_sets(ex["nome"], state)
        ex_sets = []
        for i in range(ex["series"]):
            if last and i < len(last):
                ex_sets.append({
                    "weight": float(last[i].get("weight", 0)),
                    "reps": int(last[i].get("reps", 0)),
                    "done": False,
                })
            else:
                ex_sets.append({"weight": 0.0, "reps": 0, "done": False})
        sets[ex["nome"]] = ex_sets

    st.session_state.active_workout = {
        "workout": workout,
        "started_at": datetime.now().isoformat(),
        "sets": sets,
    }


def _finish_workout(state: dict, save_fn):
    session = st.session_state.active_workout
    workout = session["workout"]
    volume = sum(
        s["weight"] * s["reps"]
        for sets in session["sets"].values()
        for s in sets
        if s["done"]
    )
    entry = {
        "date": str(datetime.now().date()),
        "workout": workout,
        "completed_at": datetime.now().isoformat(),
        "sets": session["sets"],
        "volume_total": round(volume, 1),
    }
    history = state.get("workout_history", [])
    history.insert(0, entry)
    state["workout_history"] = history[:60]  # keep last 60 sessions

    log_entry = {
        "date": entry["date"],
        "workout": workout,
        "completed_at": entry["completed_at"],
    }
    state["workout_log"] = [log_entry] + state.get("workout_log", [])

    if workout != "E":
        state["current_index"] = (state["current_index"] + 1) % 4

    save_fn(state)
    st.session_state.active_workout = None
    st.success(f"✅ Treino {workout} finalizado! Volume: {volume:,.0f} kg")


def render_musculacao(state: dict, hevy_df, save_fn):
    if "active_workout" not in st.session_state:
        st.session_state.active_workout = None

    if st.session_state.active_workout is None:
        _render_picker(state, save_fn)
    else:
        _render_session(state, save_fn)


# ── Tela de escolha de treino ──────────────────────────────────────────────────

def _render_picker(state: dict, save_fn):
    st.markdown("### Qual treino hoje?")

    cols = st.columns(5)
    for i, letter in enumerate(["A", "B", "C", "D", "E"]):
        with cols[i]:
            conflict, _ = check_72h_conflict(state, letter)
            label = f"**{letter}**\n\n{WORKOUT_DESC[letter]}"
            btn = st.button(
                f"Treino {letter}",
                key=f"pick_{letter}",
                use_container_width=True,
                type="primary" if not conflict else "secondary",
            )
            st.caption(WORKOUT_DESC[letter])
            if conflict:
                st.caption("⚠️ 72h")
            if btn:
                _init_session(letter, state)
                st.rerun()

    # Histórico resumido
    history = state.get("workout_history", [])
    if history:
        st.markdown("---")
        st.markdown("#### Últimos treinos")
        for s in history[:6]:
            vol = s.get("volume_total", 0)
            st.markdown(
                f"**{s['workout']}** — {s['date']} — {vol:,.0f} kg volume"
            )


# ── Sessão ativa ───────────────────────────────────────────────────────────────

def _render_session(state: dict, save_fn):
    session = st.session_state.active_workout
    workout = session["workout"]
    exercises = EXERCISES[workout]

    # Header
    col_title, col_cancel = st.columns([4, 1])
    with col_title:
        st.markdown(f"### 🏋️ Treino {workout} — {WORKOUT_DESC[workout]}")
    with col_cancel:
        if st.button("✕ Sair", help="Cancela sem salvar"):
            st.session_state.active_workout = None
            st.rerun()

    # Progresso global
    all_sets = [s for ex in exercises for s in session["sets"].get(ex["nome"], [])]
    done_sets = [s for s in all_sets if s["done"]]
    progress = len(done_sets) / len(all_sets) if all_sets else 0
    st.progress(progress, text=f"{len(done_sets)} / {len(all_sets)} séries")

    st.markdown("---")

    # Exercícios
    for ex in exercises:
        name = ex["nome"]
        ex_sets = session["sets"].get(name, [])
        done_count = sum(1 for s in ex_sets if s["done"])
        all_done = done_count == len(ex_sets) and len(ex_sets) > 0

        icon = "✅" if all_done else "○"
        last = _get_last_sets(name, state)
        last_hint = ""
        if last:
            last_hint = "  ·  ".join(
                f"{s['weight']}kg×{s['reps']}" for s in last if s.get("done")
            )

        with st.expander(f"{icon} {name}", expanded=not all_done):
            if last_hint:
                st.caption(f"Última vez: {last_hint}")

            for i, s in enumerate(ex_sets):
                c_num, c_w, c_r, c_btn = st.columns([0.7, 2, 2, 1])
                with c_num:
                    st.markdown(f"**{i+1}**")
                with c_w:
                    w = st.number_input(
                        "kg",
                        min_value=0.0, max_value=400.0, step=2.5,
                        value=float(s["weight"]),
                        key=f"w_{name}_{i}",
                        label_visibility="collapsed",
                    )
                    s["weight"] = w
                with c_r:
                    r = st.number_input(
                        "reps",
                        min_value=0, max_value=200, step=1,
                        value=int(s["reps"]),
                        key=f"r_{name}_{i}",
                        label_visibility="collapsed",
                    )
                    s["reps"] = r
                with c_btn:
                    if s["done"]:
                        if st.button("✅", key=f"chk_{name}_{i}", help="Desmarcar"):
                            s["done"] = False
                            st.rerun()
                    else:
                        if st.button("○", key=f"chk_{name}_{i}", help="Marcar feito"):
                            s["done"] = True
                            st.rerun()

    st.markdown("---")

    col_fin, col_vol = st.columns([2, 1])
    with col_vol:
        vol_atual = sum(
            s["weight"] * s["reps"]
            for ex in exercises
            for s in session["sets"].get(ex["nome"], [])
            if s["done"]
        )
        st.metric("Volume atual", f"{vol_atual:,.0f} kg")
    with col_fin:
        if st.button("🏁 Finalizar Treino", type="primary", use_container_width=True):
            _finish_workout(state, save_fn)
            st.rerun()
