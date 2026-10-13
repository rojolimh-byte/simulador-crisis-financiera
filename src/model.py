"""
Simulador de contagio financiero basado en agentes.
Modela una red de bancos donde un shock inicial puede propagarse en cadena.
"""

import random
import networkx as nx
from mesa import Agent, Model
from mesa.time import RandomActivation


class Bank(Agent):
    """Un banco en la red financiera."""

    def __init__(self, unique_id, model, capital, exposures):
        super().__init__(unique_id, model)
        self.capital = capital
        self.exposures = exposures  # dict: {banco_id: monto}
        self.alive = True

    def step(self):
        if not self.alive:
            return
        # Si el capital cae por debajo de cero, el banco quiebra
        if self.capital < 0:
            self.alive = False
            self.propagate_loss()

    def propagate_loss(self):
        """Transmite las exposiciones a los bancos conectados."""
        for other_id, amount in self.exposures.items():
            other = self.model.schedule._agents[other_id]
            if other.alive:
                other.capital -= amount


class FinancialNetwork(Model):
    """Red de bancos interconectados con contagio financiero."""

    def __init__(self, n_banks=20, shock_size=0.3, bailout=False):
        super().__init__()
        self.num_agents = n_banks
        self.schedule = RandomActivation(self)
        self.bailout = bailout
        self.shock_size = shock_size

        # Crear red de bancos (grafo aleatorio)
        self.G = nx.erdos_renyi_graph(n_banks, 0.15, seed=42)

        # Crear agentes (bancos)
        for i in range(n_banks):
            capital = random.uniform(80, 120)
            exposures = {}
            for j in self.G.neighbors(i):
                exposures[j] = random.uniform(5, 20)
            bank = Bank(i, self, capital, exposures)
            self.schedule.add(bank)

        # Aplicar shock inicial al banco 0
        self.schedule._agents[0].capital -= self.shock_size * 100

    def step(self):
        self.schedule.step()

    def get_state(self):
        """Devuelve el estado actual de la red para visualización."""
        states = {}
        for i in range(self.num_agents):
            bank = self.schedule._agents[i]
            states[i] = "alive" if bank.alive else "dead"
        return states

    def run(self, max_steps=50):
        """Corre la simulación hasta que no haya más contagio o max_steps."""
        for _ in range(max_steps):
            before = sum(1 for a in self.schedule._agents if a.alive)
            self.step()
            after = sum(1 for a in self.schedule._agents if a.alive)
            if before == after:
                break
        return self.get_state()
