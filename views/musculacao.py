import streamlit as st
from logic.schedule import (
    get_next_workout, WORKOUT_LABELS, EXERCISES, WORKOUT_SEQUENCE,
    check_72h_conflict, mark_workout_done,
)
from logic.adaptation import (
    is_adaptation_phase, get_adaptation_week, get_adaptation_load,
    get_max_loads_from_hevy, ADAPTATION_MESSAGE, ADAPTATION_WEEKS,
)


def render_musculacao(state: dict, hevy_df, save_fn):
    next_wk = get_next_workout(state)
    week = get_adaptation_week(state)
    in_adaptation = is_adaptation_phase(state)
    max_loads = get_max_loads_from_hevy(hevy_df)

    st.markdown(f"### Próximo Treino: {WORKOUT_LABELS[next_wk]}")

    # Fila visual
    queue = []
    idx = state["current_index"]
    if state.get("use_e_next"):
        queue.append(("E", True))
    for i in range(6):
        letter = WORKOUT_SEQUENCE[(idx + i) % 4]
        queue.append((letter, i == 0 and not state.get("use_e_next")))

    fila_str = " → ".join(
        f"**[{l}]**" if current else l for l, current in queue[:5]
    )
    st.markdown(f"**Fila:** {fila_str} → ...")

    if in_adaptation:
        st.warning(ADAPTATION_MESSAGE)
    else:
        st.info("💪 Fase de adaptação concluída — evolua as cargas progressivamente.")

    st.markdown("---")

    # Tabs por treino
    tab_labels = [f"**{l}**" if l == next_wk else l for l in ["A", "B", "C", "D", "E"]]
    tabs = st.tabs(["A", "B", "C", "D", "E ⚡"])
    for tab, letter in zip(tabs, ["A", "B", "C", "D", "E"]):
        with tab:
            _render_workout_tab(letter, in_adaptation, max_loads, letter == next_wk)

    st.markdown("---")

    # Botão check
    conflict, conflict_msg = check_72h_conflict(state, next_wk)
    if conflict:
        st.warning(conflict_msg)
    if st.button(f"✅ Marcar Treino {next_wk} como Concluído", type="primary"):
        state = mark_workout_done(state)
        save_fn(state)
        st.success(f"Treino {next_wk} registrado!")
        st.rerun()


def _render_workout_tab(letter: str, in_adaptation: bool, max_loads: dict, is_current: bool):
    label = WORKOUT_LABELS[letter]
    if is_current:
        st.markdown(f"#### ▶ {label}")
    else:
        st.markdown(f"#### {label}")

    exercises = EXERCISES[letter]

    # Build table data
    rows = []
    for ex in exercises:
        nome = ex["nome"]
        series = ex["series"]
        reps = ex["reps"]
        max_load = max_loads.get(nome)

        if in_adaptation:
            target = get_adaptation_load(max_load)
            hist = f"{max_load:.1f} kg" if max_load else "—"
        else:
            target = f"{max_load:.1f} kg" if max_load else "—"
            hist = target

        rows.append({
            "Exercício": nome,
            "Séries × Reps": f"{series} × {reps}",
            "Carga hist. máx.": hist if in_adaptation else "—",
            "Meta de Retorno (65%)": target if in_adaptation else "—",
        })

    import pandas as pd
    df = pd.DataFrame(rows)

    if not in_adaptation:
        df = df.drop(columns=["Carga hist. máx.", "Meta de Retorno (65%)"])
        df["Carga"] = "—"

    st.dataframe(df, use_container_width=True, hide_index=True)

    if in_adaptation and not max_loads:
        st.caption("💡 Faça upload do Hevy CSV na sidebar para ver as metas de carga automáticas.")
