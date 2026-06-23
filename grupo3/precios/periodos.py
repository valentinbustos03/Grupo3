"""Ventanas temporales por horizonte (Etapa 2).

Define, dado el tipo de análisis y su fecha, qué rango de mercado mirar:
- diario  : apertura vs cierre del MISMO día.
- semanal : lunes (entrada) vs cierre del último día hábil de esa semana.
- mensual : primer día hábil vs cierre del último día hábil del mes.

Devuelve un rango de fechas (inicio, fin) para pedirle OHLC al PriceProvider.
El "precio de entrada real" será el Open de la primera fila con dato del rango,
y el "cierre real" el Close de la última fila con dato (robusto a feriados).
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta


def _a_date(fecha_iso: str) -> date:
    return datetime.strptime(fecha_iso, "%Y-%m-%d").date()


def rango(tipo: str, fecha_iso: str) -> tuple[str, str]:
    """Devuelve (inicio, fin) ISO inclusivos para el horizonte dado."""
    d = _a_date(fecha_iso)
    tipo = tipo.lower()

    if tipo == "diario":
        inicio = fin = d

    elif tipo == "semanal":
        # Semana de la fecha: lunes -> domingo (el último hábil se resuelve con
        # los datos OHLC reales, tomando el último Close disponible del rango).
        inicio = d - timedelta(days=d.weekday())   # lunes
        fin = inicio + timedelta(days=6)            # domingo

    elif tipo == "mensual":
        inicio = d.replace(day=1)
        ultimo = calendar.monthrange(d.year, d.month)[1]
        fin = d.replace(day=ultimo)

    else:
        raise ValueError(f"tipo desconocido: {tipo!r}")

    return inicio.isoformat(), fin.isoformat()
