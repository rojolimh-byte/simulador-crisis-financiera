"""
Simulador de riesgo sistémico y contagio financiero en América Latina.
Nodos = países. Shocks = eventos globales (Fed, commodities, guerra, clima).
Calibración ilustrativa basada en BIS Consolidated Banking Statistics e IMF FSI.
"""

import networkx as nx

# Países LAC incluidos en la red
COUNTRIES = ["Brasil", "México", "Argentina", "Chile", "Colombia", "Perú"]

# Capital de absorción (proxy: reservas / deuda externa corto plazo, escala 0-100)
# Calibración ilustrativa basada en IMF FSI y datos de reservas
CAPITAL = {
    "Brasil": 75,
    "México": 70,
    "Argentina": 30,
    "Chile": 65,
    "Colombia": 50,
    "Perú": 72,
}

# Matriz de exposiciones (quién le debe a quién, escala relativa)
# Basada en BIS CBS: exposición del país fila hacia el país columna
EXPOSURES = {
    "Brasil":    {"México": 10, "Argentina": 15, "Chile": 8, "Colombia": 6, "Perú": 5},
    "México":    {"Brasil": 12, "Argentina": 5, "Chile": 6, "Colombia": 7, "Perú": 4},
    "Argentina": {"Brasil": 25, "México": 8, "Chile": 5, "Colombia": 4, "Perú": 3},
    "Chile":     {"Brasil": 15, "México": 7, "Argentina": 6, "Colombia": 5, "Perú": 8},
    "Colombia":  {"Brasil": 10, "México": 9, "Argentina": 5, "Chile": 6, "Perú": 4},
    "Perú":      {"Brasil": 12, "México": 6, "Argentina": 4, "Chile": 10, "Colombia": 5},
}

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

    def __init__(self, shock_name, shock_intensity=1.0, bailout=False):
        self.shock_name = shock_name
        self.shock_intensity = shock_intensity
        self.bailout = bailout

        self.countries = {}
        for name in COUNTRIES:
            self.countries[name] = Country(name, CAPITAL[name], EXPOSURES[name])

        # Aplicar shock inicial
        shock = SHOCKS[shock_name]
        for country_name, base_impact in shock["impacto"].items():
            self.countries[country_name].capital -= base_impact * shock_intensity

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

    def build_graph(self):
        """Construye el grafo para visualización."""
        G = nx.DiGraph()
        for name in COUNTRIES:
            G.add_node(name)
        for source, targets in EXPOSURES.items():
            for target, amount in targets.items():
                G.add_edge(source, target, weight=amount)
        return G
