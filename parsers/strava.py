import pandas as pd
import io
from datetime import datetime


RUNNING_TYPES = {"Corrida", "Treinamento com peso", "Caminhada", "Pedalada", "Elíptico"}


def parse_strava(file):
    try:
        content = file.read() if hasattr(file, "read") else open(file, "rb").read()
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8", dtype=str)
        df = _dedup_columns(df)
        df = _normalize_columns(df)
        df = _parse_dates(df)
        return df
    except Exception as e:
        print(f"Erro ao ler Strava CSV: {e}")
        return None


def _dedup_columns(df: pd.DataFrame) -> pd.DataFrame:
    seen = {}
    new_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}.{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols
    return df


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    TARGETS = {
        "data": lambda c: "data da atividade" in c,
        "tipo": lambda c: "tipo de atividade" in c,
        "nome": lambda c: "nome da atividade" in c,
        "distancia_km": lambda c: c in ("distância", "distancia"),
        "velocidade_media": lambda c: ("velocidade média" in c or "velocidade media" in c) and "tempo" not in c,
        "fc_media": lambda c: "frequência cardíaca média" in c and "máx" not in c,
        "fc_max": lambda c: ("frequência cardíaca máxima" in c) and "média" not in c,
        "calorias": lambda c: c == "calorias",
        "tempo_decorrido": lambda c: c == "tempo decorrido",
        "elevacao_ganho": lambda c: "ganho de elevação" in c,
    }
    used_targets = set()
    rename = {}
    for col in df.columns:
        c = col.strip().lower()
        for target, matcher in TARGETS.items():
            if target not in used_targets and matcher(c):
                rename[col] = target
                used_targets.add(target)
                break
    df = df.rename(columns=rename)
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    if "data" not in df.columns:
        return df
    MONTH_MAP = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04",
        "mai": "05", "jun": "06", "jul": "07", "ago": "08",
        "set": "09", "out": "10", "nov": "11", "dez": "12",
    }

    def parse_date(s):
        if pd.isna(s):
            return pd.NaT
        s = str(s)
        for pt, num in MONTH_MAP.items():
            s = s.replace(f" de {pt}. de ", f"-{num}-").replace(f" de {pt} de ", f"-{num}-")
        s = s.replace(" de ", "-")
        try:
            return pd.to_datetime(s.split(",")[0].strip(), format="%d-%m-%Y", dayfirst=True)
        except Exception:
            try:
                return pd.to_datetime(s[:10], dayfirst=True)
            except Exception:
                return pd.NaT

    df["data"] = df["data"].apply(parse_date)
    df = df.sort_values("data", ascending=False).reset_index(drop=True)
    return df


def _to_float(series: pd.Series) -> pd.Series:
    """Handles both '3,14' (BR decimal) and '1.713' (dot decimal) formats."""
    return (
        series.astype(str)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )


def get_runs(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or "tipo" not in df.columns:
        return pd.DataFrame()
    mask = df["tipo"].str.contains("Corrida", case=False, na=False)
    runs = df[mask].copy()
    if "distancia_km" in runs.columns:
        runs["distancia_km"] = _to_float(runs["distancia_km"])
    if "velocidade_media" in runs.columns:
        runs["velocidade_media"] = _to_float(runs["velocidade_media"])
        runs["pace_min_km"] = runs["velocidade_media"].apply(
            lambda v: round(1000 / (v * 60), 2) if pd.notna(v) and v > 0 else None
        )
    return runs


def get_weekly_run_volume(df: pd.DataFrame) -> pd.DataFrame:
    runs = get_runs(df)
    if runs.empty or "data" not in runs.columns:
        return pd.DataFrame()
    runs = runs.copy()
    runs["distancia_km"] = _to_float(runs["distancia_km"])
    runs = runs.dropna(subset=["data", "distancia_km"])
    runs["semana"] = runs["data"].dt.to_period("W").apply(lambda p: p.start_time)
    weekly = runs.groupby("semana")["distancia_km"].sum().reset_index()
    weekly.columns = ["Semana", "Distância (km)"]
    return weekly.sort_values("Semana")
