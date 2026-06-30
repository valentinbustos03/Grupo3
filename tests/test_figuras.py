"""Figuras Plotly del dashboard (equity y calibración, sin red)."""
import pandas as pd
import plotly.graph_objects as go

from grupo3.dashboard import figuras


def test_fig_equity_dos_trazas():
    df = pd.DataFrame(
        {"fecha": ["2026-06-01", "2026-06-02"],
         "recos_acum": [0.0, 1.5], "sp500_acum": [0.0, 0.8]}
    )
    fig = figuras.fig_equity(df)
    assert isinstance(fig, go.Figure)
    nombres = {t.name for t in fig.data}
    assert "IA" in nombres and "S&P 500" in nombres
    assert fig.layout.paper_bgcolor == "rgba(0,0,0,0)"


def test_fig_equity_vacio_no_rompe():
    fig = figuras.fig_equity(pd.DataFrame(columns=["fecha", "recos_acum", "sp500_acum"]))
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 0


def test_fig_calibracion_dos_series():
    df = pd.DataFrame(
        {"tramo": ["80–90", "90–100"], "conf_media": [85.0, 95.0],
         "aciertos_pct": [50.0, 100.0], "n": [2, 1]}
    )
    fig = figuras.fig_calibracion(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.layout.barmode == "group"
