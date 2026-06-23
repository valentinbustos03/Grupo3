"""Tests del extractor histórico v1 (módulo PURO, sin dependencias externas).

Valida la heurística contra los 3 ejemplos reales (texto renderizado de los
HTML viejos). Sólo se exige lo inferible con confianza: ticker, nivel de riesgo
y fecha. El resto queda en None a propósito (best-effort).
"""
from pathlib import Path

from grupo3.ingesta import parser_v1

FX = Path(__file__).parent / "fixtures" / "v1"


def _recos(nombre):
    return parser_v1.extraer_recos_v1((FX / nombre).read_text(encoding="utf-8"))


def _pares(recos):
    return [(r["ticker"], r["riesgo"]) for r in recos]


def test_18jun_exchange_prefix():
    # Formato con "NASDAQ: QQQ" / "NYSE: ACN".
    assert _pares(_recos("2026-06-18_diario.txt")) == [
        ("QQQ", "Segura"),
        ("NVDA", "Moderado"),
        ("ACN", "Riesgosa"),
    ]


def test_11jun_ticker_en_titulo():
    # Sin prefijo de bolsa: ticker es el primer token del título.
    assert _pares(_recos("2026-06-11_diario.txt")) == [
        ("XLE", "Moderado"),
        ("ITA", "Moderado"),
        ("CVX", "Riesgosa"),
    ]


def test_08jun_simbolos_y_emojis():
    assert _pares(_recos("2026-06-08_diario.txt")) == [
        ("XLE", "Moderado"),
        ("GLD", "Segura"),
        ("AMD", "Riesgosa"),
    ]


def test_no_falsos_positivos():
    # ORCL (entre paréntesis), SPCX (ticker: ...) y MU/MRVL/AVGO no deben colarse.
    tickers_11 = {t for t, _ in _pares(_recos("2026-06-11_diario.txt"))}
    assert {"ORCL", "SPCX"}.isdisjoint(tickers_11)
    tickers_08 = {t for t, _ in _pares(_recos("2026-06-08_diario.txt"))}
    assert {"MU", "MRVL", "AVGO"}.isdisjoint(tickers_08)


def test_campos_no_inferibles_quedan_null():
    r = _recos("2026-06-18_diario.txt")[0]
    assert r["precio_entrada"] is None
    assert r["crecimiento_estimado"] is None
    assert r["confianza"] is None


def test_fecha_varios_formatos():
    assert parser_v1.fecha_v1("Jueves, 18 de junio de 2026") == "2026-06-18"
    assert parser_v1.fecha_v1("Fecha 11/06/2026") == "2026-06-11"
    assert parser_v1.fecha_v1("corte 2025-01-01 experimental") == "2025-01-01"
