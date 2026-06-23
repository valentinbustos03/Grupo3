"""Métricas agregadas (Etapa 2). Filtrables por horizonte y formato_version.

Todo se calcula sobre las recomendaciones con estado_dato='ok' (las que tienen
precios resueltos). Las funciones devuelven DataFrames/escalares listos para la UI.
"""
from __future__ import annotations

import sqlite3

import pandas as pd


def df_recomendaciones(
    conn: sqlite3.Connection,
    formato_version: int | None = None,
    tipo: str | None = None,
    solo_ok: bool = True,
) -> pd.DataFrame:
    """Recomendaciones unidas a su análisis, con filtros opcionales."""
    sql = [
        "SELECT a.fecha, a.tipo, a.formato_version, r.activo, r.ticker,",
        "       r.precio_entrada, r.crecimiento_estimado, r.confianza, r.riesgo,",
        "       r.ret_activo, r.ret_sp500, r.alpha, r.veredicto,",
        "       r.acierto_absoluto, r.direccion_coincide, r.estado_dato",
        "FROM recomendaciones r JOIN analisis a ON a.id = r.analisis_id",
    ]
    cond, params = [], []
    if formato_version is not None:
        cond.append("a.formato_version = ?")
        params.append(formato_version)
    if tipo:
        cond.append("a.tipo = ?")
        params.append(tipo)
    if solo_ok:
        cond.append("r.estado_dato = 'ok'")
    if cond:
        sql.append("WHERE " + " AND ".join(cond))
    sql.append("ORDER BY a.fecha, a.tipo")
    return pd.read_sql_query("\n".join(sql), conn, params=params)


def kpis(df: pd.DataFrame) -> dict:
    """KPI cards del resumen: hit rate vs S&P, alpha prom/acum, acierto absoluto."""
    if df.empty:
        return {"n": 0, "hit_rate": None, "alpha_promedio": None,
                "alpha_acumulado": None, "acierto_absoluto": None}
    n = len(df)
    return {
        "n": n,
        "hit_rate": float((df["alpha"] > 0).mean() * 100),       # % que le ganó al índice
        "alpha_promedio": float(df["alpha"].mean()),
        "alpha_acumulado": float(df["alpha"].sum()),
        "acierto_absoluto": float(df["acierto_absoluto"].mean() * 100),
    }


def performance_por_riesgo(df: pd.DataFrame) -> pd.DataFrame:
    """Alpha y hit rate agrupados por nivel de riesgo."""
    if df.empty:
        return pd.DataFrame(columns=["riesgo", "n", "alpha_promedio", "hit_rate"])
    g = df.groupby("riesgo", dropna=False)
    return pd.DataFrame(
        {
            "n": g.size(),
            "alpha_promedio": g["alpha"].mean(),
            "hit_rate": g.apply(lambda x: (x["alpha"] > 0).mean() * 100, include_groups=False),
        }
    ).reset_index()


def calibracion(df: pd.DataFrame) -> pd.DataFrame:
    """Confianza declarada vs acierto real (para scatter/barras de calibración)."""
    cols = ["ticker", "fecha", "confianza", "acierto_absoluto",
            "direccion_coincide", "alpha"]
    presentes = [c for c in cols if c in df.columns]
    return df[presentes].dropna(subset=["confianza"]) if not df.empty else df[presentes]


def equity_curve(df: pd.DataFrame) -> pd.DataFrame:
    """Retorno acumulado de las recos vs S&P 500 en el mismo eje temporal.

    Promedia el retorno de las recos por fecha (cartera equiponderada) y acumula
    de forma compuesta; hace lo mismo con el S&P 500 para comparar dos líneas.
    """
    if df.empty:
        return pd.DataFrame(columns=["fecha", "recos_acum", "sp500_acum"])
    por_fecha = (
        df.groupby("fecha")[["ret_activo", "ret_sp500"]].mean().sort_index()
    )
    recos_acum = (1 + por_fecha["ret_activo"] / 100).cumprod() * 100 - 100
    sp500_acum = (1 + por_fecha["ret_sp500"] / 100).cumprod() * 100 - 100
    return pd.DataFrame(
        {
            "fecha": por_fecha.index,
            "recos_acum": recos_acum.values,
            "sp500_acum": sp500_acum.values,
        }
    )
