"""
Simulador de riesgo sistémico y contagio financiero en América Latina.
Nodos = países. Shocks = eventos globales (Fed, commodities, guerra, clima).
Calibración ilustrativa basada en BIS Consolidated Banking Statistics e IMF FSI.
Incluye análisis Monte Carlo (múltiples corridas con aleatoriedad).
"""

import numpy as np
import pandas as pd
import networkx as nx
from src.data_loader import load_capitals, load_exposures

# Países LAC incluidos en la red
COUNTRIES = ["Brasil", "México", "Argentina", "Chile", "Colombia", "Perú"]

# Capital y exposiciones: se cargan desde data_loader (CSV real si existe, sino ilustrativo)
CAPITAL = load_capitals()
EXPOSURES = load_exposures()

# Definición de shocks: a qué países golpea y con qué intensidad (0-100)
SHOCKS = {
    "Suba de tasas de la Fed": {
        "descripcion": "Endurecimiento global: fuga de capitales, devaluación, spreads más altos",
        "impacto": {"Argentina": 60, "Brasil": 25, "México": 20, "Chile": 20, "Colombia": 30, "Perú": 20},
    },
    "Caída de precios de commodities": {
        "descripcion": "Menos divisas y recaudación para exportadores (cobre, petróleo, soja)",
        "impacto": {"Chile": 55, "Perú": 50, "Colombia": 45, "Brasil": 35, "México": 15, "Argentina": 25},
    },
    "Turbulencia financiera global": {
        "descripcion": "Menor acceso a financiamiento externo y spreads más altos",
        "impacto": {"Argentina": 70, "Brasil": 30, "México": 25, "Chile": 25, "Colombia": 35, "Perú": 25},
    },
    "Riesgo climático (huracán/sequía)": {
        "descripcion": "Pérdidas directas en bancos y aseguradoras de zonas afectadas",
        "impacto": {"México": 40, "Colombia": 30, "Brasil": 20, "Argentina": 15, "Chile": 10, "Perú": 15},
    },
}


class Country:
    """Un país en la red financiera LAC."""

    def __init__(self, name, capital, exposures):
        self.name = name
        self.capital = capital
        self.exposures = exposures
        self.in_crisis = False


class LACNetwork:
    """Red de países LAC con contagio financiero y shocks globales."""

    def __init__(self, shock_name, shock_intensity=1.0, bailout=False, seed=None):
        if seed is not None:
            np.random.seed(seed)

        self.shock_name = shock_name
        self.shock_intensity = shock_intensity
        self.bailout = bailout

        self.countries = {}
        for name in COUNTRIES:
            self.countries[name] = Country(name, CAPITAL[name], EXPOSURES[name])

        # Aplicar shock inicial (con ruido estocástico opcional)
        shock = SHOCKS[shock_name]
        for country_name, base_impact in shock["impacto"].items():
            # Ruido: multiplicador normal truncado (media 1, desvío 0.3)
            ruido = np.random.normal(loc=1.0, scale=0.3)
            ruido = max(0.2, min(2.0, ruido))
            impacto_ajustado = base_impact * shock_intensity * ruido
            self.countries[country_name].capital -= impacto_ajustado

        # Rescate regional: inyección de capital si está activado
        if bailout:
            for c in self.countries.values():
                c.capital += 15

    def step(self):
        """Un paso: detectar crisis y propagar pérdidas a acreedores."""
        newly_in_crisis = [c for c in self.countries.values() if not c.in_crisis and c.capital < 0]
        for country in newly_in_crisis:
            country.in_crisis = True
            for other_name, exposure in country.exposures.items():
                other = self.countries[other_name]
                if not other.in_crisis:
                    other.capital -= exposure
        return len(newly_in_crisis)

    def get_state(self):
        return {name: ("sano" if not c.in_crisis else "en crisis") for name, c in self.countries.items()}

    def run(self, max_steps=20):
        for _ in range(max_steps):
            new_crises = self.step()
            if new_crises == 0:
                break
        return self.get_state()

    def get_summary(self):
        """Resumen de una corrida: nro de países en crisis y capital total restante."""
        state = self.get_state()
        n_crisis = sum(1 for v in state.values() if v == "en crisis")
        total_capital = sum(c.capital for c in self.countries.values())
        return {"paises_en_crisis": n_crisis, "capital_total": round(total_capital, 1)}

    def build_graph(self):
        """Construye el grafo para visualización."""
        G = nx.DiGraph()
        for name in COUNTRIES:
            G.add_node(name)
        for source, targets in EXPOSURES.items():
            for target, amount in targets.items():
                G.add_edge(source, target, weight=amount)
        return G


def run_monte_carlo(n_sims=200, shock_name="Suba de tasas de la Fed",
                    shock_intensity=1.0, bailout=False):
    """
    Corre n_sims simulaciones independientes.
    Cada corrida crea una nueva LACNetwork (que ya incluye ruido estocástico
    en el impacto del shock), la ejecuta y registra el resumen.
    Devuelve DataFrame con P5/P50/P95 de países en crisis y capital total.
    """
    resultados = []
    for _ in range(n_sims):
        net = LACNetwork(
            shock_name=shock_name,
            shock_intensity=shock_intensity,
            bailout=bailout,
            seed=None,  # sin seed fijo -> aleatoriedad real en cada corrida
        )
        net.run()
        resultados.append(net.get_summary())

    df = pd.DataFrame(resultados)
    resumen = pd.DataFrame({
        "P5 (pesimista)": df.quantile(0.05),
        "P50 (mediano)": df.quantile(0.50),
        "P95 (optimista)": df.quantile(0.95),
    })
    return resumen
