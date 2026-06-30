"""Página Panel del dashboard (vista principal)."""
from __future__ import annotations

import streamlit as st

from grupo3.analisis import metricas
from grupo3.dashboard import componentes, datos, figuras

_TIPOS  = {"Diario": "diario", "Semanal": "semanal", "Mensual": "mensual"}
_RIESGOS = ["Todos", "Muy segura", "Segura", "Moderado", "Riesgosa", "Muy Riesgosa"]


def render() -> None:
    # --- Topnav -----------------------------------------------------------
    st.markdown(componentes.topnav("panel"), unsafe_allow_html=True)

    # --- Masthead = UNA tarjeta glass (mockup v2) --------------------------
    mast = st.container(border=True)
    with mast:
        st.markdown('<span class="mh-anchor"></span>', unsafe_allow_html=True)
        col_l, col_r = st.columns([1.7, 1], vertical_alignment="top")
        with col_l:
            st.markdown(componentes.masthead(), unsafe_allow_html=True)
        with col_r:
            st.markdown('<p class="ctl-label">Horizonte</p>', unsafe_allow_html=True)
            label_tipo = st.segmented_control(
                "Horizonte", list(_TIPOS), default="Diario",
                label_visibility="collapsed", key="hz",
            )
        # Controles integrados en el masthead
        st.markdown('<hr class="mh-sep">', unsafe_allow_html=True)
        ctl_l, ctl_r, _ = st.columns([1.5, 1.1, 2.2], vertical_alignment="bottom")
        riesgo     = ctl_l.selectbox("Nivel de riesgo", _RIESGOS, label_visibility="visible")
        actualizar = ctl_r.button("↻  Actualizar", width="stretch")

    tipo = _TIPOS[label_tipo or "Diario"]

    if actualizar:
        with st.spinner("Repo → precios → veredictos…"):
            r_ing, r_cal = datos.actualizar()
        st.success(
            f"Ingesta: {r_ing['nuevos']} nuevos, {r_ing['actualizados']} actualizados · "
            f"Cálculo: {r_cal['ok']} ok, {r_cal['sin_dato']} sin dato"
        )

    if datos.contar_analisis() == 0:
        st.markdown(
            componentes.estado_vacio(
                "No hay análisis todavía. Cargá HTML en data/analisis/ y tocá Actualizar."
            ),
            unsafe_allow_html=True,
        )
        return

    # --- Datos + KPIs -----------------------------------------------------
    df       = datos.aplicar_filtros(datos.cargar_recos(tipo=tipo), riesgo)
    k        = metricas.kpis(df)
    mejor    = metricas.mejor_recomendacion(df)
    alpha_acum   = k["alpha_acumulado"]
    ia_en_ventaja = None if alpha_acum is None else alpha_acum > 0

    # Pill de estado dentro del masthead (col_r, debajo del segmented_control)
    with col_r:
        st.markdown(
            f'<div class="pill-wrap">{componentes.status_pill(ia_en_ventaja)}</div>',
            unsafe_allow_html=True,
        )

    # --- KPI cards --------------------------------------------------------
    resumen = {
        "hit_rate":       k["hit_rate"],
        "alpha_acumulado": alpha_acum,
        "n":              k["n"],
        "mejor_ticker":   mejor["ticker"] if mejor else None,
        "mejor_alpha":    mejor["alpha"] if mejor else None,
    }
    st.markdown(componentes.kpi_cards(resumen), unsafe_allow_html=True)

    # --- Fig 1: equity curve ---------------------------------------------
    with st.container(border=True):
        st.markdown('<span class="gc"></span>', unsafe_allow_html=True)
        st.markdown(
            componentes.chart_header(
                "Curva de retorno acumulado",
                "Retorno compuesto de las recomendaciones de IA frente al S&P 500.",
            ),
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            figuras.fig_equity(metricas.equity_curve(df)),
            width="stretch", config={"displayModeBar": False},
        )

    # --- Fig 2 + Fig 3: candlestick y calibración (lado a lado) ----------
    c2, c3 = st.columns(2, gap="medium")

    with c2:
        with st.container(border=True):
            st.markdown('<span class="gc"></span>', unsafe_allow_html=True)
            if df.empty:
                st.markdown(
                    componentes.chart_header("Vela comparativa normalizada (base 100)"),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    componentes.estado_vacio("Sin recomendaciones para graficar."),
                    unsafe_allow_html=True,
                )
            else:
                opciones = {
                    f"{r.fecha} · {r.ticker or r.activo}": (
                        r.ticker or r.activo, r.tipo, r.fecha, r.veredicto
                    )
                    for r in df.itertuples()
                    if (r.ticker or r.activo)
                }
                sel = st.selectbox("Análisis", list(opciones), key="cs",
                                   label_visibility="collapsed")
                ticker, t_tipo, fecha, veredicto = opciones[sel]
                st.markdown(
                    componentes.chart_header(
                        f"Vela comparativa — {ticker} vs. S&P 500",
                        "OHLC normalizado a base 100 en la apertura del período.",
                    ),
                    unsafe_allow_html=True,
                )
                try:
                    fig = figuras.fig_candlestick(ticker, t_tipo, fecha,
                                                  veredicto=veredicto)
                    st.plotly_chart(fig, width="stretch",
                                    config={"displayModeBar": False})
                except Exception as e:  # noqa: BLE001
                    st.markdown(
                        componentes.estado_vacio(
                            f"Sin datos de mercado para {ticker}: {e}"
                        ),
                        unsafe_allow_html=True,
                    )

    with c3:
        with st.container(border=True):
            st.markdown('<span class="gc"></span>', unsafe_allow_html=True)
            st.markdown(
                componentes.chart_header(
                    "Calibración — confianza vs. aciertos",
                    "Confianza declarada por la IA frente a la tasa de aciertos real.",
                ),
                unsafe_allow_html=True,
            )
            df_cal = datos.aplicar_filtros(
                datos.cargar_recos_calibracion(tipo=tipo), riesgo
            )
            st.plotly_chart(
                figuras.fig_calibracion(metricas.calibracion_por_tramo(df_cal)),
                width="stretch", config={"displayModeBar": False},
            )

    # --- Tabla -----------------------------------------------------------
    with st.container(border=True):
        st.markdown('<span class="gc"></span>', unsafe_allow_html=True)
        st.markdown(componentes.tabla_recos(df), unsafe_allow_html=True)

    st.markdown(
        '<p style="text-align:center; color:rgba(255,255,255,.4); font-size:12px;'
        ' margin-top:18px;">Datos del experimento · no constituye asesoramiento'
        ' financiero</p>',
        unsafe_allow_html=True,
    )
