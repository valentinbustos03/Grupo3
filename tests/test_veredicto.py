"""Tests del cálculo de veredicto (sin dependencias externas)."""
from grupo3.analisis.veredicto import calcular_veredicto


def test_gano_al_indice():
    v = calcular_veredicto(entrada_activo=100, cierre_activo=103,
                           entrada_sp500=5000, cierre_sp500=5050,
                           crecimiento_estimado=2.5)
    assert round(v["ret_activo"], 4) == 3.0
    assert round(v["ret_sp500"], 4) == 1.0
    assert round(v["alpha"], 4) == 2.0
    assert v["veredicto"] == "GANO"
    assert v["acierto_absoluto"] == 1
    assert v["direccion_coincide"] == 1


def test_perdio_contra_indice():
    v = calcular_veredicto(entrada_activo=100, cierre_activo=100.5,
                           entrada_sp500=5000, cierre_sp500=5100)
    assert v["veredicto"] == "PERDIO"          # +0.5% vs +2.0% => alpha -1.5


def test_neutro_dentro_del_umbral():
    v = calcular_veredicto(entrada_activo=100, cierre_activo=101,
                           entrada_sp500=5000, cierre_sp500=5050, umbral=0.1)
    assert v["veredicto"] == "NEUTRO"          # +1% vs +1% => alpha 0


def test_sin_dato_no_rompe():
    v = calcular_veredicto(entrada_activo=100, cierre_activo=None,
                           entrada_sp500=5000, cierre_sp500=5050)
    assert v["estado_dato"] == "sin_dato"
    assert v["veredicto"] is None


def test_direccion_no_coincide():
    # Modelo dijo +3% pero el activo cayó.
    v = calcular_veredicto(entrada_activo=100, cierre_activo=98,
                           entrada_sp500=5000, cierre_sp500=4990,
                           crecimiento_estimado=3.0)
    assert v["direccion_coincide"] == 0
