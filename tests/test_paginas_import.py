"""Smoke: las páginas importan y exponen render() callable (sin ejecutar Streamlit)."""
import importlib


def test_panel_tiene_render():
    mod = importlib.import_module("grupo3.dashboard.panel")
    assert callable(mod.render)


def test_metodologia_tiene_render():
    mod = importlib.import_module("grupo3.dashboard.metodologia")
    assert callable(mod.render)
