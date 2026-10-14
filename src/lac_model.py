"""
Simulador de riesgo sistémico y contagio financiero en América Latina.
Nodos = países. Shocks = eventos globales (Fed, commodities, guerra, clima).

Calibración basada en datos:
- Capital: ratios reales FMI FSI — capital regulatorio sobre activos ponderados por riesgo (CAR, % RWA)
- Umbral de crisis: 8% (mínimo regulatorio Basilea sobre RWA)
- Shock directo: 1-4.5 pp, consistente con estrés severo (Fed/ECB/IMF: 2.5-4 pp)
- Vulnerabilidad diferenciada: multiplicador basado en spreads EMBI (CEPAL, abr-2024)
- Contagio por cartera común: países sistémicos propagan más al entrar en crisis
- Contagio bilateral: exposiciones BIS normalizadas por PIB del receptor (FMI WEO 2024)
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

# PIB nominal 2024, miles de millones USD (FMI WEO)
GDP_BUSD = {
    "Brasil": 2170.0,
    "México": 1830.0,
    "Argentina": 637.2,
    "Chile": 330.2,
    "Colombia": 420.5,
    "Perú": 295.2,
}

# Umbral de crisis: mínimo regulatorio de capital (Basilea)
CRISIS_THRESHOLD = 8.0

# Coeficiente de transmisión del contagio bilateral
CONTAGION_PASSTHROUGH = 1.0

# Vulnerabilidad macro diferenciada: multiplicador sobre el shock directo,
# derivado de los spreads EMBI (CEPAL, abr-2024):
# Argentina 1215bp, México 309, Colombia 303, Brasil 202, Perú 160, Chile 121.
VULNERABILIDAD_MACRO = {
    "Argentina": 3.0,
    "México": 1.5,
    "Colombia": 1.5,
    "Brasil": 1.2,
    "Perú": 1.0,
    "Chile": 1.0,
}

# Contagio por cartera común: golpe (pp de capital) al resto de la región
# cuando este país entra en crisis. Basado en evidencia de spillovers.
PORTFOLIO_CONTAGION_PP = {
    "Brasil": 1.5,
    "México": 1.5,
    "Argentina": 2.0,
    "Chile": 0.5,
    "Perú": 0.5,
    "Colombia": 0.5,
}

# Shocks: impacto directo base en puntos porcentuales del CAR.
SHOCKS = {
    "Suba de tasas de la Fed": {
        "descripcion": "Endurecimiento global: fuga de capitales, devaluación, spreads más altos",
        "impacto": {"Argentina": 4.0, "Brasil": 2.5, "México": 2.0, "Chile": 2.0, "Colombia": 3.0, "Perú": 2.0},
    },
    "Caída de precios de commodities": {
        "descripcion": "Menos divisas y recaudación para exportadores (cobre, petróleo, soja)",
        "impacto": {"Chile": 3.5, "Perú": 3.0, "Colombia": 3.0, "Brasil": 2.5, "México": 1.0, "Argentina": 2.0},
    },
    "Turbulencia financiera global": {
        "descripcion": "Menor acceso a financiamiento externo y spreads más altos",
        "impacto": {"Argentina": 4.5, "Brasil": 3.0, "México": 2.5, "Chile": 2.5, "Colombia": 3.5, "Perú": 2.5},
    },
    "Riesgo climático (huracán/sequía)": {
        "descripcion": "Pérdidas directas en bancos y aseguradoras de zonas afectadas",
        "impacto": {"México": 2.5, "Colombia": 2.0, "Brasil": 1.5, "Argentina": 1.0, "Chile": 1.0, "Perú": 1.0},
    },
}


class Country:
    """Un país en la red financiera LAC."""

    def __init__(self, name, capital, exposures):
        self.name = name
        self.capital = capital          # capital regulatorio (CAR, % RWA)
        self.exposures = exposures      # dict {destino: exposicion en millones USD}
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
            self.countries[name] = Country(name, CAPITAL[name], EXPOSURES.get(name, {}))

        # Shock directo: impacto base × vulnerabilidad macro × intensidad × ruido
        shock = SHOCKS[shock_name]
        for country_name, base_impact in shock["impacto"].items():
            ruido = np.random.normal(loc=1.0, scale=0.3)
            ruido = max(0.2, min(2.0, ruido))
            vulnerabilidad = VULNERABILIDAD_MACRO.get(country_name, 1.0)
            impacto_pp = base_impact * vulnerabilidad * shock_intensity * ruido
            self.countries[country_name].capital -= impacto_pp

        # Rescate regional: inyección de 2 pp de capital a todos
        if bailout:
            for c in self.countries.values():
                c.capital += 2.0

    def _contagion_loss_pp(self, exposure_musd, destino):
        """Exposición (millones USD) -> pérdida de capital (pp) del destino."""
        gdp_musd = GDP_BUSD[destino] * 1000.0
        exposicion_pct_pib = (exposure_musd / gdp_musd) * 100.0
        return exposicion_pct_pib * CONTAGION_PASSTHROUGH

    def step(self):
        """Un paso: detectar crisis (capital < 8%) y propagar por dos canales."""
        newly_in_crisis = [
            c for c in self.countries.values()
            if not c.in_crisis and c.capital < CRISIS_THRESHOLD
        ]

        for country in newly_in_crisis:
            country.in_crisis = True

            # Canal 1: contagio bilateral por exposiciones BIS
            for other_name, exposure in country.exposures.items():
                other = self.countries.get(other_name)
                if other and not other.in_crisis:
                    perdida_pp = self._contagion_loss_pp(exposure, other_name)
                    other.capital -= perdida_pp

            # Canal 2: contagio por cartera común (portfolio contagion)
            golpe = PORTFOLIO_CONTAGION_PP.get(country.name, 0.5)
            for other in self.countries.values():
                if other.name != country.name and not other.in_crisis:
                    other.capital -= golpe

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
        state = self.get_state()
        n_crisis = sum(1 for v in state.values() if v == "en crisis")
        total_capital = sum(c.capital for c in self.countries.values())
        return {"paises_en_crisis": n_crisis, "capital_total": round(total_capital, 1)}

    def build_graph(self):
        G = nx.DiGraph()
        for name in COUNTRIES:
            G.add_node(name)
        for source, targets in EXPOSURES.items():
            for target, amount in targets.items():
                G.add_edge(source, target, weight=amount)
        return G


def run_monte_carlo(n_sims=200, shock_name="Suba de tasas de la Fed",
                    shock_intensity=1.0, bailout=False):
    """Corre n_sims simulaciones con ruido estocástico; devuelve P5/P50/P95."""
    resultados = []
    for _ in range(n_sims):
        net = LACNetwork(
            shock_name=shock_name,
            shock_intensity=shock_intensity,
            bailout=bailout,
            seed=None,
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
