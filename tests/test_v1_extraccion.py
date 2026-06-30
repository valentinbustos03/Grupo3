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


def test_01jun_diario_titulo_numerado_paren():
    # Formato nuevo: "🥇 1. ARM Holdings (ARM)" — título numerado con (TICKER).
    assert _pares(_recos("2026-06-01_diario.txt")) == [
        ("ARM", "Riesgosa"),
        ("IBM", "Moderado"),
        ("TMHC", "Segura"),
    ]


def test_01jun_semanal_titulo_numerado_paren():
    # Cortito numerado, riesgo en línea aparte ("Clasificación: ✅ Segura").
    assert _pares(_recos("2026-06-01_semanal.txt")) == [
        ("MSFT", "Segura"),
        ("NVDA", "Moderado"),
        ("QQQ", "Muy segura"),
    ]


def test_01jun_mensual_cortito_ticker_inicio():
    # Cortito: ticker al inicio de línea + nombre + riesgo en la misma línea.
    assert _pares(_recos("2026-06-01_mensual.txt")) == [
        ("AVGO", "Moderado"),
        ("APP", "Riesgosa"),
        ("IGV", "Segura"),
    ]


def test_no_falsos_positivos():
    # ORCL (entre paréntesis), SPCX (ticker: ...) y MU/MRVL/AVGO no deben colarse.
    tickers_11 = {t for t, _ in _pares(_recos("2026-06-11_diario.txt"))}
    assert {"ORCL", "SPCX"}.isdisjoint(tickers_11)
    tickers_08 = {t for t, _ in _pares(_recos("2026-06-08_diario.txt"))}
    assert {"MU", "MRVL", "AVGO"}.isdisjoint(tickers_08)


def test_cortito_etiquetado():
    # Formato cortito: "TICKER | etiqueta: valor | ..." -> parseo preciso.
    recos = _recos("2026-06-02_diario.txt")
    assert _pares(recos) == [
        ("AAPL", "Segura"),
        ("MSFT", "Moderado"),
        ("NVDA", "Riesgosa"),
    ]
    aapl = recos[0]
    assert aapl["activo"] == "Apple Inc."
    assert aapl["crecimiento_estimado"] == 2.5
    assert aapl["confianza"] == 80
    assert aapl["precio_entrada"] == 195.30
    # campo omitido en la línea de NVDA -> None
    assert recos[2]["precio_entrada"] is None


def test_confianza_y_crecimiento_en_prosa():
    # Los reportes viejos traen confianza/crecimiento en prosa -> se capturan.
    recos = {r["ticker"]: r for r in _recos("2026-06-18_diario.txt")}
    assert recos["QQQ"]["confianza"] == 78
    assert recos["NVDA"]["confianza"] == 67
    assert recos["ACN"]["confianza"] == 58
    # crecimiento: sólo importa que tome un valor positivo (la dirección).
    assert recos["QQQ"]["crecimiento_estimado"] > 0


def test_precio_en_prosa_queda_null():
    # En prosa el layout del precio es poco fiable -> se deja en None a propósito.
    assert _recos("2026-06-18_diario.txt")[0]["precio_entrada"] is None


def test_fecha_varios_formatos():
    assert parser_v1.fecha_v1("Jueves, 18 de junio de 2026") == "2026-06-18"
    assert parser_v1.fecha_v1("Fecha 11/06/2026") == "2026-06-11"
    assert parser_v1.fecha_v1("corte 2025-01-01 experimental") == "2025-01-01"
