"""Integración offline del cálculo de mercado con un PriceProvider falso.

No usa red: un FakeProvider devuelve OHLC determinista por ticker. Valida la
orquestación recalcular + persistencia + métricas.
"""
import tempfile

import pandas as pd

from grupo3 import db
from grupo3.analisis import recalcular, metricas
from grupo3.precios.provider import PriceProvider


class FakeProvider(PriceProvider):
    """mapa: ticker -> (open, close). Ticker ausente => sin dato (DataFrame vacío)."""

    def __init__(self, mapa):
        self.mapa = mapa

    def ohlc(self, ticker, inicio, fin):
        v = self.mapa.get(ticker)
        if not v:
            return pd.DataFrame()
        o, c = v
        return pd.DataFrame(
            {"Open": [o, o], "High": [max(o, c)] * 2,
             "Low": [min(o, c)] * 2, "Close": [o, c]}
        )


def _conn():
    # Path explícito por test => aislamiento (config.DB_PATH se fija al importar).
    conn = db.connect(tempfile.mktemp(suffix=".db"))
    db.init_db(conn)
    return conn


def _sembrar(conn):
    aid, *_ = db.upsert_analisis(conn, tipo="diario", fecha="2024-01-03",
                                 formato_version=1, ruta_archivo="x", hash_contenido="h")
    db.insert_recomendaciones(conn, aid, [
        {"activo": "AAPL", "ticker": "AAPL", "precio_entrada": None, "factores": None,
         "crecimiento_estimado": 1.0, "confianza": 80, "riesgo": "Moderado"},
        {"activo": "MSFT", "ticker": "MSFT", "precio_entrada": None, "factores": None,
         "crecimiento_estimado": -1.0, "confianza": 60, "riesgo": "Segura"},
        {"activo": "FAKE", "ticker": "ZZZ", "precio_entrada": None, "factores": None,
         "crecimiento_estimado": 2.0, "confianza": 50, "riesgo": "Riesgosa"},
    ])


def test_recalcular_alpha_y_veredicto():
    conn = _conn()
    _sembrar(conn)
    fp = FakeProvider({"AAPL": (100, 103), "MSFT": (200, 198), "^GSPC": (5000, 5050)})
    resumen = recalcular(conn, provider=fp)
    assert resumen == {"procesadas": 3, "ok": 2, "sin_benchmark": 0,
                       "sin_dato": 1, "pendientes": 0}

    df = metricas.df_recomendaciones(conn, solo_ok=False).set_index("ticker")
    # AAPL: +3% vs +1% => alpha +2 => GANO
    assert df.loc["AAPL", "veredicto"] == "GANO"
    assert round(df.loc["AAPL", "alpha"], 6) == 2.0
    assert df.loc["AAPL", "acierto_absoluto"] == 1
    assert df.loc["AAPL", "direccion_coincide"] == 1
    # MSFT: -1% vs +1% => alpha -2 => PERDIO; estimó -1% y bajó => dirección coincide
    assert df.loc["MSFT", "veredicto"] == "PERDIO"
    assert df.loc["MSFT", "acierto_absoluto"] == 0
    assert df.loc["MSFT", "direccion_coincide"] == 1
    # Ticker inexistente => sin dato
    assert df.loc["ZZZ", "estado_dato"] == "sin_dato"


def test_metricas_agregadas():
    conn = _conn()
    _sembrar(conn)
    fp = FakeProvider({"AAPL": (100, 103), "MSFT": (200, 198), "^GSPC": (5000, 5050)})
    recalcular(conn, provider=fp)

    df = metricas.df_recomendaciones(conn)            # solo estado_dato='ok'
    k = metricas.kpis(df)
    assert k["n"] == 2
    assert k["hit_rate"] == 50.0                       # 1 de 2 con alpha>0
    assert round(k["alpha_acumulado"], 6) == 0.0       # +2 y -2

    porr = metricas.performance_por_riesgo(df)
    assert set(porr["riesgo"]) == {"Moderado", "Segura"}

    eq = metricas.equity_curve(df)
    assert list(eq.columns) == ["fecha", "recos_acum", "sp500_acum"]
    assert len(eq) == 1                                # una sola fecha


def test_protocolo_sin_benchmark_dia_cerrado():
    # Día de mercado cerrado: los activos cotizan pero el S&P (y SPY) no.
    conn = _conn()
    _sembrar(conn)
    fp = FakeProvider({"AAPL": (100, 102), "MSFT": (200, 198)})   # sin ^GSPC/SPY
    resumen = recalcular(conn, provider=fp)
    assert resumen["sin_benchmark"] == 2        # AAPL y MSFT: precio sí, S&P no
    assert resumen["sin_dato"] == 1             # ZZZ: ticker inexistente

    # Métricas vs S&P excluyen 'sin_benchmark'.
    df_ok = metricas.df_recomendaciones(conn)            # solo 'ok'
    assert metricas.kpis(df_ok)["n"] == 0

    # La calibración SÍ los incluye (retorno absoluto + dirección disponibles).
    df_cal = metricas.df_recomendaciones(conn, estados=("ok", "sin_benchmark"))
    cal = metricas.calibracion(df_cal).set_index("ticker")
    assert set(cal.index) == {"AAPL", "MSFT"}
    assert cal.loc["AAPL", "acierto_absoluto"] == 1      # +2% subió
    assert cal.loc["AAPL", "direccion_coincide"] == 1    # estimó +1%, subió


def test_idempotencia_recalcular_solo_pendientes():
    conn = _conn()
    _sembrar(conn)
    fp = FakeProvider({"AAPL": (100, 103), "MSFT": (200, 198), "^GSPC": (5000, 5050)})
    recalcular(conn, provider=fp)
    # Segunda corrida solo_pendientes: ok ya no se reprocesan; queda el sin_dato.
    r2 = recalcular(conn, provider=fp, solo_pendientes=True)
    assert r2["procesadas"] == 1                       # solo el ZZZ (sin_dato) se reintenta
