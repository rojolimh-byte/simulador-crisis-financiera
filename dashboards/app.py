"""
Dashboard de Streamlit para el simulador de contagio financiero.
"""

import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.model import FinancialNetwork

st.set_page_config(page_title="Simulador de Crisis Financiera", layout="wide")
st.title("🏦 Simulador de Contagio Financiero")
st.markdown("Modelo de agentes: una red de bancos donde un shock inicial puede desencadenar una crisis sistémica.")

# Sidebar de parámetros
st.sidebar.header("Parámetros")
n_banks = st.sidebar.slider("Cantidad de bancos", 5, 50, 20)
shock_size = st.sidebar.slider("Magnitud del shock inicial", 0.1, 1.0, 0.3, 0.05)
bailout = st.sidebar.checkbox("Activar rescate estatal (bailout)")

if st.sidebar.button("Ejecutar simulación"):
    model = FinancialNetwork(n_banks=n_banks, shock_size=shock_size, bailout=bailout)
    states = model.run()

    # Construir visualización de la red
    G = model.G
    pos = nx.spring_layout(G, seed=42)

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="#888"),
        hoverinfo="none"
    )

    node_x, node_y, node_color, node_text = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        alive = states[node] == "alive"
        node_color.append("green" if alive else "red")
        node_text.append(f"Banco {node}: {'Sano' if alive else 'Quebrado'}")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=20, color=node_color, line=dict(width=2, color="white")),
        text=[str(n) for n in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text"
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Red bancaria después del contagio",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    st.plotly_chart(fig, use_container_width=True)

    alive_count = sum(1 for s in states.values() if s == "alive")
    dead_count = n_banks - alive_count
    st.metric("Bancos sanos", alive_count)
    st.metric("Bancos quebrados", dead_count)

    if dead_count > n_banks / 2:
        st.error("⚠️ Crisis sistémica: más de la mitad de los bancos quebraron.")
    elif dead_count > 0:
        st.warning("Contagio parcial: algunos bancos quebraron.")
    else:
        st.success("Sistema estable: ningún banco quebró.")
