"""Resolución de precios de mercado por período (Etapa 2).

Dado (ticker, tipo, fecha) trae el OHLC del horizonte y deriva:
- entrada = Open de la PRIMERA fila con dato del período.
- cierre  = Close de la ÚLTIMA fila con dato del período.
Esto es robusto a feriados/días sin cotización (toma lo que exista en el rango).

El benchmark (S&P 500) usa ^GSPC con fallback a SPY.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from grupo3 import config
from grupo3.precios import periodos
from grupo3.precios.provider import PriceProvider


def _ohlc_periodo(provider: PriceProvider, ticker: str, tipo: str, fecha: str) -> pd.DataFrame:
    inicio, fin = periodos.rango(tipo, fecha)
    # yfinance trata 'end' como EXCLUSIVO: sumamos un día para incluir 'fin'.
    fin_excl = (date.fromisoformat(fin) + timedelta(days=1)).isoformat()
    return provider.ohlc(ticker, inicio, fin_excl)


def _entrada_cierre(df: pd.DataFrame) -> tuple[float | None, float | None]:
    if df is None or df.empty:
        return None, None
    return float(df["Open"].iloc[0]), float(df["Close"].iloc[-1])


def periodo_cerrado(tipo: str, fecha: str, hoy: date | None = None) -> bool:
    """True si el período ya terminó (su último día es <= hoy).

    Evita emitir veredictos sobre períodos en curso (p.ej. un mensual del mes
    actual todavía sin cerrar).
    """
    _, fin = periodos.rango(tipo, fecha)
    return date.fromisoformat(fin) <= (hoy or date.today())


def precios_activo(
    provider: PriceProvider, ticker: str, tipo: str, fecha: str
) -> tuple[float | None, float | None, pd.DataFrame]:
    df = _ohlc_periodo(provider, ticker, tipo, fecha)
    e, c = _entrada_cierre(df)
    return e, c, df


def precios_benchmark(
    provider: PriceProvider, tipo: str, fecha: str
) -> tuple[float | None, float | None, pd.DataFrame, str | None]:
    """Devuelve (entrada, cierre, ohlc, ticker_usado). Prueba ^GSPC y luego SPY."""
    for tk in (config.BENCHMARK_TICKER, config.BENCHMARK_FALLBACK):
        df = _ohlc_periodo(provider, tk, tipo, fecha)
        e, c = _entrada_cierre(df)
        if e is not None and c is not None:
            return e, c, df, tk
    return None, None, pd.DataFrame(), None
