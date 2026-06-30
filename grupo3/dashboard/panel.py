"""Página Panel del dashboard (vista principal)."""
from __future__ import annotations

import streamlit as st

from grupo3.analisis import metricas
from grupo3.dashboard import componentes, datos, figuras

_TIPOS = {"Diario": "diario", "Semanal": "semanal", "Mensual": "mensual"}
_RIESGOS = ["Todos", "Muy segura", "Segura", "Moderado", "Riesgosa", "Muy Riesgosa"]


def render() -> None:
    st.markdown(componentes.masthead(), unsafe_allow_html=True)

    # --- Filtros ---
    f1, f2, f3 = st.columns([1.2, 1.2, 1])
    label_tipo = f1.radio("Horizonte", list(_TIPOS), horizontal=True)
    riesgo = f2.selectbox("Nivel de riesgo", _RIESGOS)
    if f3.button("🔄 Actualizar", width="stretch"):
        with st.spinner("Repo → precios → veredictos…"):
            r_ing, r_cal = datos.actualizar()
        st.success(
            f"Ingesta: nuevos {r_ing['nuevos']}, actualizados {r_ing['actualizados']} · "
            f"Cálculo: ok {r_cal['ok']}, sin dato {r_cal['sin_dato']}"
        )

    if datos.contar_analisis() == 0:
        st.markdown(
            componentes.estado_vacio(
                "No hay análisis todavía. Cargá HTML en data/analisis/ del repo "
                "y tocá Actualizar."
            ),
            unsafe_allow_html=True,
        )
        return

    tipo = _TIPOS[label_tipo]
    df = datos.aplicar_filtros(datos.cargar_recos(tipo=tipo), riesgo)

    # --- KPI cards ---
    k = metricas.kpis(df)
    mejor = metricas.mejor_recomendacion(df)
    resumen = {
        "hit_rate": k["hit_rate"], "alpha_acumulado": k["alpha_acumulado"], "n": k["n"],
        "mejor_ticker": mejor["ticker"] if mejor else None,
        "mejor_alpha": mejor["alpha"] if mejor else None,
    }
    st.markdown(componentes.kpi_cards(resumen), unsafe_allow_html=True)

    # --- Fig 1: equity curve ---
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("##### Fig. 1 · Curva de retorno acumulado")
    st.plotly_chart(figuras.fig_equity(metricas.equity_curve(df)),
                    width="stretch", config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Fig 2: candlestick comparativo ---
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("##### Fig. 2 · Vela comparativa normalizada (base 100)")
    if df.empty:
        st.markdown(componentes.estado_vacio("Sin recomendaciones para graficar."),
                    unsafe_allow_html=True)
    else:
        opciones = {
            f"{r.fecha} · {r.ticker or r.activo}": (r.ticker or r.activo, r.tipo,
                                                    r.fecha, r.veredicto)
            for r in df.itertuples()
            if (r.ticker or r.activo)
        }
        sel = st.selectbox("Análisis", list(opciones), key="cs")
        ticker, t_tipo, fecha, veredicto = opciones[sel]
        try:
            fig = figuras.fig_candlestick(ticker, t_tipo, fecha, veredicto=veredicto)
            st.plotly_chart(fig, width="stretch",
                            config={"displayModeBar": False})
        except Exception as e:  # noqa: BLE001 — feriado/sin red no debe romper la vista
            st.markdown(
                componentes.estado_vacio(f"Sin datos de mercado para {ticker}: {e}"),
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Fig 3: calibración ---
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("##### Fig. 3 · Calibración — confianza declarada vs aciertos")
    df_cal = datos.aplicar_filtros(datos.cargar_recos_calibracion(tipo=tipo), riesgo)
    st.plotly_chart(figuras.fig_calibracion(metricas.calibracion_por_tramo(df_cal)),
                    width="stretch", config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Tabla ---
    st.markdown("##### Recomendaciones evaluadas")
    st.markdown(componentes.tabla_recos(df), unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center;color:rgba(255,255,255,.4);font-size:12px;'
        'margin-top:18px">Datos del experimento · no constituye asesoramiento '
        'financiero</p>',
        unsafe_allow_html=True,
    )
