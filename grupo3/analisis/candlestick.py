"""Candlestick comparativo normalizado (Etapa 2b, pedido del profesor).

En un mismo gráfico y eje temporal: vela OHLC del activo recomendado vs vela
OHLC del S&P 500 del mismo período. Se NORMALIZA a base 100 en la apertura del
período (una acción ~$195 y el índice ~5000 pts no son comparables en escala
directa): así ambas arrancan en 100 y se ve quién subió/bajó más en %.

    normalizado = serie / Open[primer día] * 100   (Open, High, Low, Close)

Color del activo según veredicto: verde = le ganó al índice, rojo = perdió.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from grupo3.precios import mercado
from grupo3.precios.provider import PriceProvider, YFinanceProvider

_COLOR_VEREDICTO = {"GANO": "#22c55e", "PERDIO": "#ef4444", "NEUTRO": "#9ca3af"}
_GRIS_BENCH = "#6b7280"
_COLS = ["Open", "High", "Low", "Close"]


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Lleva el OHLC a base 100 en la apertura del período."""
    base = df["Open"].iloc[0]
    return df[_COLS] / base * 100


def _vela(fig, df, nombre, color, opacidad):
    n = _normalizar(df)
    fig.add_trace(
        go.Candlestick(
            x=n.index, open=n["Open"], high=n["High"], low=n["Low"], close=n["Close"],
            name=nombre, opacity=opacidad,
            increasing_line_color=color, decreasing_line_color=color,
            increasing_fillcolor=color, decreasing_fillcolor=color,
        )
    )


def build_candlestick(
    ticker: str,
    tipo: str,
    fecha: str,
    veredicto: str | None = None,
    provider: PriceProvider | None = None,
) -> go.Figure:
    """Figura Plotly con el activo y el S&P 500 normalizados a base 100."""
    provider = provider or YFinanceProvider()
    _, _, df_act = mercado.precios_activo(provider, ticker, tipo, fecha)
    _, _, df_bench, bench_tk = mercado.precios_benchmark(provider, tipo, fecha)

    fig = go.Figure()
    if df_bench is not None and not df_bench.empty:
        _vela(fig, df_bench, f"S&P 500 ({bench_tk})", _GRIS_BENCH, 0.55)
    if df_act is not None and not df_act.empty:
        _vela(fig, df_act, f"{ticker} (reco)",
              _COLOR_VEREDICTO.get(veredicto, "#9ca3af"), 0.95)

    fig.add_hline(y=100, line_dash="dot", line_color="#888",
                  annotation_text="base 100 (apertura)", annotation_position="top left")
    fig.update_layout(
        template="plotly_dark",
        title=f"{ticker} vs S&P 500 — {tipo} {fecha} (base 100 en la apertura)",
        yaxis_title="Índice (apertura = 100)",
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 40, "r": 20, "t": 60, "b": 30},
    )
    return fig
