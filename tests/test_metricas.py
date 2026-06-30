"""Métricas de presentación del dashboard (sin red)."""
import pandas as pd

from grupo3.analisis import metricas


def _df():
    return pd.DataFrame(
        {
            "ticker": ["NVDA", "AAPL", "TSLA"],
            "activo": ["Nvidia", "Apple", "Tesla"],
            "confianza": [55.0, 85.0, 92.0],
            "acierto_absoluto": [1, 0, 1],
            "direccion_coincide": [1, 0, 1],
            "ret_activo": [3.0, -1.0, 5.0],
            "alpha": [1.2, -0.8, 4.5],
        }
    )


def test_mejor_recomendacion_devuelve_la_de_mayor_alpha():
    m = metricas.mejor_recomendacion(_df())
    assert m["ticker"] == "TSLA"
    assert round(m["alpha"], 2) == 4.5
    assert round(m["ret"], 2) == 5.0


def test_mejor_recomendacion_vacio_es_none():
    vacio = pd.DataFrame({"ticker": [], "alpha": [], "ret_activo": [], "activo": []})
    assert metricas.mejor_recomendacion(vacio) is None


def test_calibracion_por_tramo_agrupa_por_banda():
    out = metricas.calibracion_por_tramo(_df())
    # 55 -> 50–60, 85 -> 80–90, 92 -> 90–100
    fila_alta = out[out["tramo"] == "90–100"].iloc[0]
    assert fila_alta["n"] == 1
    assert fila_alta["aciertos_pct"] == 100.0
    fila_media = out[out["tramo"] == "80–90"].iloc[0]
    assert fila_media["aciertos_pct"] == 0.0


def test_calibracion_por_tramo_vacio_no_rompe():
    vacio = pd.DataFrame({"confianza": [], "acierto_absoluto": []})
    out = metricas.calibracion_por_tramo(vacio)
    assert list(out.columns) == ["tramo", "conf_media", "aciertos_pct", "n"]
    assert out.empty


def test_calibracion_por_tramo_incluye_filas_sin_alpha():
    import numpy as np
    df = pd.DataFrame({
        "ticker": ["BTC", "AAPL"],
        "confianza": [75.0, 75.0],
        "acierto_absoluto": [1, 0],
        "alpha": [np.nan, 1.0],  # BTC = sin_benchmark (sin alpha) pero con acierto
    })
    out = metricas.calibracion_por_tramo(df)
    fila = out[out["tramo"] == "70–80"].iloc[0]
    assert fila["n"] == 2            # ambas cuentan, incluida la de alpha NaN
    assert fila["aciertos_pct"] == 50.0
