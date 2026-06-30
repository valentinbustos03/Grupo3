"""Figuras Plotly tematizadas (Liquid Glass). Las puras no usan red."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from grupo3.dashboard import theme


def fig_equity(df_equity: pd.DataFrame) -> go.Figure:
    """Curva de retorno acumulado: recomendaciones de IA vs S&P 500."""
    fig = go.Figure()
    if df_equity is not None and not df_equity.empty:
        fig.add_trace(go.Scatter(
            x=df_equity["fecha"], y=df_equity["recos_acum"], name="IA",
            mode="lines", line={"color": theme.VERDE, "width": 2.6},
            fill="tozeroy", fillcolor=theme.rgba(theme.VERDE, 0.10),
        ))
        fig.add_trace(go.Scatter(
            x=df_equity["fecha"], y=df_equity["sp500_acum"], name="S&P 500",
            mode="lines", line={"color": theme.CIAN, "width": 2, "dash": "dot"},
        ))
    fig.update_layout(**theme.plotly_layout())
    fig.update_layout(yaxis_title="Retorno acumulado (%)")
    return fig


def fig_calibracion(df_tramos: pd.DataFrame) -> go.Figure:
    """Confianza declarada vs aciertos reales, por tramo de confianza."""
    fig = go.Figure()
    if df_tramos is not None and not df_tramos.empty:
        fig.add_trace(go.Bar(
            x=df_tramos["tramo"], y=df_tramos["conf_media"],
            name="Confianza declarada", marker_color=theme.rgba(theme.VIOLETA, 0.6),
        ))
        fig.add_trace(go.Bar(
            x=df_tramos["tramo"], y=df_tramos["aciertos_pct"],
            name="Aciertos reales", marker_color=theme.VERDE,
        ))
    fig.update_layout(**theme.plotly_layout())
    fig.update_layout(barmode="group", yaxis_title="%",
                      xaxis_title="Tramo de confianza declarada")
    return fig


def fig_candlestick(ticker, tipo, fecha, veredicto=None, provider=None) -> go.Figure:
    """Vela comparativa normalizada base 100 (envuelve build_candlestick)."""
    from grupo3.analisis import build_candlestick  # import perezoso (toca yfinance)

    fig = build_candlestick(ticker, tipo, fecha, veredicto=veredicto, provider=provider)
    fig.update_layout(**theme.plotly_layout())
    return fig
