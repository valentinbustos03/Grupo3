"""Smoke de las páginas: import + render callable, y la app entera vía AppTest."""
import importlib
import os

from streamlit.testing.v1 import AppTest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_panel_tiene_render():
    mod = importlib.import_module("grupo3.dashboard.panel")
    assert callable(mod.render)


def test_metodologia_tiene_render():
    mod = importlib.import_module("grupo3.dashboard.metodologia")
    assert callable(mod.render)


def test_app_expone_render():
    mod = importlib.import_module("grupo3.dashboard.app")
    assert callable(mod.render)


def test_app_corre_sin_excepcion():
    """Ejecuta streamlit_app.py completo (st.navigation incluido) y verifica que
    no lanza excepción. Cubre la colisión de url_path entre las dos páginas
    `render` (ambas funciones se llaman igual)."""
    at = AppTest.from_file(os.path.join(_ROOT, "streamlit_app.py"), default_timeout=120)
    at.run()
    assert not at.exception, at.exception
