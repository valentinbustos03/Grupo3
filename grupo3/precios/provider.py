"""Interfaz de precios intercambiable (``PriceProvider``) + impl yfinance.

Todo el resto del sistema depende de la INTERFAZ, no de yfinance. Si más
adelante se cambia la fuente, sólo se implementa otro PriceProvider.

yfinance: gratis y sin API key (por eso es el default del experimento).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class PriceProvider(ABC):
    """Contrato de un proveedor de precios."""

    @abstractmethod
    def ohlc(self, ticker: str, inicio: str, fin: str) -> pd.DataFrame:
        """OHLC diario en [inicio, fin] (ISO AAAA-MM-DD), índice = fecha.

        Columnas garantizadas: Open, High, Low, Close. DataFrame vacío si no hay
        dato (ticker inexistente, feriado, etc.). NUNCA lanza excepción: el
        pipeline trata el vacío como "sin dato".
        """
        raise NotImplementedError


class YFinanceProvider(PriceProvider):
    """Implementación con yfinance. Import perezoso para no pesar al arranque."""

    def ohlc(self, ticker: str, inicio: str, fin: str) -> pd.DataFrame:
        if not ticker:
            return pd.DataFrame()
        try:
            import logging  # noqa: PLC0415

            import yfinance as yf  # noqa: PLC0415

            # yfinance loguea 404 ruidosos para tickers inexistentes; los tratamos
            # como "sin dato", así que bajamos su nivel de log.
            logging.getLogger("yfinance").setLevel(logging.CRITICAL)

            # end es exclusivo en yfinance: se suma un día al pedir el rango
            # desde la capa de períodos. Acá descargamos tal cual nos pasan.
            df = yf.download(
                ticker,
                start=inicio,
                end=fin,
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if df is None or df.empty:
                return pd.DataFrame()
            # yfinance puede devolver columnas MultiIndex (ticker en nivel 1).
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            cols = [c for c in ("Open", "High", "Low", "Close") if c in df.columns]
            return df[cols]
        except Exception:
            # Sin dato: el pipeline marca "sin_dato", no rompe.
            return pd.DataFrame()
