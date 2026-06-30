"""Entrypoint del dashboard: tema + navegación de 2 páginas.

Importado por ``streamlit_app.py`` (convención de Streamlit Cloud).
"""
from __future__ import annotations

import streamlit as st

from grupo3.dashboard import metodologia, panel
from grupo3.dashboard.theme import inject_css


def render() -> None:
    st.set_page_config(
        page_title="Grupo3 · IA vs S&P 500",
        page_icon="📈",
        layout="wide",
    )
    inject_css()

    # url_path explícito: ambas funciones se llaman ``render``, y Streamlit infiere
    # el pathname del nombre del callable -> sin esto colisionan ("URL pathnames
    # must be unique").
    nav = st.navigation([
        st.Page(panel.render, title="Panel", icon="📊",
                url_path="panel", default=True),
        st.Page(metodologia.render, title="Metodología", icon="📖",
                url_path="metodologia"),
    ])
    nav.run()
