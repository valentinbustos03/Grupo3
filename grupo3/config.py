"""Configuración central del proyecto.

Valores sensibles (token de GitHub) NO se hardcodean: se leen de
``st.secrets`` (Streamlit Cloud) o de variables de entorno.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Raíz del proyecto -------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

# --- Repo de GitHub: ÚNICA fuente de verdad de los HTML ----------------------
GITHUB_OWNER = "valentinbustos03"
GITHUB_REPO = "Grupo3"
GITHUB_BRANCH = "main"
DATA_DIR = "data/analisis"          # carpeta DENTRO del repo donde se commitean los HTML

# --- Benchmark S&P 500 -------------------------------------------------------
BENCHMARK_TICKER = "^GSPC"          # índice S&P 500 en yfinance
BENCHMARK_FALLBACK = "SPY"          # ETF que replica el S&P 500 (si ^GSPC falla)

# --- Veredicto relativo ------------------------------------------------------
# |alpha| < UMBRAL_NEUTRO (en puntos %) => NEUTRO.
UMBRAL_NEUTRO = 0.1

# --- Corte experimental ------------------------------------------------------
# v2 (formato estandarizado data-*) se implementó a partir del 2026-06-19.
# Análisis con fecha <= 2026-06-18 son históricos v1 (texto libre, best-effort).
# Las métricas se filtran SIEMPRE por formato_version para no mezclar series.
FECHA_CORTE_EXPERIMENTAL = "2026-06-19"

# --- Persistencia ------------------------------------------------------------
# SQLite puede ser efímera en Streamlit Cloud (el contenedor se reinicia): la
# base se reconstruye desde el repo + yfinance. Ver README "Estrategia de datos".
DB_PATH = os.environ.get("GRUPO3_DB", str(ROOT / "grupo3.db"))


def github_token() -> str | None:
    """Token opcional de GitHub (repo privado / evitar rate limit anónimo).

    Orden de búsqueda: st.secrets["GITHUB_TOKEN"] -> env GITHUB_TOKEN -> None.
    Importar streamlit de forma perezosa para no acoplar este módulo a la UI.
    """
    try:
        import streamlit as st  # noqa: PLC0415

        if "GITHUB_TOKEN" in st.secrets:
            return st.secrets["GITHUB_TOKEN"]
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN")
