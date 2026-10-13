"""
Simulador de contagio financiero basado en agentes.
Modela una red de bancos donde un shock inicial puede propagarse en cadena.
"""

import random
import networkx as nx


class Bank:
    """Un banco en la red financiera."""

    def __init__(self, unique_id, capital, exposures):
        self.unique_id = unique_id
        self.capital = capital
        self.exposures = exposures
        self.alive = True


class FinancialNetwork:
    """Red de bancos interconectados con contagio financiero."""

    def __init__(self, n_banks=20, shock_size=0.3, bailout=False):
        self.num_agents = n_banks
        self.bailout = bailout
        self.shock_size = shock_size

        self.G = nx.erdos_renyi_graph(n_banks, 0.15, seed=42)

        self.banks = {}
        for i in range(n_banks):
            capital = random.uniform(80, 120)
            exposures = {}
            for j in self.G.neighbors(i):
                exposures[j] = random.uniform(5, 20)
            self.banks[i] = Bank(i, capital, exposures)

        self.banks[0].capital -= self.shock_size * 100

    def step(self):
        newly_dead = [b for b in self.banks.values() if b.alive and b.capital < 0]
        for bank in newly_dead:
            bank.alive = False
            for other_id, amount in bank.exposures.items():
                other = self.banks[other_id]
                if other.alive:
                    other.capital -= amount
        return len(newly_dead)

    def get_state(self):
        return {i: ("alive" if b.alive else "dead") for i, b in self.banks.items()}

    def run(self, max_steps=50):
        for _ in range(max_steps):
            deaths = self.step()
            if deaths == 0:
                break
        return self.get_state()
