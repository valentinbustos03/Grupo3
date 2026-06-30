"""Dashboard de análisis bursátil automatizado (experimento comparación IA).

Paquete modular:
- config        : configuración central (repo, benchmark, umbrales, paths).
- db            : esquema SQLite + helpers de persistencia.
- ingesta       : lectura de HTML desde GitHub + parser v1/v2.
- precios       : PriceProvider intercambiable (yfinance) + ventanas por horizonte.
- analisis      : cálculo de alpha/veredicto, métricas agregadas, candlestick.
- dashboard     : UI Streamlit.
"""
