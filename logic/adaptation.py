ADAPTATION_WEEKS = 4
WORKOUTS_PER_WEEK = 5
LOAD_FACTOR = 0.65
ADAPTATION_MESSAGE = (
    "🎯 **Fase de Adaptação** — Foco 100% na execução e cadência. "
    "Mantenha **3 séries de 10-12 repetições**, sem buscar a falha concêntrica nesta fase de retorno."
)


def is_adaptation_phase(state: dict) -> bool:
    week = get_adaptation_week(state)
    return week <= ADAPTATION_WEEKS


def get_adaptation_week(state: dict) -> int:
    override = state.get("adaptation_week_override")
    if override is not None:
        return int(override)
    total = len(state.get("workout_log", []))
    return total // WORKOUTS_PER_WEEK + 1


def get_workouts_in_current_week(state: dict) -> int:
    """Treinos concluídos na semana de adaptação atual (0–5)."""
    override = state.get("adaptation_week_override")
    if override is not None:
        return 0
    total = len(state.get("workout_log", []))
    return total % WORKOUTS_PER_WEEK


def get_adaptation_load(max_load) -> str:
    if max_load is None or max_load == 0:
        return "—"
    return f"{round(max_load * LOAD_FACTOR, 1)} kg"


def get_max_loads_from_hevy(hevy_df) -> dict:
    """Returns {exercise_name: max_weight_kg} from Hevy CSV DataFrame."""
    if hevy_df is None or hevy_df.empty:
        return {}
    result = {}
    weight_col = next((c for c in hevy_df.columns if "weight" in c.lower()), None)
    name_col = next((c for c in hevy_df.columns if "exercise" in c.lower() and "name" in c.lower()), None)
    if not weight_col or not name_col:
        return {}
    for name, group in hevy_df.groupby(name_col):
        try:
            max_w = group[weight_col].dropna().astype(float).max()
            if max_w > 0:
                result[str(name)] = max_w
        except Exception:
            pass
    return result
