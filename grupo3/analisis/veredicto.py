"""Cálculo del veredicto RELATIVO al S&P 500 (Etapa 2).

Funciones puras (sin I/O) para poder testearlas con TDD al cablear la etapa.

    ret_activo = (cierre_activo / entrada_activo - 1) * 100
    ret_sp500  = (cierre_sp500  / entrada_sp500  - 1) * 100
    alpha      = ret_activo - ret_sp500

    veredicto: GANO   si alpha >  umbral
               PERDIO si alpha < -umbral
               NEUTRO si |alpha| <= umbral
"""
from __future__ import annotations

from grupo3 import config


def _retorno(entrada: float | None, cierre: float | None) -> float | None:
    if entrada is None or cierre is None or entrada == 0:
        return None
    return (cierre / entrada - 1) * 100


def calcular_veredicto(
    *,
    entrada_activo: float | None,
    cierre_activo: float | None,
    entrada_sp500: float | None,
    cierre_sp500: float | None,
    crecimiento_estimado: float | None = None,
    umbral: float | None = None,
) -> dict:
    """Devuelve métricas del veredicto. Si falta dato => estado_dato='sin_dato'.

    direccion_coincide: el signo del crecimiento_estimado (lo que dijo el modelo)
    coincide con el signo del retorno real del activo (mide calibración, aparte
    del alpha vs benchmark).
    """
    umbral = config.UMBRAL_NEUTRO if umbral is None else umbral

    ret_activo = _retorno(entrada_activo, cierre_activo)
    ret_sp500 = _retorno(entrada_sp500, cierre_sp500)

    # Sin retorno del activo no hay NADA utilizable (ticker inexistente, hueco).
    if ret_activo is None:
        return {
            "ret_activo": None,
            "ret_sp500": ret_sp500,
            "alpha": None,
            "veredicto": None,
            "acierto_absoluto": None,
            "direccion_coincide": None,
            "estado_dato": "sin_dato",
        }

    # Señales que NO dependen del benchmark (calibración del modelo).
    acierto_absoluto = int(ret_activo > 0)
    direccion_coincide = None
    if crecimiento_estimado is not None:
        direccion_coincide = int((crecimiento_estimado >= 0) == (ret_activo >= 0))

    # Protocolo PARCIAL (días de mercado cerrado): el activo cotiza (24/7) pero el
    # S&P 500 no → no hay alpha relativo. Guardamos retorno absoluto + calibración;
    # alpha/veredicto quedan N/A y estos casos se excluyen de las métricas vs S&P.
    if ret_sp500 is None:
        return {
            "ret_activo": ret_activo,
            "ret_sp500": None,
            "alpha": None,
            "veredicto": None,
            "acierto_absoluto": acierto_absoluto,
            "direccion_coincide": direccion_coincide,
            "estado_dato": "sin_benchmark",
        }

    alpha = ret_activo - ret_sp500
    if alpha > umbral:
        veredicto = "GANO"
    elif alpha < -umbral:
        veredicto = "PERDIO"
    else:
        veredicto = "NEUTRO"

    return {
        "ret_activo": ret_activo,
        "ret_sp500": ret_sp500,
        "alpha": alpha,
        "veredicto": veredicto,
        "acierto_absoluto": acierto_absoluto,
        "direccion_coincide": direccion_coincide,
        "estado_dato": "ok",
    }
