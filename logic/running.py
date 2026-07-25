from datetime import date, timedelta

# Semana definida em 24/07/2026:
#   Seg = só corrida · Ter/Qua = musculação + corrida · Qui = descanso
#   Sex = só corrida · Sáb = só musculação · Dom = descanso
RUNNING_DAYS = {0: "Segunda", 1: "Terça", 2: "Quarta", 4: "Sexta"}
REST_DAYS = {3: "Quinta", 6: "Domingo"}
RUNNING_OPTIONAL_DAYS = set()  # nenhuma corrida é condicional — HRV descontinuado

# Segunda e sexta são os dias sem musculação: recebem as corridas mais longas.
# Terça e quarta dividem o dia com a musculação: corrida curta.
DAY_RUN_TYPE = {
    0: {"tipo": "intervalada", "duracao": "30-40 min", "descricao": "Corrida intervalada 1:1 (1 min corre / 1 min anda) — dia sem musculação"},
    1: {"tipo": "Z1 curta", "duracao": "20 min", "descricao": "Corrida Z1 curta — 20 min, FC ≤ 130bpm (dia de musculação)"},
    2: {"tipo": "Z1 curta", "duracao": "20 min", "descricao": "Corrida Z1 curta — 20 min, FC ≤ 130bpm (dia de musculação)"},
    4: {"tipo": "esteira intervalada", "duracao": "30-40 min", "descricao": "Corrida esteira intervalada — dia sem musculação"},
}

EQUIPMENT_REMINDER = "🛡️ **Equipamento obrigatório:** Palmilha plana de Gel PU — EU 41-42 / 260mm"
MAX_DISTANCE_KM = 10.0


def is_running_day(d: date = None) -> bool:
    d = d or date.today()
    return d.weekday() in RUNNING_DAYS


def is_optional_run_day(d: date = None) -> bool:
    d = d or date.today()
    return d.weekday() in RUNNING_OPTIONAL_DAYS


def get_run_info(d: date = None) -> dict:
    d = d or date.today()
    return DAY_RUN_TYPE.get(d.weekday(), {})


def is_rest_day(d: date = None) -> bool:
    d = d or date.today()
    return d.weekday() in REST_DAYS


def get_day_label(d: date = None) -> str:
    d = d or date.today()
    weekday = d.weekday()
    names = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
             4: "Sexta", 5: "Sábado", 6: "Domingo"}
    return names.get(weekday, "")


def get_current_distance(state: dict) -> float:
    try:
        start = date.fromisoformat(state.get("running_week_start", str(date.today())))
    except ValueError:
        start = date.today()
    weeks = max(0, (date.today() - start).days // 7)
    base = float(state.get("running_base_km", 3.0))
    distance = base * (1.10 ** weeks)
    return round(min(distance, MAX_DISTANCE_KM), 2)


def get_progression_table(state: dict, num_weeks: int = 8) -> list[dict]:
    try:
        start = date.fromisoformat(state.get("running_week_start", str(date.today())))
    except ValueError:
        start = date.today()
    base = float(state.get("running_base_km", 3.0))
    rows = []
    for i in range(num_weeks):
        week_start = start + timedelta(weeks=i)
        dist = round(min(base * (1.10 ** i), MAX_DISTANCE_KM), 2)
        current = (date.today() - week_start).days in range(7)
        rows.append({
            "Semana": i + 1,
            "Início": week_start.strftime("%d/%m"),
            "Distância (km)": dist,
            "Sessões": 4,
            "Volume semanal (km)": round(dist * 4, 2),
            "Atual": current,
        })
    return rows
