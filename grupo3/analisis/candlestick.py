"""Candlestick comparativo normalizado (Etapa 2b, pedido del profesor).

Dos paneles lado a lado con eje Y compartido (ambos en base 100 = apertura):
izquierda el activo recomendado, derecha el S&P 500.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from grupo3.precios import mercado
from grupo3.precios.provider import PriceProvider, YFinanceProvider

_COLOR_VEREDICTO = {"GANO": "#22c55e", "PERDIO": "#ef4444", "NEUTRO": "#9ca3af"}
_COLOR_BENCH = "#38bdf8"   # cyan para S&P 500
_COLS = ["Open", "High", "Low", "Close"]


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """OHLC a base 100 en la apertura del período."""
    base = df["Open"].iloc[0]
    return df[_COLS] / base * 100


def _add_vela(fig: go.Figure, df: pd.DataFrame, nombre: str, color: str,
              row: int, col: int) -> None:
    n = _normalizar(df)
    fig.add_trace(
        go.Candlestick(
            x=n.index,
            open=n["Open"], high=n["High"], low=n["Low"], close=n["Close"],
            name=nombre, showlegend=False,
            increasing_line_color=color, decreasing_line_color=color,
            increasing_fillcolor=color, decreasing_fillcolor=color,
        ),
        row=row, col=col,
    )


def build_candlestick(
    ticker: str,
    tipo: str,
    fecha: str,
    veredicto: str | None = None,
    provider: PriceProvider | None = None,
) -> go.Figure:
    """Figura Plotly: activo (izq) vs S&P 500 (der), normalizados a base 100."""
    provider = provider or YFinanceProvider()
    _, _, df_act = mercado.precios_activo(provider, ticker, tipo, fecha)
    _, _, df_bench, bench_tk = mercado.precios_benchmark(provider, tipo, fecha)

    color_act = _COLOR_VEREDICTO.get(veredicto, "#9ca3af")

    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        column_widths=[0.5, 0.5],
        horizontal_spacing=0.05,
        subplot_titles=[ticker, f"S&P 500 ({bench_tk})"],
    )

    if df_act is not None and not df_act.empty:
        _add_vela(fig, df_act, ticker, color_act, row=1, col=1)
    if df_bench is not None and not df_bench.empty:
        _add_vela(fig, df_bench, f"S&P 500 ({bench_tk})", _COLOR_BENCH, row=1, col=2)

    fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,.35)",
                  annotation_text="base 100", annotation_position="top left")

    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(
        template="plotly_dark",
        yaxis_title="Base 100 (apertura del período)",
        margin={"l": 44, "r": 16, "t": 36, "b": 30},
    )
    return fig
