"""
Validación histórica del modelo de riesgo sistémico LAC.

Corre el modelo contra episodios de crisis reales y compara los países
que el modelo predice en crisis contra los que efectivamente entraron en
estrés/crisis según el registro histórico.

Episodios incluidos:
- Argentina 2001-02: crisis de deuda y convertibilidad
- Tensión de mercados emergentes 2018: taper tantrum II, crisis argentina y turca
- Caída de commodities 2014-16: presión sobre exportadores (Brasil, Colombia)

Métrica: tasa de acierto = (verdaderos positivos + verdaderos negativos) / total
"""

from __future__ import annotations

import pandas as pd

from src.lac_model import LACNetwork, COUNTRIES

# Episodios históricos: shock aproximado y países que efectivamente entraron
# en estrés/crisis según el registro (FMI, BIS, literatura de crisis).
EPISODIOS = {
    "Argentina 2001-02 (crisis de deuda)": {
        "shock": "Turbulencia financiera global",
        "intensidad": 3.0,
        "bailout": False,
        "crisis_real": ["Argentina"],
    },
    "Tensión de mercados emergentes 2018": {
        "shock": "Suba de tasas de la Fed",
        "intensidad": 2.0,
        "bailout": False,
        "crisis_real": ["Argentina"],
    },
    "Caída de commodities 2014-16": {
        "shock": "Caída de precios de commodities",
        "intensidad": 2.0,
        "bailout": False,
        "crisis_real": ["Brasil", "Colombia"],
    },
}


def validar_episodio(nombre_episodio: str, n_sims: int = 100) -> dict:
    """
    Corre el modelo n_sims veces para un episodio y evalúa la frecuencia
    de crisis por país contra la crisis real.

    Devuelve:
    - frecuencia de crisis por país (fracción de simulaciones)
    - países predichos en crisis (frecuencia > 0.5)
    - aciertos y errores vs. crisis real
    """
    ep = EPISODIOS[nombre_episodio]
    frecuencias = {pais: 0 for pais in COUNTRIES}

    for _ in range(n_sims):
        net = LACNetwork(
            shock_name=ep["shock"],
            shock_intensity=ep["intensidad"],
            bailout=ep["bailout"],
            seed=None,
        )
        estado = net.run()
        for pais, s in estado.items():
            if s == "en crisis":
                frecuencias[pais] += 1

    frecuencias = {p: f / n_sims for p, f in frecuencias.items()}
    predichos = [p for p, f in frecuencias.items() if f > 0.5]
    reales = set(ep["crisis_real"])

    verdaderos_positivos = len(set(predichos) & reales)
    falsos_positivos = len(set(predichos) - reales)
    falsos_negativos = len(reales - set(predichos))
    verdaderos_negativos = len(COUNTRIES) - verdaderos_positivos - falsos_positivos - falsos_negativos

    acierto = (verdaderos_positivos + verdaderos_negativos) / len(COUNTRIES)

    return {
        "episodio": nombre_episodio,
        "frecuencia_crisis": frecuencias,
        "predichos_en_crisis": predichos,
        "crisis_real": ep["crisis_real"],
        "verdaderos_positivos": verdaderos_positivos,
        "falsos_positivos": falsos_positivos,
        "falsos_negativos": falsos_negativos,
        "tasa_acierto": round(acierto, 2),
    }


def validar_todos(n_sims: int = 100) -> pd.DataFrame:
    """Valida todos los episodios y devuelve un resumen en DataFrame."""
    resultados = [validar_episodio(nombre, n_sims) for nombre in EPISODIOS]
    df = pd.DataFrame([
        {
            "Episodio": r["episodio"],
            "Predichos": ", ".join(r["predichos_en_crisis"]) or "ninguno",
            "Reales": ", ".join(r["crisis_real"]),
            "Aciertos (VP)": r["verdaderos_positivos"],
            "Falsos positivos": r["falsos_positivos"],
            "Falsos negativos": r["falsos_negativos"],
            "Tasa de acierto": r["tasa_acierto"],
        }
        for r in resultados
    ])
    return df


if __name__ == "__main__":
    print(validar_todos(n_sims=100).to_string(index=False))
