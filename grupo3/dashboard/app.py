"""Render del dashboard (placeholder Etapas 1-2).

La estética fintech completa (KPI cards, equity curve, badges) es la Etapa 3 y
se construye sobre el mockup aprobado. Por ahora valida el pipeline de punta a
punta: ingesta del repo -> precios yfinance -> alpha/veredicto -> métricas.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from grupo3 import config, db
from grupo3.analisis import metricas, recalcular
from grupo3.ingesta import ingestar


@st.cache_resource
def _conn():
    """Conexión SQLite cacheada por sesión del contenedor."""
    conn = db.connect()
    db.init_db(conn)
    return conn


def render() -> None:
    st.set_page_config(
        page_title="Grupo3 · Análisis bursátil IA",
        page_icon="📈",
        layout="wide",
    )
    st.title("📈 Grupo3 — Análisis bursátil IA vs S&P 500")
    st.caption(
        f"Fuente de verdad: github.com/{config.GITHUB_OWNER}/{config.GITHUB_REPO} "
        f"· carpeta `{config.DATA_DIR}` · (Etapas 1-2: ingesta + veredicto)"
    )

    conn = _conn()

    if st.button("🔄 Actualizar (repo → precios → veredictos)", type="primary"):
        with st.spinner("Leyendo HTML del repo e ingiriendo..."):
            r_ing = ingestar(conn)
        with st.spinner("Trayendo precios (yfinance) y calculando alpha/veredictos..."):
            r_cal = recalcular(conn)
        st.success(
            f"Ingesta — vistos {r_ing['vistos']}, nuevos {r_ing['nuevos']}, "
            f"actualizados {r_ing['actualizados']}, sin cambios {r_ing['sin_cambios']}  ·  "
            f"Cálculo — ok {r_cal['ok']}, sin dato {r_cal['sin_dato']}, "
            f"pendientes {r_cal['pendientes']}"
        )
        for err in r_ing["errores"]:
            st.warning(err)

    analisis = pd.read_sql_query(
        "SELECT id, fecha, tipo, formato_version, ruta_archivo FROM analisis "
        "ORDER BY fecha DESC, tipo",
        conn,
    )
    if analisis.empty:
        st.info(
            "No hay análisis todavía. Cargá HTML en "
            f"`{config.DATA_DIR}` del repo y tocá **Actualizar**."
        )
        return

    # KPIs rápidos (sobre recomendaciones con datos resueltos).
    df_ok = metricas.df_recomendaciones(conn)
    k = metricas.kpis(df_ok)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recos medidas", k["n"])
    c2.metric("Hit rate vs S&P", "—" if k["hit_rate"] is None else f"{k['hit_rate']:.0f}%")
    c3.metric("Alpha promedio", "—" if k["alpha_promedio"] is None else f"{k['alpha_promedio']:+.2f}%")
    c4.metric("Alpha acumulado", "—" if k["alpha_acumulado"] is None else f"{k['alpha_acumulado']:+.2f}%")

    st.subheader("Análisis ingeridos")
    st.dataframe(analisis, use_container_width=True, hide_index=True)

    st.subheader("Recomendaciones")
    recos = pd.read_sql_query(
        """SELECT a.fecha, a.tipo, r.activo, r.ticker, r.riesgo,
                  r.crecimiento_estimado, r.confianza,
                  r.ret_activo, r.ret_sp500, r.alpha, r.veredicto, r.estado_dato
           FROM recomendaciones r JOIN analisis a ON a.id = r.analisis_id
           ORDER BY a.fecha DESC, a.tipo""",
        conn,
    )
    st.dataframe(recos, use_container_width=True, hide_index=True)
