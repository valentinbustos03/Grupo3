"""Tokens y CSS del tema (sin Streamlit runtime)."""
from grupo3.dashboard import theme


def test_paleta_riesgo_tiene_los_cinco_niveles():
    for nivel in ["Muy segura", "Segura", "Moderado", "Riesgosa", "Muy Riesgosa"]:
        assert nivel in theme.RIESGO_COLOR
        assert theme.RIESGO_COLOR[nivel].startswith("#")


def test_veredicto_color_mapea_los_tres_estados():
    assert theme.VEREDICTO_COLOR["GANO"] == theme.VERDE
    assert theme.VEREDICTO_COLOR["PERDIO"] == theme.ROJO
    assert theme.VEREDICTO_COLOR["NEUTRO"] == theme.NEUTRO


def test_plotly_layout_transparente():
    lay = theme.plotly_layout()
    assert lay["paper_bgcolor"] == "rgba(0,0,0,0)"
    assert lay["plot_bgcolor"] == "rgba(0,0,0,0)"
    assert "Inter" in lay["font"]["family"]


def test_build_css_incluye_aurora_y_glass():
    css = theme.build_css()
    assert css.strip().startswith("<style>")
    assert "auroraShift" in css
    assert ".glass" in css
    assert theme.FONDO in css
