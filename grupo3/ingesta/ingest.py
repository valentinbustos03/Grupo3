"""Orquesta la ingesta: fuente (GitHub o disco local) -> parser -> SQLite.

Flujo por archivo:
  1. obtiene el HTML crudo (de GitHub o del disco)
  2. parsea (v1/v2 tolerante)
  3. upsert del análisis por (fecha, tipo); si cambió el contenido, re-parsea recos
  4. nunca rompe el pipeline por un archivo malo: lo saltea y reporta

Dos fuentes:
- ``ingestar``        : lee del repo de GitHub (producción / Streamlit Cloud).
- ``ingestar_local``  : lee de ``data/analisis/`` en disco (carga única del
                        batch histórico v1 sin necesidad de pushear primero).
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from grupo3 import config, db
from grupo3.ingesta import github_client, parser


def _resumen_vacio() -> dict:
    return {"vistos": 0, "nuevos": 0, "actualizados": 0, "sin_cambios": 0, "errores": []}


def _procesar(conn, nombre, ruta, html, hash_contenido, resumen) -> None:
    """Parsea un HTML y lo persiste (idempotente). Acumula en ``resumen``."""
    resumen["vistos"] += 1
    try:
        data = parser.parse_html(html, ruta_archivo=ruta)

        if not data.get("tipo") or not data.get("fecha"):
            resumen["errores"].append(f"{nombre}: sin tipo/fecha detectables")
            return

        analisis_id, cambio, es_nuevo = db.upsert_analisis(
            conn,
            tipo=data["tipo"],
            fecha=data["fecha"],
            formato_version=data["formato_version"],
            ruta_archivo=ruta,
            hash_contenido=hash_contenido,
        )

        if not cambio:
            resumen["sin_cambios"] += 1
            return

        # Nuevo o modificado: reemplaza las recomendaciones.
        db.reset_recomendaciones(conn, analisis_id)
        db.insert_recomendaciones(conn, analisis_id, data["recomendaciones"])
        resumen["nuevos" if es_nuevo else "actualizados"] += 1

    except Exception as exc:
        resumen["errores"].append(f"{nombre}: {exc}")


def ingestar(conn: sqlite3.Connection) -> dict:
    """Ingesta los HTML del repo de GitHub. Devuelve un resumen."""
    db.init_db(conn)
    resumen = _resumen_vacio()

    try:
        archivos = github_client.listar_html()
    except Exception as exc:  # red / API caída: que el dashboard no muera
        resumen["errores"].append(f"listar repo: {exc}")
        return resumen

    for arch in archivos:
        try:
            html = github_client.descargar_raw(arch["download_url"])
        except Exception as exc:
            resumen["vistos"] += 1
            resumen["errores"].append(f"{arch['name']}: descarga: {exc}")
            continue
        _procesar(conn, arch["name"], arch["path"], html, arch["sha"], resumen)

    return resumen


def ingestar_local(conn: sqlite3.Connection, carpeta: str | Path | None = None) -> dict:
    """Ingesta los .html de una carpeta local (default: ``data/analisis/``).

    Pensado para la carga única del batch histórico v1: dropeás los archivos,
    ingerís y verificás localmente, y recién después pusheás al repo.
    """
    db.init_db(conn)
    resumen = _resumen_vacio()

    base = Path(carpeta) if carpeta else (config.ROOT / config.DATA_DIR)
    if not base.exists():
        resumen["errores"].append(f"no existe la carpeta {base}")
        return resumen

    for archivo in sorted(base.glob("*.html")):
        html = archivo.read_text(encoding="utf-8")
        hash_contenido = hashlib.sha1(html.encode("utf-8")).hexdigest()
        ruta = f"{config.DATA_DIR}/{archivo.name}"
        _procesar(conn, archivo.name, ruta, html, hash_contenido, resumen)

    return resumen
