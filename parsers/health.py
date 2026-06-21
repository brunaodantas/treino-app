import xml.etree.ElementTree as ET
from datetime import datetime, date
from collections import defaultdict
import streamlit as st


WORKOUT_TYPE_MAP = {
    "HKWorkoutActivityTypeRunning": "Corrida",
    "HKWorkoutActivityTypeWalking": "Caminhada",
    "HKWorkoutActivityTypeCycling": "Pedalada",
    "HKWorkoutActivityTypeTraditionalStrengthTraining": "Musculação",
    "HKWorkoutActivityTypeFunctionalStrengthTraining": "Força Funcional",
    "HKWorkoutActivityTypeOther": "Outro",
    "HKWorkoutActivityTypeElliptical": "Elíptico",
    "HKWorkoutActivityTypeMixedCardio": "Cardio Misto",
    "HKWorkoutActivityTypeHiking": "Trilha",
    "HKWorkoutActivityTypeRowing": "Remo",
}


def parse_health(file, progress_bar=None) -> dict:
    """
    Parses Apple Health XML (streaming via iterparse).
    Returns a dict with workouts, daily_steps, daily_calories.
    """
    result = {
        "workouts": [],
        "daily_steps": defaultdict(float),
        "daily_calories": defaultdict(float),
        "daily_resting_hr": defaultdict(list),
    }

    content = file.read() if hasattr(file, "read") else open(file, "rb").read()
    total_size = len(content)
    processed = 0
    chunk_report = total_size // 20

    import io
    source = io.BytesIO(content)

    context = ET.iterparse(source, events=("end",))
    count = 0

    for event, elem in context:
        count += 1
        if count % 50000 == 0 and progress_bar is not None:
            progress_bar.progress(min(0.95, count / 5_000_000))

        if elem.tag == "Workout":
            workout = _parse_workout(elem)
            if workout:
                result["workouts"].append(workout)

        elif elem.tag == "Record":
            rtype = elem.attrib.get("type", "")
            val = elem.attrib.get("value")
            start = elem.attrib.get("startDate", "")[:10]

            if rtype == "HKQuantityTypeIdentifierStepCount" and val:
                try:
                    result["daily_steps"][start] += float(val)
                except ValueError:
                    pass

            elif rtype == "HKQuantityTypeIdentifierActiveEnergyBurned" and val:
                try:
                    result["daily_calories"][start] += float(val)
                except ValueError:
                    pass

            elif rtype == "HKQuantityTypeIdentifierRestingHeartRate" and val:
                try:
                    result["daily_resting_hr"][start].append(float(val))
                except ValueError:
                    pass

        elem.clear()

    if progress_bar is not None:
        progress_bar.progress(1.0)

    return result


def _parse_workout(elem):
    wtype_raw = elem.attrib.get("workoutActivityType", "")
    wtype = WORKOUT_TYPE_MAP.get(wtype_raw, wtype_raw.replace("HKWorkoutActivityType", ""))
    start_str = elem.attrib.get("startDate", "")
    duration = elem.attrib.get("duration")
    start_date = start_str[:10] if start_str else None

    distance_km = None
    calories = None

    for child in elem:
        if child.tag == "WorkoutStatistics":
            stat_type = child.attrib.get("type", "")
            if "DistanceWalkingRunning" in stat_type or "DistanceCycling" in stat_type:
                unit = child.attrib.get("unit", "")
                val = child.attrib.get("sum")
                if val:
                    try:
                        distance_km = float(val)
                        if unit == "mi":
                            distance_km *= 1.60934
                    except ValueError:
                        pass
            elif "ActiveEnergyBurned" in stat_type:
                val = child.attrib.get("sum")
                if val:
                    try:
                        calories = float(val)
                    except ValueError:
                        pass

    if not start_date:
        return None

    return {
        "tipo": wtype,
        "data": start_date,
        "duracao_min": round(float(duration), 1) if duration else None,
        "distancia_km": round(distance_km, 2) if distance_km else None,
        "calorias": round(calories) if calories else None,
    }


def get_run_workouts(health_data: dict) -> list[dict]:
    if not health_data:
        return []
    return [w for w in health_data["workouts"] if w["tipo"] == "Corrida"]


def get_daily_steps_df(health_data: dict):
    import pandas as pd
    if not health_data:
        return pd.DataFrame()
    steps = health_data["daily_steps"]
    if not steps:
        return pd.DataFrame()
    df = pd.DataFrame(
        [(date, int(v)) for date, v in steps.items()],
        columns=["Data", "Passos"]
    )
    df["Data"] = pd.to_datetime(df["Data"])
    return df.sort_values("Data").tail(90)


def get_daily_calories_df(health_data: dict):
    import pandas as pd
    if not health_data:
        return pd.DataFrame()
    cals = health_data["daily_calories"]
    if not cals:
        return pd.DataFrame()
    df = pd.DataFrame(
        [(date, round(v)) for date, v in cals.items()],
        columns=["Data", "Calorias"]
    )
    df["Data"] = pd.to_datetime(df["Data"])
    return df.sort_values("Data").tail(90)
