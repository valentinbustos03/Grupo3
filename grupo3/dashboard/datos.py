"""Capa de datos del dashboard: conexión cacheada, filtros y refresh.

La SQLite puede ser efímera en Streamlit Cloud: ``conn`` reconstruye la base
desde el repo + yfinance si arranca vacía. Las lecturas se cachean con
``st.cache_data`` y se invalidan al Actualizar.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from grupo3 import db
from grupo3.analisis import metricas, recalcular
from grupo3.ingesta import ingestar


def aplicar_filtros(df: pd.DataFrame, riesgo: str | None) -> pd.DataFrame:
    """Filtra por nivel de riesgo. 'Todos'/None no filtra. (Puro, testeable.)"""
    if df is None or df.empty or not riesgo or riesgo == "Todos":
        return df
    return df[df["riesgo"] == riesgo]


@st.cache_resource
def conn():
    """Conexión SQLite cacheada. Bootstrap (ingesta + cálculo) si la base está vacía."""
    c = db.connect()
    db.init_db(c)
    if c.execute("SELECT COUNT(*) FROM analisis").fetchone()[0] == 0:
        try:
            ingestar(c)
            recalcular(c)
        except Exception:  # noqa: BLE001 — sin red/sin repo no debe romper el arranque
            pass
    return c


@st.cache_data(show_spinner=False)
def cargar_recos(tipo: str | None = None) -> pd.DataFrame:
    """Recomendaciones resueltas (estado_dato='ok') unidas a su análisis."""
    return metricas.df_recomendaciones(conn(), tipo=tipo, solo_ok=True)


def contar_analisis() -> int:
    return int(conn().execute("SELECT COUNT(*) FROM analisis").fetchone()[0])


def actualizar() -> tuple[dict, dict]:
    """Repo -> precios -> veredictos. Invalida la cache de lectura."""
    c = conn()
    r_ing = ingestar(c)
    r_cal = recalcular(c)
    st.cache_data.clear()
    return r_ing, r_cal
