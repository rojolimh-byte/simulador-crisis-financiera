"""
Cargador de datos para el simulador LAC.
Si existen CSVs en /data, usa datos reales; si no, usa calibración ilustrativa.

CSVs esperados:
- data/capitals.csv   -> columnas: pais,capital  ó  pais,capital_ratio
- data/exposures.csv  -> columnas: origen,destino,exposicion
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FALLBACK_CAPITAL = {
    "Brasil": 75, "México": 70, "Argentina": 30,
    "Chile": 65, "Colombia": 50, "Perú": 72,
}

FALLBACK_EXPOSURES = {
    "Brasil":    {"México": 10, "Argentina": 15, "Chile": 8, "Colombia": 6, "Perú": 5},
    "México":    {"Brasil": 12, "Argentina": 5, "Chile": 6, "Colombia": 7, "Perú": 4},
    "Argentina": {"Brasil": 25, "México": 8, "Chile": 5, "Colombia": 4, "Perú": 3},
    "Chile":     {"Brasil": 15, "México": 7, "Argentina": 6, "Colombia": 5, "Perú": 8},
    "Colombia":  {"Brasil": 10, "México": 9, "Argentina": 5, "Chile": 6, "Perú": 4},
    "Perú":      {"Brasil": 12, "México": 6, "Argentina": 4, "Chile": 10, "Colombia": 5},
}


def load_capitals():
    """Devuelve dict {pais: capital}. Acepta 'capital' o 'capital_ratio'."""
    path = os.path.join(DATA_DIR, "capitals.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        col = "capital_ratio" if "capital_ratio" in df.columns else "capital"
        return dict(zip(df["pais"], df[col]))
    return FALLBACK_CAPITAL


def load_exposures():
    """Devuelve dict {origen: {destino: exposicion}}. Usa CSV si existe, sino fallback."""
    path = os.path.join(DATA_DIR, "exposures.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        exposures = {}
        for _, row in df.iterrows():
            exposures.setdefault(row["origen"], {})[row["destino"]] = row["exposicion"]
        return exposures
    return FALLBACK_EXPOSURES


def get_data_source():
    """Indica si se están usando datos reales (CSV) o ilustrativos."""
    has_csv = os.path.exists(os.path.join(DATA_DIR, "capitals.csv")) and \
              os.path.exists(os.path.join(DATA_DIR, "exposures.csv"))
    return "datos reales (CSV)" if has_csv else "calibración ilustrativa"
