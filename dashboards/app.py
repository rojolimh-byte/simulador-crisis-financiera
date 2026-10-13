"""
Dashboard de Streamlit: riesgo sistémico y contagio financiero en América Latina.
"""

import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.lac_model import LACNetwork, SHOCKS, COUNTRIES, run_monte_carlo

st.set_page_config(page_title="Riesgo Sistémico LAC", layout="wide")
st.title("🌎 Simulador de Riesgo Sistémico en América Latina")
st.markdown("Modelo de contagio financiero entre países LAC, con shocks globales (Fed, commodities, guerra, clima).")

st.sidebar.header("Escenario de shock")
shock_name = st.sidebar.selectbox("Tipo de shock", list(SHOCKS.keys()))
st.sidebar.info(SHOCKS[shock_name]["descripcion"])
shock_intensity = st.sidebar.slider("Intensidad del shock", 0.5, 2.0, 1.0, 0.1)
bailout = st.sidebar.checkbox("Activar rescate regional (swap lines / bailout)")

if st.sidebar.button("Ejecutar simulación"):
    model = LACNetwork(shock_name=shock_name, shock_intensity=shock_intensity, bailout=bailout)
    states = model.run()
    G = model.build_graph()
    pos = nx.spring_layout(G, seed=42, k=2)

    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1, color="#aaa"),
        hoverinfo="none"
    )

    node_x, node_y, node_color, node_text = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        in_crisis = states[node] == "en crisis"
        node_color.append("red" if in_crisis else "green")
        node_text.append(f"{node}: {'EN CRISIS' if in_crisis else 'Sano'}")

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=35, color=node_color, line=dict(width=2, color="white")),
        text=list(G.nodes()),
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text"
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=f"Red financiera LAC después de: {shock_name}",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    st.plotly_chart(fig, use_container_width=True)

    crisis_count = sum(1 for s in states.values() if s == "en crisis")
    st.metric("Países en crisis", f"{crisis_count} / {len(COUNTRIES)}")

    crisis_countries = [n for n, s in states.items() if s == "en crisis"]
    if crisis_countries:
        st.error(f"⚠️ Países en crisis: {', '.join(crisis_countries)}")
    else:
        st.success("Ningún país entró en crisis con este shock.")

    st.subheader("Detalle por país")
    for name in COUNTRIES:
        c = model.countries[name]
        status = "🔴 En crisis" if c.in_crisis else "🟢 Sano"
        st.write(f"**{name}**: {status} — capital restante: {c.capital:.0f}")

    # --- Monte Carlo ---
    st.subheader("🎲 Análisis Monte Carlo")
    n_sims = st.slider("Cantidad de simulaciones", 50, 500, 200, step=50)

    if st.button("Ejecutar Monte Carlo"):
        with st.spinner(f"Corriendo {n_sims} simulaciones..."):
            resumen_mc = run_monte_carlo(
                n_sims=n_sims,
                shock_name=shock_name,
                shock_intensity=shock_intensity,
                bailout=bailout,
            )

        st.write(f"**Distribución de resultados en {n_sims} simulaciones**")
        st.bar_chart(resumen_mc)
        st.dataframe(resumen_mc.style.format("{:.1f}"))
        st.info(
            "**Cómo leerlo:**\n"
            "- **P5 (pesimista):** en el 5% de los escenarios más malos, el valor fue igual o peor\n"
            "- **P50 (mediano):** el escenario típico (mediana)\n"
            "- **P95 (optimista):** en el 95% de los escenarios, el valor fue igual o mejor"
        )
