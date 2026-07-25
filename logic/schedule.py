from __future__ import annotations
from datetime import date, datetime, timedelta
from utils import now_br

# ── Programa ativo (desde 28/07/2026): corpo inteiro, 3x/semana ────────────────
# Ciclo fixo de 3 treinos. Cada músculo é treinado 3x na semana em vez de 0,75x.
# Superséries de antagonistas: o par mantém o descanso ideal por músculo (~2,4 min
# no SS1) dentro do limite de 40 min de academia.
WORKOUT_SEQUENCE = ["1", "2", "3"]

# Dias de musculação: Terça=1, Quarta=2, Sábado=5 (weekday numbers)
# Segunda e sexta são só corrida. Quinta e domingo, descanso.
WORKOUT_DAYS = [1, 2, 5]
DAY_NAMES = {1: "Terça", 2: "Quarta", 5: "Sábado"}

# Treinos 1/2/3 são corpo inteiro — a sobreposição de grupos é intencional.
_FULL_BODY_GROUPS = {
    "peito", "costas", "ombro_lat", "ombro_post", "triceps", "biceps",
    "quadriceps", "isquios", "gluteo_adutor", "core",
}
FULL_BODY_WORKOUTS = {"1", "2", "3"}

MUSCLE_GROUPS = {
    # Programa ativo — corpo inteiro
    "1": set(_FULL_BODY_GROUPS),
    "2": set(_FULL_BODY_GROUPS) | {"panturrilha"},
    "3": set(_FULL_BODY_GROUPS) | {"trapezio"},
}

WORKOUT_LABELS = {
    "1": "Treino 1 — Corpo inteiro · Supino Inclinado + Remada",
    "2": "Treino 2 — Corpo inteiro · Supino Máquina + Remada V",
    "3": "Treino 3 — Corpo inteiro · Supino Halter + Remada Unilateral",
}

# Split A–E aposentado em 25/07/2026. Mantido só para o histórico não quebrar —
# workout_log e workout_history têm registros antigos com essas letras.
LEGACY_LABELS = {
    "A": "Treino A — Peito · Ombro · Tríceps (aposentado)",
    "B": "Treino B — Costas · Bíceps (aposentado)",
    "C": "Treino C — Pernas (aposentado)",
    "D": "Treino D — Peito · Costas · Braços (aposentado)",
    "E": "Treino E — Glúteo · Core (aposentado)",
}


def label_for(workout: str) -> str:
    """Rótulo de um treino, atual ou aposentado. Nunca levanta KeyError."""
    return WORKOUT_LABELS.get(workout) or LEGACY_LABELS.get(workout, f"Treino {workout}")

# Descanso ideal DEPOIS de marcar a série, em segundos.
# Primeiro exercício do par = só o tempo de trocar de aparelho.
# Segundo exercício do par = o descanso real do par.
REST_PAIR_2 = {"SS1": 90, "SS2": 75, "SS3": 60, "SS4": 75, "CORE": 45}
REST_PAIR_1 = 20

def _ss(ss: str, pos: int, par: str) -> dict:
    """Metadados de supersérie: grupo, posição no par, parceiro e descanso."""
    return {
        "ss": ss,
        "ss_pos": pos,
        "par": par,
        "rest": REST_PAIR_1 if pos == 1 else REST_PAIR_2[ss],
    }


EXERCISES = {
    # ── Programa ativo — corpo inteiro 3x/semana ───────────────────────────────
    "1": [
        {"nome": "Supino Inclinado Halter",    "series": 3, "reps": "8-10",  "peso_atual":  20.0, "peso_prog":  22.0, **_ss("SS1", 1, "Remada Chest Supported")},
        {"nome": "Remada Chest Supported",     "series": 3, "reps": "10-12", "peso_atual":  45.0, "peso_prog":  50.0, **_ss("SS1", 2, "Supino Inclinado Halter")},
        {"nome": "Elevação Lateral Polia",     "series": 3, "reps": "12-15", "peso_atual":   9.0, "peso_prog":  11.0, **_ss("SS2", 1, "Puxada Alta Polia")},
        {"nome": "Puxada Alta Polia",          "series": 3, "reps": "10-12", "peso_atual":  45.0, "peso_prog":  50.0, **_ss("SS2", 2, "Elevação Lateral Polia")},
        {"nome": "Tríceps Corda Barra",        "series": 3, "reps": "12-15", "peso_atual":  50.0, "peso_prog":  55.0, **_ss("SS3", 1, "Rosca Direta Polia")},
        {"nome": "Rosca Direta Polia",         "series": 3, "reps": "12-15", "peso_atual":  25.0, "peso_prog":  26.0, **_ss("SS3", 2, "Tríceps Corda Barra")},
        {"nome": "Leg Press 45°",              "series": 3, "reps": "12-15", "peso_atual": 120.0, "peso_prog": 130.0, **_ss("SS4", 1, "Cadeira Flexora")},
        {"nome": "Cadeira Flexora",            "series": 3, "reps": "12-15", "peso_atual":  41.0, "peso_prog":  46.0, **_ss("SS4", 2, "Leg Press 45°")},
        {"nome": "Prancha",                    "series": 3, "reps": "40s",   "peso_atual":   0.0, "peso_prog":   0.0, **_ss("CORE", 2, "")},
    ],
    "2": [
        {"nome": "Supino Reto Máquina",        "series": 3, "reps": "10-12", "peso_atual":  40.0, "peso_prog":  45.0, **_ss("SS1", 1, "Remada Sentada c/ Pegada V")},
        {"nome": "Remada Sentada c/ Pegada V", "series": 3, "reps": "10-12", "peso_atual":  45.0, "peso_prog":  50.0, **_ss("SS1", 2, "Supino Reto Máquina")},
        {"nome": "Crucifixo Inverso Polia",    "series": 3, "reps": "12-15", "peso_atual":   9.0, "peso_prog":  11.0, **_ss("SS2", 1, "Puxada Fechada Polia")},
        {"nome": "Puxada Fechada Polia",       "series": 3, "reps": "10-12", "peso_atual":  45.0, "peso_prog":  50.0, **_ss("SS2", 2, "Crucifixo Inverso Polia")},
        {"nome": "Tríceps Mergulho Máquina",   "series": 3, "reps": "10-12", "peso_atual":  70.0, "peso_prog":  80.0, **_ss("SS3", 1, "Rosca Martelo Halter")},
        {"nome": "Rosca Martelo Halter",       "series": 3, "reps": "10-12", "peso_atual":  14.0, "peso_prog":  16.0, **_ss("SS3", 2, "Tríceps Mergulho Máquina")},
        {"nome": "Cadeira Extensora",          "series": 3, "reps": "15-20", "peso_atual":  63.0, "peso_prog":  70.0, **_ss("SS4", 1, "Abdução Quadril Máquina")},
        {"nome": "Abdução Quadril Máquina",    "series": 3, "reps": "15-20", "peso_atual":  50.0, "peso_prog":  55.0, **_ss("SS4", 2, "Cadeira Extensora")},
        {"nome": "Elevação de Pernas",         "series": 3, "reps": "12",    "peso_atual":   0.0, "peso_prog":   0.0, **_ss("CORE", 1, "Panturrilha Sentado")},
        {"nome": "Panturrilha Sentado",        "series": 3, "reps": "15-20", "peso_atual":  50.0, "peso_prog":  55.0, **_ss("CORE", 2, "Elevação de Pernas")},
    ],
    "3": [
        {"nome": "Supino Reto Halter",         "series": 3, "reps": "10-12", "peso_atual":  20.0, "peso_prog":  22.0, **_ss("SS1", 1, "Remada Unilateral Halter")},
        {"nome": "Remada Unilateral Halter",   "series": 3, "reps": "10-12", "peso_atual":  24.0, "peso_prog":  27.0, **_ss("SS1", 2, "Supino Reto Halter")},
        {"nome": "Elevação Lateral Polia",     "series": 3, "reps": "12-15", "peso_atual":   9.0, "peso_prog":  11.0, **_ss("SS2", 1, "Puxada Alta Polia")},
        {"nome": "Puxada Alta Polia",          "series": 3, "reps": "10-12", "peso_atual":  45.0, "peso_prog":  50.0, **_ss("SS2", 2, "Elevação Lateral Polia")},
        {"nome": "Tríceps Francês Polia",      "series": 3, "reps": "10-12", "peso_atual":  25.0, "peso_prog":  30.0, **_ss("SS3", 1, "Rosca Scott Máquina")},
        {"nome": "Rosca Scott Máquina",        "series": 3, "reps": "10-12", "peso_atual":  25.0, "peso_prog":  27.0, **_ss("SS3", 2, "Tríceps Francês Polia")},
        {"nome": "Cadeira Flexora",            "series": 3, "reps": "12-15", "peso_atual":  41.0, "peso_prog":  46.0, **_ss("SS4", 1, "Adução Quadril Máquina")},
        {"nome": "Adução Quadril Máquina",     "series": 3, "reps": "15-20", "peso_atual":  50.0, "peso_prog":  55.0, **_ss("SS4", 2, "Cadeira Flexora")},
        {"nome": "Rodinha (Ab Wheel)",         "series": 3, "reps": "8",     "peso_atual":   0.0, "peso_prog":   0.0, **_ss("CORE", 1, "Encolhimento Halter")},
        {"nome": "Encolhimento Halter",        "series": 3, "reps": "12-15", "peso_atual":  24.0, "peso_prog":  27.0, **_ss("CORE", 2, "Rodinha (Ab Wheel)")},
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
    Retorna None se d não for dia de musculação (Ter/Qua/Sáb).

    Mapeamento fixo — 3 treinos e 3 dias sincronizam, sem fila deslizante:
      Ter = Treino 1 · Qua = Treino 2 · Sáb = Treino 3
    Se numa semana houver uma 4ª sessão, ela avança o ciclo manualmente pela
    seleção livre de treino no dashboard.
    """
    d = d or date.today()
    weekday = d.weekday()
    if weekday not in WORKOUT_DAYS:
        return None
    return WORKOUT_SEQUENCE[WORKOUT_DAYS.index(weekday)]


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
    return WORKOUT_SEQUENCE[state.get("current_index", 0) % len(WORKOUT_SEQUENCE)]


# ── Conflito 72h ──────────────────────────────────────────────────────────────

def check_72h_conflict(state: dict, workout: str):
    """
    Returns (has_conflict, message).

    Programa ativo (1/2/3) é corpo inteiro 3x/semana — a sobreposição de grupos
    é intencional, não conflito. Nesse caso a regra de 72h por grupo não se
    aplica: só alerta se a MESMA sessão foi repetida em menos de 20h.
    A regra original de 72h continua valendo para o split antigo (A–E).
    """
    log = state.get("workout_log", [])
    now = now_br()

    if workout in FULL_BODY_WORKOUTS:
        for entry in log:
            if entry.get("workout") != workout:
                continue
            try:
                ts = datetime.fromisoformat(entry["completed_at"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=now.tzinfo)
            except Exception:
                continue
            hours_ago = (now - ts).total_seconds() / 3600
            if hours_ago < 20:
                return True, (
                    f"⚠️ Treino {workout} foi feito há {hours_ago:.0f}h. "
                    f"Corpo inteiro pede ~24h entre sessões — considere o próximo do ciclo."
                )
        return False, ""

    groups = MUSCLE_GROUPS.get(workout, set())
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
