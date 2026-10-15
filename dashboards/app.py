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
st.markdown("Modelo agent-based de contagio financiero entre países LAC, con shocks globales (Fed, commodities, guerra, clima) y decisiones endógenas de política.")

st.sidebar.header("Escenario de shock")
shock_name = st.sidebar.selectbox("Tipo de shock", list(SHOCKS.keys()))
st.sidebar.info(SHOCKS[shock_name]["descripcion"])
shock_intensity = st.sidebar.slider("Intensidad del shock", 0.5, 3.0, 1.0, 0.1)
bailout = st.sidebar.checkbox("Activar rescate regional (swap lines / bailout)")

# Ejecutar simulación base y guardar en session_state
if st.sidebar.button("Ejecutar simulación"):
    model = LACNetwork(shock_name=shock_name, shock_intensity=shock_intensity, bailout=bailout)
    states = model.run()
    st.session_state["model"] = model
    st.session_state["states"] = states
    st.session_state["shock_name"] = shock_name
    st.session_state["shock_intensity"] = shock_intensity
    st.session_state["bailout"] = bailout

# Mostrar resultados si hay una simulación en sesión
if "model" in st.session_state:
    model = st.session_state["model"]
    states = st.session_state["states"]
    shock_name = st.session_state["shock_name"]

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
    acciones = model.get_acciones()
    etiqueta_accion = {
        "intervino": "🛡️ Intervino (usó reservas)",
        "pidio_rescate": "🆘 Pidió rescate",
        "fire_sale": "📉 Fire sale (redujo exposición)",
        "mantuvo": "⏸️ Mantuvo",
    }
    for name in COUNTRIES:
        c = model.countries[name]
        status = "🔴 En crisis" if c.in_crisis else "🟢 Sano"
        accion = etiqueta_accion.get(acciones.get(name, "mantuvo"), "⏸️ Mantuvo")
        st.write(f"**{name}**: {status} — capital restante: {c.capital:.0f} — {accion}")

    # --- Monte Carlo (usa session_state para no desaparecer) ---
    st.subheader("🎲 Análisis Monte Carlo")
    n_sims = st.slider("Cantidad de simulaciones", 50, 500, 200, step=50)

    if st.button("Ejecutar Monte Carlo"):
        with st.spinner(f"Corriendo {n_sims} simulaciones..."):
            resumen_mc = run_monte_carlo(
                n_sims=n_sims,
                shock_name=st.session_state["shock_name"],
                shock_intensity=st.session_state["shock_intensity"],
                bailout=st.session_state["bailout"],
            )
        st.session_state["resumen_mc"] = resumen_mc

    # Mostrar resultados de Monte Carlo si existen
    if "resumen_mc" in st.session_state:
        resumen_mc = st.session_state["resumen_mc"]
        st.write(f"**Distribución de resultados en {n_sims} simulaciones**")
        st.bar_chart(resumen_mc)
        st.dataframe(resumen_mc.style.format("{:.1f}"))
        st.info(
            "**Cómo leerlo:**\n"
            "- **P5 (pesimista):** en el 5% de los escenarios más malos, el valor fue igual o peor\n"
            "- **P50 (mediano):** el escenario típico (mediana)\n"
            "- **P95 (optimista):** en el 95% de los escenarios, el valor fue igual o mejor"
        )
else:
    st.info("👈 Configurá el shock en el panel izquierdo y ejecutá la simulación.")
