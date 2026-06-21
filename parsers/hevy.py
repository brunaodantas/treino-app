import pandas as pd
import io


def parse_hevy(file):
    try:
        content = file.read() if hasattr(file, "read") else open(file, "rb").read()
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
        return df
    except Exception as e:
        print(f"Erro ao ler Hevy CSV: {e}")
        return None
