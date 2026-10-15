# Simulador de Riesgo Sistémico y Contagio Financiero en América Latina

Modelo **agent-based** de riesgo sistémico: una red de países LAC interconectados donde shocks globales (Fed, commodities, clima) pueden propagarse y desencadenar crisis en cascada, con decisiones endógenas de política por país.

## Qué hace

- Modela 6 países LAC (Brasil, México, Argentina, Chile, Colombia, Perú) como **agentes** en una red financiera
- Aplica **shocks globales** con impacto diferenciado por país
- Propaga el contagio por tres canales: exposiciones bilaterales (BIS), cartera común y spreads EMBI
- Cada país-agente **decide** según su estado: intervenir con reservas, pedir rescate, o hacer fire sale
- Incluye **Monte Carlo** (P5/P50/P95) para capturar la cola de riesgo

## Cómo funciona

Cada país-agente tiene:
- **Capital regulatorio** (CAR, % RWA) — FMI FSI
- **Exposiciones bilaterales** hacia otros países — BIS LBS
- **Reservas internacionales** (meses de importación) — FMI WEO
- **Vulnerabilidad macro** derivada del spread EMBI — CEPAL/JP Morgan

### Decisiones endógenas (nivel 5)

| Estado | Decisión | Efecto |
|---|---|---|
| En crisis, reservas ≥ 5 meses | Intervenir | +1.5 pp capital, -2 meses reservas |
| En crisis, reservas < 5 meses | Pedir rescate | +2 pp capital si bailout activo |
| Vecino en crisis, exposición alta | Fire sale | Reduce 30% exposición, amplifica contagio x1.5 |
| Sano, sin vecino en crisis | Mantener | Sin cambio |

### Canales de contagio

1. **Bilateral (BIS):** exposición del país en crisis al receptor, normalizada por PIB del receptor
2. **Cartera común:** golpe fijo (pp) al resto de la región cuando un país entra en crisis
3. **Fire sale:** si el país en crisis redujo exposición, el contagio bilateral se amplifica x1.5 (retroalimentación)

## Instalación y ejecución

```bash
git clone https://github.com/rojolimh-byte/simulador-crisis-financiera.git
cd simulador-crisis-financiera
pip install -r requirements.txt
streamlit run dashboards/app.py
```

## Dashboard

El dashboard permite ajustar:
- Tipo de shock (Fed, commodities, turbulencia, clima)
- Intensidad del shock
- Activar/desactivar rescate regional (swap lines / bailout)
- Cantidad de simulaciones Monte Carlo

Y visualiza la red con países sanos (verde) y en crisis (rojo), más la decisión de cada agente.

## Fuentes de datos

- **Capital regulatorio (CAR):** FMI Financial Soundness Indicators (FSI)
- **PIB, reservas:** FMI World Economic Outlook (WEO)
- **Exposiciones bilaterales:** BIS Locational Banking Statistics (LBS)
- **Spreads EMBI:** JP Morgan EMBI Global, vía CEPAL

## Limitaciones

- Las **exposiciones bilaterales** y los **shocks base** son ilustrativos (no calibrados econométricamente con crisis históricas)
- La **vulnerabilidad macro** usa spreads EMBI reales pero el mapeo a multiplicador es una simplificación
- El modelo es **estático por ronda** (no hay aprendizaje ni adaptación de estrategias entre simulaciones)
- No incluye bancos individuales dentro de cada país (agregación a nivel país)

## Tecnologías

- Python
- NumPy / pandas
- NetworkX (redes)
- Streamlit (dashboard)
