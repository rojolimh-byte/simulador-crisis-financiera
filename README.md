# Simulador de Contagio Financiero

Simulador de crisis financieras basado en agentes (ABM): una red de bancos conectados donde un shock inicial puede propagarse en cadena y desencadenar una crisis sistémica.

## Qué hace

- Modela un sistema bancario como una **red de bancos interconectados**
- Aplica un **shock inicial** a un banco (pérdida repentina de capital)
- Si un banco quiebra, **transmite pérdidas a sus conexiones** (contagio)
- Permite comparar escenarios: shock bajo (crisis contenida) vs. shock alto (efecto dominó)

## Cómo funciona

Cada banco tiene:
- Un **capital inicial**
- **Exposiciones** hacia otros bancos (préstamos interbancarios)

Cuando un banco pierde más capital del que tiene, quiebra y transmite el valor de sus exposiciones a sus conexiones, que pueden quebrar a su vez — generando un **efecto dominó**.

## Instalación y ejecución

```bash
git clone [https://github.com/rojolimh-byte/simulador-crisis-financiera.git](https://github.com/rojolimh-byte/simulador-crisis-financiera.git)
cd simulador-crisis-financiera
pip install -r requirements.txt
streamlit run dashboards/app.py
```

## Dashboard

El dashboard permite ajustar:
- Cantidad de bancos
- Magnitud del shock inicial
- Activar/desactivar un rescate estatal (bailout)

Y visualiza la red bancaria con bancos sanos (verde) y quebrados (rojo).

## Limitaciones

Este es un **modelo ilustrativo con parámetros sintéticos**. La calibración con datos reales (balances bancarios, exposiciones interbancarias de países LAC) es una extensión futura.

## Tecnologías

- Python
- Mesa (modelado basado en agentes)
- NetworkX (redes)
- Streamlit (dashboard)
