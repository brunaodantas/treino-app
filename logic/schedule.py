from datetime import datetime, timedelta
from utils import now_br

WORKOUT_SEQUENCE = ["A", "B", "C", "D"]

MUSCLE_GROUPS = {
    "A": {"peito", "ombro_lat", "triceps"},
    "B": {"costas", "ombro_post", "biceps"},
    "C": {"pernas"},
    "D": {"peito", "costas", "triceps", "biceps"},
    "E": {"ombro_full", "trapezio", "triceps", "biceps"},
}

WORKOUT_LABELS = {
    "A": "Treino A — Peito · Ombro · Tríceps",
    "B": "Treino B — Costas · Bíceps",
    "C": "Treino C — Pernas",
    "D": "Treino D — Peito · Costas · Braços",
    "E": "Treino E — Ombros · Trapézio · Braços",
}

EXERCISES_C_REDUCED = [
    {"nome": "Leg Press 45°",          "series": 4, "reps": "12-15", "peso_atual": 120.0, "peso_prog": 130.0},
    {"nome": "Adução Quadril Máquina", "series": 3, "reps": "15-20", "peso_atual":  50.0, "peso_prog":  55.0},
]

EXERCISES = {
    "A": [
        {"nome": "Supino Inclinado Halter",    "series": 3, "reps": "8-10",  "peso_atual": 20.0, "peso_prog": 22.0},
        {"nome": "Supino Reto Halter",         "series": 3, "reps": "10-12", "peso_atual": 20.0, "peso_prog": 22.0},
        {"nome": "Crossover Polia",            "series": 3, "reps": "12-15", "peso_atual": 13.0, "peso_prog": 15.0},
        {"nome": "Elevação Lateral Polia",     "series": 3, "reps": "12-15", "peso_atual":  9.0, "peso_prog": 11.0},
        {"nome": "Tríceps Corda Barra",        "series": 3, "reps": "12-15", "peso_atual": 50.0, "peso_prog": 55.0},
        {"nome": "Tríceps Francês Polia",      "series": 3, "reps": "10-12", "peso_atual": 25.0, "peso_prog": 30.0},
    ],
    "B": [
        {"nome": "Puxada Alta Polia",          "series": 3, "reps": "10-12", "peso_atual": 45.0, "peso_prog": 50.0},
        {"nome": "Remada Sentada c/ Pegada V", "series": 3, "reps": "10-12", "peso_atual": 45.0, "peso_prog": 50.0},
        {"nome": "Remada Chest Supported",     "series": 3, "reps": "10-12", "peso_atual": 45.0, "peso_prog": 50.0},
        {"nome": "Rosca Direta Polia",         "series": 3, "reps": "12-15", "peso_atual": 25.0, "peso_prog": 26.0},
        {"nome": "Rosca Scott Máquina",        "series": 3, "reps": "10-12", "peso_atual": 25.0, "peso_prog": 27.0},
    ],
    "C": [
        {"nome": "Leg Press 45°",              "series": 4, "reps": "12-15", "peso_atual": 120.0, "peso_prog": 130.0},
        {"nome": "Cadeira Extensora",          "series": 3, "reps": "12-15", "peso_atual": 63.0, "peso_prog": 70.0},
        {"nome": "Cadeira Flexora",            "series": 3, "reps": "12-15", "peso_atual": 41.0, "peso_prog": 46.0},
        {"nome": "Adução Quadril Máquina",     "series": 3, "reps": "15-20", "peso_atual": 50.0, "peso_prog": 55.0},
        {"nome": "Panturrilha Sentado",        "series": 3, "reps": "15-20", "peso_atual": 50.0, "peso_prog": 55.0},
    ],
    "D": [
        {"nome": "Supino Reto Máquina",        "series": 3, "reps": "10-12", "peso_atual": 40.0, "peso_prog": 45.0},
        {"nome": "Crossover Polia",            "series": 3, "reps": "12-15", "peso_atual": 13.0, "peso_prog": 15.0},
        {"nome": "Puxada Fechada Polia",       "series": 3, "reps": "10-12", "peso_atual": 45.0, "peso_prog": 50.0},
        {"nome": "Remada Unilateral Halter",   "series": 3, "reps": "10-12", "peso_atual": 24.0, "peso_prog": 27.0},
        {"nome": "Rosca Martelo Halter",       "series": 3, "reps": "10-12", "peso_atual": 14.0, "peso_prog": 16.0},
        {"nome": "Tríceps Mergulho Máquina",   "series": 3, "reps": "10-12", "peso_atual": 70.0, "peso_prog": 80.0},
    ],
    "E": [
        {"nome": "Desenvolvimento Ombros Máquina",  "series": 3, "reps": "10-12", "peso_atual": 30.0, "peso_prog": 35.0},
        {"nome": "Elevação Lateral Máquina",        "series": 3, "reps": "12-15", "peso_atual": 10.0, "peso_prog": 12.0},
        {"nome": "Elevação Frontal Polia",          "series": 3, "reps": "12-15", "peso_atual":  9.0, "peso_prog": 11.0},
        {"nome": "Crucifixo Invertido",             "series": 3, "reps": "12-15", "peso_atual": 10.0, "peso_prog": 12.0},
        {"nome": "Encolhimento Ombros Halter",      "series": 3, "reps": "12-15", "peso_atual": 20.0, "peso_prog": 22.0},
        {"nome": "Rosca Martelo Halter",            "series": 3, "reps": "10-12", "peso_atual": 14.0, "peso_prog": 16.0},
        {"nome": "Tríceps Pulley Reto",             "series": 3, "reps": "12-15", "peso_atual": 25.0, "peso_prog": 27.0},
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
    now = now_br()
    cutoff = now - timedelta(hours=72)

    for entry in log:
        try:
            ts = datetime.fromisoformat(entry["completed_at"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=now.tzinfo)
        except Exception:
            continue
        if ts < cutoff:
            continue
        prev_groups = MUSCLE_GROUPS.get(entry["workout"], set())
        overlap = groups & prev_groups
        if overlap:
            hours_ago = (now - ts).total_seconds() / 3600
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
