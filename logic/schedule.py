from datetime import datetime, timedelta

WORKOUT_SEQUENCE = ["A", "B", "C", "D"]

MUSCLE_GROUPS = {
    "A": {"peito", "ombro_lat", "triceps"},
    "B": {"costas", "ombro_post", "biceps"},
    "C": {"pernas"},
    "D": {"peito", "costas", "triceps", "biceps"},
    "E": {"ombro_full", "trapezio", "triceps", "biceps"},
}

WORKOUT_LABELS = {
    "A": "Treino A — Peito / Ombro Lateral / Tríceps",
    "B": "Treino B — Costas / Ombro Posterior / Bíceps",
    "C": "Treino C — Pernas (Máquinas)",
    "D": "Treino D — Peito / Costas / Braços",
    "E": "Treino E — Ombros / Trapézio / Braços",
}

EXERCISES = {
    "A": [
        {"nome": "Supino Inclinado na Máquina",      "series": 3, "reps": "10-12"},
        {"nome": "Peck Deck (Crucifixo na Máquina)", "series": 3, "reps": "10-12"},
        {"nome": "Elevação Lateral na Máquina",      "series": 3, "reps": "12-15"},
        {"nome": "Elevação Lateral com Halter",      "series": 3, "reps": "12-15"},
        {"nome": "Tríceps Corda na Polia",           "series": 3, "reps": "12-15"},
        {"nome": "Tríceps Francês na Polia",         "series": 3, "reps": "10-12"},
    ],
    "B": [
        {"nome": "Puxada Alta na Polia (Máquina)",          "series": 3, "reps": "10-12"},
        {"nome": "Remada Sentada c/ Pegada em V (Cabo)",    "series": 3, "reps": "10-12"},
        {"nome": "Remada na Máquina (Chest Supported)",     "series": 3, "reps": "10-12"},
        {"nome": "Elevação Posterior com Halter",           "series": 3, "reps": "12-15"},
        {"nome": "Rosca Direta na Polia",                   "series": 3, "reps": "12-15"},
        {"nome": "Rosca Scott na Máquina",                  "series": 3, "reps": "10-12"},
    ],
    "C": [
        {"nome": "Leg Press 45°",                          "series": 4, "reps": "12-15"},
        {"nome": "Cadeira Extensora (Quadríceps)",          "series": 3, "reps": "12-15"},
        {"nome": "Cadeira Flexora (Isquiotibiais)",         "series": 3, "reps": "12-15"},
        {"nome": "Abdução de Quadril na Máquina",           "series": 3, "reps": "15-20"},
        {"nome": "Adução de Quadril na Máquina",            "series": 3, "reps": "15-20"},
        {"nome": "Panturrilha Sentado na Máquina",          "series": 4, "reps": "15-20"},
    ],
    "D": [
        {"nome": "Supino Reto na Máquina",              "series": 3, "reps": "10-12"},
        {"nome": "Crossover na Polia (Cabo)",            "series": 3, "reps": "12-15"},
        {"nome": "Puxada Fechada na Polia",              "series": 3, "reps": "10-12"},
        {"nome": "Remada Unilateral com Halter",         "series": 3, "reps": "10-12"},
        {"nome": "Tríceps Mergulho na Máquina",          "series": 3, "reps": "10-12"},
        {"nome": "Rosca Alternada com Halter",           "series": 3, "reps": "10-12"},
    ],
    "E": [
        {"nome": "Desenvolvimento de Ombros na Máquina",   "series": 3, "reps": "10-12"},
        {"nome": "Elevação Lateral na Máquina",             "series": 3, "reps": "12-15"},
        {"nome": "Elevação Frontal na Polia",               "series": 3, "reps": "12-15"},
        {"nome": "Crucifixo Invertido (Peck Deck Inverso)", "series": 3, "reps": "12-15"},
        {"nome": "Encolhimento de Ombros com Halter",       "series": 3, "reps": "12-15"},
        {"nome": "Rosca Martelo com Halter",                "series": 3, "reps": "10-12"},
        {"nome": "Tríceps Pulley Reto",                     "series": 3, "reps": "12-15"},
    ],
}


def get_next_workout(state: dict) -> str:
    if state.get("use_e_next"):
        return "E"
    return WORKOUT_SEQUENCE[state["current_index"] % 4]


def check_72h_conflict(state: dict, workout: str):
    """Returns (has_conflict, message)."""
    groups = MUSCLE_GROUPS.get(workout, set())
    log = state.get("workout_log", [])
    cutoff = datetime.now() - timedelta(hours=72)

    for entry in log:
        try:
            ts = datetime.fromisoformat(entry["completed_at"])
        except Exception:
            continue
        if ts < cutoff:
            continue
        prev_groups = MUSCLE_GROUPS.get(entry["workout"], set())
        overlap = groups & prev_groups
        if overlap:
            hours_ago = (datetime.now() - ts).total_seconds() / 3600
            remaining = 72 - hours_ago
            return True, (
                f"⚠️ Treino {entry['workout']} foi feito há {hours_ago:.0f}h. "
                f"Conflito: {', '.join(overlap)}. "
                f"Aguarde mais {remaining:.0f}h para descanso ideal."
            )
    return False, ""


def mark_workout_done(state: dict) -> dict:
    workout = get_next_workout(state)
    entry = {
        "date": str(datetime.now().date()),
        "workout": workout,
        "completed_at": datetime.now().isoformat(),
    }
    state["workout_log"] = [entry] + state.get("workout_log", [])

    if state.get("use_e_next"):
        state["use_e_next"] = False
    else:
        state["current_index"] = (state["current_index"] + 1) % 4

    return state
