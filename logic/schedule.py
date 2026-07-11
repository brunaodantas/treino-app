from __future__ import annotations
from datetime import date, datetime, timedelta
from utils import now_br

WORKOUT_SEQUENCE = ["A", "B", "C", "D"]

# Dias de musculação: Terça=1, Quarta=2, Sexta=4 (weekday numbers)
WORKOUT_DAYS = [1, 2, 4]
DAY_NAMES = {1: "Terça", 2: "Quarta", 4: "Sexta"}

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


# ── Agenda semanal com rotação deslizante ──────────────────────────────────────

def _schedule_origin(state: dict) -> date:
    """Segunda-feira da semana em que o app foi iniciado (âncora do ciclo)."""
    raw = state.get("app_start_date", str(date.today()))
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        d = date.today()
    return d - timedelta(days=d.weekday())  # normaliza para segunda


def get_cycle_week(state: dict, ref: date = None) -> int:
    """Número de semanas desde o início (0-indexed), para calcular offset do ciclo.
    schedule_week_offset ajusta qual treino cai em qual dia da semana."""
    ref = ref or date.today()
    origin = _schedule_origin(state)
    raw = max(0, (ref - origin).days // 7)
    offset = int(state.get("schedule_week_offset", 0))
    return (raw + offset) % 4


def get_scheduled_workout(state: dict, d: date = None) -> str | None:
    """
    Retorna o treino programado para a data d.
    Retorna None se d não for dia de musculação (Ter/Qua/Sex).

    Ciclo de 4 semanas:
      Sem 1: Ter=A Qua=B Sex=C
      Sem 2: Ter=D Qua=A Sex=B
      Sem 3: Ter=C Qua=D Sex=A
      Sem 4: Ter=B Qua=C Sex=D
    Fórmula: SEQUENCE[(slot_index - week_num) % 4]
    """
    d = d or date.today()
    weekday = d.weekday()
    if weekday not in WORKOUT_DAYS:
        return None
    slot_index = WORKOUT_DAYS.index(weekday)
    week_num = get_cycle_week(state, d)
    return WORKOUT_SEQUENCE[(slot_index - week_num) % 4]


def get_week_schedule(state: dict, week_offset: int = 0) -> list:
    """
    Retorna a agenda da semana atual + week_offset semanas.
    Lista de dicts: {dia, data, treino, hoje}
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_monday = monday + timedelta(weeks=week_offset)
    result = []
    for weekday in WORKOUT_DAYS:
        d = week_monday + timedelta(days=weekday)
        result.append({
            "dia": DAY_NAMES[weekday],
            "data": d,
            "treino": get_scheduled_workout(state, d),
            "hoje": d == today,
        })
    return result


def get_next_scheduled(state: dict) -> tuple:
    """Retorna (date, workout_letter) do próximo dia de musculação a partir de hoje."""
    today = date.today()
    for days_ahead in range(10):
        d = today + timedelta(days=days_ahead)
        w = get_scheduled_workout(state, d)
        if w:
            return d, w
    return None, None


def get_next_workout(state: dict) -> str:
    """Retorna o treino da agenda para hoje (se dia de musculação) ou o próximo agendado."""
    if state.get("use_e_next"):
        return "E"
    today_w = get_scheduled_workout(state)
    if today_w:
        return today_w
    _, next_w = get_next_scheduled(state)
    if next_w:
        return next_w
    return WORKOUT_SEQUENCE[state.get("current_index", 0) % 4]


# ── Conflito 72h ──────────────────────────────────────────────────────────────

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


# ── Marcar treino concluído ───────────────────────────────────────────────────

def mark_workout_done(state: dict, workout: str = None) -> dict:
    if state.get("use_e_next"):
        workout = "E"
        state["use_e_next"] = False
    elif workout is None:
        workout = get_next_workout(state)

    now = now_br()
    entry = {
        "date": now.date().isoformat(),
        "workout": workout,
        "completed_at": now.isoformat(),
    }
    state["workout_log"] = [entry] + state.get("workout_log", [])

    # Mantém current_index em sincronia com a agenda
    if workout in WORKOUT_SEQUENCE:
        state["current_index"] = (WORKOUT_SEQUENCE.index(workout) + 1) % 4

    return state
