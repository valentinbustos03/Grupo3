"""Página Metodología: documenta rutinas, qué se analiza y cómo se planteó."""
from __future__ import annotations

import streamlit as st

from grupo3 import config


def _seccion(titulo: str, cuerpo_html: str) -> None:
    st.markdown(
        f'<div class="glass doc"><h2>{titulo}</h2>{cuerpo_html}</div>',
        unsafe_allow_html=True,
    )


def render() -> None:
    st.markdown(
        '<div class="glass"><p class="masthead-kicker">Grupo 3 · Documentación</p>'
        '<h1 class="masthead-title">Metodología</h1>'
        '<p class="masthead-sub">Cómo se generan los análisis, qué se mide y cómo '
        'se construyó este dashboard.</p></div>',
        unsafe_allow_html=True,
    )

    _seccion(
        "El experimento",
        "<p>Usamos Claude (IA) para generar análisis de mercado y medimos qué tan "
        "bien le va frente al <b>S&amp;P 500</b>. Cada análisis produce "
        "<b>3 recomendaciones</b> con estructura fija:</p>"
        "<ul><li>Activo / ticker</li><li>Precio de entrada</li>"
        "<li>Factores / catalizadores</li><li>% de crecimiento estimado</li>"
        "<li>Nivel de confianza (%)</li>"
        "<li>Riesgo (5 niveles): Muy segura, Segura, Moderado, Riesgosa, Muy Riesgosa</li></ul>"
        "<p>Se evalúa en tres horizontes: <b>diario</b> (open vs close del día), "
        "<b>semanal</b> (lunes vs cierre del viernes) y <b>mensual</b> "
        "(primer vs último día hábil).</p>",
    )

    _seccion(
        "La rutina generadora",
        "<p>Una <b>Claude Code Routine</b> corre en la nube de Anthropic (fuera de "
        "este proyecto) y, por cada análisis:</p>"
        "<ul><li>Commitea el HTML al repo de GitHub → <b>única fuente de verdad</b>.</li>"
        "<li>Crea un draft en Gmail como aviso (no es fuente de datos).</li></ul>"
        "<p>El dashboard <b>no depende de ninguna PC encendida ni de Gmail</b>: "
        "lee siempre del repo.</p>",
    )

    _seccion(
        "Arquitectura",
        '<p class="flow">Claude Routine (nube)<br>'
        f"&nbsp;&nbsp;└─ commit HTML → GitHub <code>{config.GITHUB_OWNER}/"
        f"{config.GITHUB_REPO}</code> · carpeta <code>{config.DATA_DIR}</code><br>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─ ingesta (parser v1/v2) → SQLite<br>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─ precios + S&amp;P 500 "
        "(yfinance) → alpha / veredicto<br>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─ "
        "dashboard Streamlit (esta app)</p>",
    )

    _seccion(
        "Cómo se calcula el veredicto",
        "<p>Todo veredicto es <b>relativo al S&amp;P 500</b>:</p>"
        "<p class='flow'>ret_activo = (cierre/entrada − 1)·100<br>"
        "ret_sp500&nbsp; = (cierre/entrada − 1)·100&nbsp;&nbsp;(mismo período)<br>"
        "alpha&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; = ret_activo − ret_sp500</p>"
        f"<p><span class='badge' style='color:#4ade80;border-color:#4ade8066;"
        f"background:#4ade801f'>GANÓ</span> si alpha &gt; 0 · "
        f"<span class='badge' style='color:#f87171;border-color:#f8717166;"
        f"background:#f871711f'>PERDIÓ</span> si alpha &lt; 0 · "
        f"<b>NEUTRO</b> si |alpha| &lt; {config.UMBRAL_NEUTRO}%.</p>"
        "<p>También se guarda el <b>acierto absoluto</b> (ret_activo &gt; 0) y si la "
        "<b>dirección</b> estimada coincidió con la real (calibración del modelo).</p>",
    )

    _seccion(
        "Normalización del candlestick",
        "<p>La vela comparativa lleva el OHLC a <b>base 100 en la apertura del "
        "período</b>: <code>serie / Open[día 1] · 100</code>. Una acción de ~$195 y "
        "el índice en ~5000 puntos no son comparables en escala directa; con base 100 "
        "ambas arrancan igual y se ve quién subió/bajó más en %.</p>",
    )

    _seccion(
        "Registro de formato (v1 / v2)",
        f"<p>Cada análisis guarda su <code>formato_version</code>: <b>v2</b> es el HTML "
        f"estandarizado con atributos <code>data-*</code> (desde "
        f"{config.FECHA_CORTE_EXPERIMENTAL}); <b>v1</b> son históricos de texto libre, "
        "parseados best-effort (campos faltantes quedan en null). Es solo un "
        "<b>registro informativo</b> del formato original: no separa ni filtra las "
        "métricas.</p>",
    )

    _seccion(
        "Cómo se planteó el proyecto (etapas)",
        "<p>Se construyó por etapas:</p>"
        "<ul><li><b>1 · Ingesta:</b> leer HTML del repo, parsear 3 recos, persistir en "
        "SQLite (idempotente por fecha+tipo).</li>"
        "<li><b>2 · Precios + veredicto:</b> yfinance trae cierres y S&amp;P 500; se "
        "calcula alpha y veredicto, tolerando feriados y datos faltantes.</li>"
        "<li><b>2b · Candlestick:</b> vela comparativa normalizada (pedido del profesor).</li>"
        "<li><b>3 · Dashboard:</b> esta interfaz (KPIs, figuras, tabla, esta doc).</li>"
        "<li><b>4 · Automatización:</b> deploy en Streamlit Cloud, refresh end-to-end.</li></ul>",
    )

    _seccion(
        "Deploy y datos",
        "<p>El dashboard se hostea en <b>Streamlit Community Cloud</b> (gratis, siempre "
        "encendido). Como el contenedor puede reiniciarse, la SQLite se trata como "
        "<b>efímera</b>: si arranca vacía, se reconstruye desde el repo + yfinance. El "
        "botón <b>Actualizar</b> vuelve a leer el repo, trae precios pendientes y "
        "recalcula veredictos.</p>",
    )
