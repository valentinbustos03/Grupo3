"""Builders HTML del dashboard (puros, sin Streamlit)."""
import pandas as pd

from grupo3.dashboard import componentes as c
from grupo3.dashboard import theme


def test_badge_riesgo_usa_color_del_nivel():
    out = c.badge_riesgo("Muy Riesgosa")
    assert "Muy Riesgosa" in out
    assert theme.RIESGO_COLOR["Muy Riesgosa"] in out
    assert "badge" in out


def test_badge_riesgo_none_no_rompe():
    assert c.badge_riesgo(None) == c.badge_riesgo(None)  # determinista
    assert "—" in c.badge_riesgo(None)


def test_badge_veredicto_traduce_y_colorea():
    assert "GANÓ" in c.badge_veredicto("GANO")
    assert theme.VEREDICTO_COLOR["GANO"] in c.badge_veredicto("GANO")
    assert "PERDIÓ" in c.badge_veredicto("PERDIO")


def test_kpi_cards_muestra_valores():
    html = c.kpi_cards(
        {"hit_rate": 62.5, "alpha_acumulado": 4.2, "n": 8,
         "mejor_ticker": "NVDA", "mejor_alpha": 4.5}
    )
    assert "62" in html
    assert "NVDA" in html
    assert "kpi-grid" in html


def test_kpi_cards_con_none_pone_guion():
    html = c.kpi_cards(
        {"hit_rate": None, "alpha_acumulado": None, "n": 0,
         "mejor_ticker": None, "mejor_alpha": None}
    )
    assert "—" in html


def test_tabla_recos_arma_filas_con_badges():
    df = pd.DataFrame(
        {
            "ticker": ["NVDA"], "activo": ["Nvidia"], "precio_entrada": [195.0],
            "crecimiento_estimado": [3.0], "ret_activo": [4.1], "alpha": [1.2],
            "confianza": [85.0], "riesgo": ["Moderado"], "veredicto": ["GANO"],
        }
    )
    html = c.tabla_recos(df)
    assert "NVDA" in html
    assert "ledger" in html
    assert "GANÓ" in html
    assert "Moderado" in html


def test_tabla_recos_vacia_devuelve_estado_vacio():
    html = c.tabla_recos(pd.DataFrame())
    assert "—" in html or "Sin" in html
