"""Cálculo de veredictos, métricas agregadas y candlestick comparativo."""
from grupo3.analisis.veredicto import calcular_veredicto
from grupo3.analisis.calculo import recalcular
from grupo3.analisis import metricas
from grupo3.analisis.candlestick import build_candlestick

__all__ = ["calcular_veredicto", "recalcular", "metricas", "build_candlestick"]
