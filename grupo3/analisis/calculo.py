"""Orquesta el cálculo de mercado + veredicto (Etapa 2).

Por cada recomendación pendiente:
  1. resuelve precios del activo en su horizonte (entrada/cierre).
  2. resuelve precios del S&P 500 en el MISMO período (cacheado por período).
  3. calcula alpha y veredicto relativo.
  4. persiste en SQLite.

Manejo de huecos: ticker None/inexistente, feriado, período no cerrado →
estado_dato 'sin_dato' o 'pendiente'; nunca rompe el pipeline.
"""
from __future__ import annotations

import sqlite3

from grupo3 import db
from grupo3.analisis.veredicto import calcular_veredicto
from grupo3.precios import mercado
from grupo3.precios.provider import PriceProvider, YFinanceProvider


def recalcular(
    conn: sqlite3.Connection,
    provider: PriceProvider | None = None,
    solo_pendientes: bool = True,
) -> dict:
    """Calcula y persiste mercado+veredicto. Devuelve un resumen."""
    provider = provider or YFinanceProvider()
    resumen = {"procesadas": 0, "ok": 0, "sin_benchmark": 0,
               "sin_dato": 0, "pendientes": 0}

    cache_benchmark: dict[tuple[str, str], tuple] = {}

    for fila in db.recomendaciones_para_calcular(conn, solo_pendientes):
        resumen["procesadas"] += 1
        tipo, fecha, ticker = fila["tipo"], fila["fecha"], fila["ticker"]

        # Período aún en curso: no emitir veredicto todavía.
        if not mercado.periodo_cerrado(tipo, fecha):
            resumen["pendientes"] += 1
            continue

        # Sin ticker no se puede traer precio.
        if not ticker:
            db.actualizar_mercado(conn, fila["id"], _sin_dato())
            resumen["sin_dato"] += 1
            continue

        ent_act, cie_act, _ = mercado.precios_activo(provider, ticker, tipo, fecha)

        clave = (tipo, fecha)
        if clave not in cache_benchmark:
            cache_benchmark[clave] = mercado.precios_benchmark(provider, tipo, fecha)
        ent_sp, cie_sp, _, _ = cache_benchmark[clave]

        v = calcular_veredicto(
            entrada_activo=ent_act,
            cierre_activo=cie_act,
            entrada_sp500=ent_sp,
            cierre_sp500=cie_sp,
            crecimiento_estimado=fila["crecimiento_estimado"],
        )

        db.actualizar_mercado(
            conn,
            fila["id"],
            {
                "precio_entrada_real": ent_act,
                "precio_cierre_real": cie_act,
                "sp500_entrada": ent_sp,
                "sp500_cierre": cie_sp,
                "ret_activo": v["ret_activo"],
                "ret_sp500": v["ret_sp500"],
                "alpha": v["alpha"],
                "veredicto": v["veredicto"],
                "acierto_absoluto": v["acierto_absoluto"],
                "direccion_coincide": v["direccion_coincide"],
                "estado_dato": v["estado_dato"],
            },
        )
        resumen[v["estado_dato"]] = resumen.get(v["estado_dato"], 0) + 1

    return resumen


def _sin_dato() -> dict:
    return {
        "precio_entrada_real": None,
        "precio_cierre_real": None,
        "sp500_entrada": None,
        "sp500_cierre": None,
        "ret_activo": None,
        "ret_sp500": None,
        "alpha": None,
        "veredicto": None,
        "acierto_absoluto": None,
        "direccion_coincide": None,
        "estado_dato": "sin_dato",
    }
