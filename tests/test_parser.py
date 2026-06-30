"""Tests del parser v2 (requieren beautifulsoup4 + lxml instalados)."""
from pathlib import Path

from grupo3.ingesta.parser import parse_html

FIXTURES = Path(__file__).parent / "fixtures"


def _cargar(nombre):
    return (FIXTURES / nombre).read_text(encoding="utf-8")


def test_v2_detecta_meta():
    data = parse_html(_cargar("2025-06-20_diario.html"),
                      ruta_archivo="data/analisis/2025-06-20_diario.html")
    assert data["formato_version"] == 2
    assert data["tipo"] == "diario"          # data-tipo="DIARIO" -> minúscula
    assert data["fecha"] == "2025-06-20"
    assert len(data["recomendaciones"]) == 3


def test_v2_parsea_campos():
    data = parse_html(_cargar("2025-06-20_diario.html"))
    aapl = data["recomendaciones"][0]
    assert aapl["activo"] == "AAPL"
    assert aapl["ticker"] == "AAPL"
    assert aapl["precio_entrada"] == 195.30
    assert aapl["crecimiento_estimado"] == 2.5     # limpia '+' y '%'
    assert aapl["confianza"] == 80
    assert aapl["riesgo"] == "Moderado"


def test_v2_riesgo_y_signo_negativo():
    data = parse_html(_cargar("2025-06-20_diario.html"))
    tsla = data["recomendaciones"][2]
    assert tsla["riesgo"] == "Muy Riesgosa"
    assert tsla["crecimiento_estimado"] == -4.0    # conserva el signo


def test_tipo_fecha_desde_nombre_archivo():
    # HTML sin data-* (simula v1): tipo/fecha salen del nombre de archivo.
    data = parse_html("<html><body>sin datos estructurados</body></html>",
                      ruta_archivo="data/analisis/2025-05-01_semanal.html")
    assert data["formato_version"] == 1
    assert data["tipo"] == "semanal"
    assert data["fecha"] == "2025-05-01"
