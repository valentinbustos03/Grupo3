"""Orquesta la ingesta: GitHub -> parser -> SQLite (idempotente).

Flujo por archivo:
  1. lista los HTML del repo
  2. descarga el crudo
  3. parsea (v1/v2 tolerante)
  4. upsert del análisis por (fecha, tipo); si cambió el contenido, re-parsea recos
  5. nunca rompe el pipeline por un archivo malo: lo saltea y reporta
"""
from __future__ import annotations

import sqlite3

from grupo3 import db
from grupo3.ingesta import github_client, parser


def ingestar(conn: sqlite3.Connection) -> dict:
    """Ingesta todos los HTML pendientes. Devuelve un resumen."""
    db.init_db(conn)

    resumen = {"vistos": 0, "nuevos": 0, "actualizados": 0, "sin_cambios": 0, "errores": []}

    try:
        archivos = github_client.listar_html()
    except Exception as exc:  # red / API caída: que el dashboard no muera
        resumen["errores"].append(f"listar repo: {exc}")
        return resumen

    for arch in archivos:
        resumen["vistos"] += 1
        try:
            html = github_client.descargar_raw(arch["download_url"])
            data = parser.parse_html(html, ruta_archivo=arch["path"])

            if not data.get("tipo") or not data.get("fecha"):
                resumen["errores"].append(
                    f"{arch['name']}: sin tipo/fecha detectables"
                )
                continue

            analisis_id, cambio, es_nuevo = db.upsert_analisis(
                conn,
                tipo=data["tipo"],
                fecha=data["fecha"],
                formato_version=data["formato_version"],
                ruta_archivo=arch["path"],
                hash_contenido=arch["sha"],
            )

            if not cambio:
                resumen["sin_cambios"] += 1
                continue

            # Nuevo o modificado: reemplaza las recomendaciones.
            db.reset_recomendaciones(conn, analisis_id)
            db.insert_recomendaciones(conn, analisis_id, data["recomendaciones"])
            resumen["nuevos" if es_nuevo else "actualizados"] += 1

        except Exception as exc:
            resumen["errores"].append(f"{arch['name']}: {exc}")

    return resumen
