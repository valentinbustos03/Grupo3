"""Conexión y helpers de persistencia SQLite.

La base es reconstruible (puede ser efímera en Streamlit Cloud). ``init_db``
es idempotente; ``upsert_analisis`` respeta la clave (fecha, tipo).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from grupo3 import config

_SCHEMA = Path(__file__).with_name("schema.sql")


def connect(db_path: str | None = None, check_same_thread: bool = True) -> sqlite3.Connection:
    """Conexión con foreign keys activas y filas accesibles por nombre.

    ``check_same_thread=False`` permite reusar la conexión entre threads: lo
    necesita el dashboard, donde la conexión se cachea con ``st.cache_resource``
    y Streamlit corre cada rerun en un thread distinto (acceso serializado de un
    solo usuario, así que es seguro). El pipeline/tests usan el default seguro.
    """
    conn = sqlite3.connect(db_path or config.DB_PATH, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Crea las tablas si no existen (idempotente)."""
    conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def upsert_analisis(
    conn: sqlite3.Connection,
    *,
    tipo: str,
    fecha: str,
    formato_version: int,
    ruta_archivo: str,
    hash_contenido: str | None,
) -> tuple[int, bool, bool]:
    """Inserta o actualiza un análisis por clave (fecha, tipo).

    Devuelve (analisis_id, cambio, es_nuevo):
    - cambio=True   si es nuevo o el hash_contenido cambió (hay que re-parsear).
    - es_nuevo=True si no existía antes.
    """
    row = conn.execute(
        "SELECT id, hash_contenido FROM analisis WHERE fecha = ? AND tipo = ?",
        (fecha, tipo),
    ).fetchone()

    if row is None:
        cur = conn.execute(
            """INSERT INTO analisis
               (tipo, fecha, formato_version, ruta_archivo, hash_contenido, creado_en)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (tipo, fecha, formato_version, ruta_archivo, hash_contenido, _now()),
        )
        conn.commit()
        return cur.lastrowid, True, True

    analisis_id = row["id"]
    if hash_contenido and hash_contenido != row["hash_contenido"]:
        conn.execute(
            """UPDATE analisis
               SET formato_version = ?, ruta_archivo = ?, hash_contenido = ?
               WHERE id = ?""",
            (formato_version, ruta_archivo, hash_contenido, analisis_id),
        )
        conn.commit()
        return analisis_id, True, False

    return analisis_id, False, False


def reset_recomendaciones(conn: sqlite3.Connection, analisis_id: int) -> None:
    """Borra las recomendaciones de un análisis (antes de re-parsear)."""
    conn.execute("DELETE FROM recomendaciones WHERE analisis_id = ?", (analisis_id,))
    conn.commit()


def actualizar_mercado(conn: sqlite3.Connection, reco_id: int, campos: dict) -> None:
    """Persiste los datos de mercado y el veredicto de una recomendación (Etapa 2).

    campos: precio_entrada_real, precio_cierre_real, sp500_entrada, sp500_cierre,
            ret_activo, ret_sp500, alpha, veredicto, acierto_absoluto,
            direccion_coincide, estado_dato.
    """
    conn.execute(
        """UPDATE recomendaciones SET
               precio_entrada_real = :precio_entrada_real,
               precio_cierre_real  = :precio_cierre_real,
               sp500_entrada       = :sp500_entrada,
               sp500_cierre        = :sp500_cierre,
               ret_activo          = :ret_activo,
               ret_sp500           = :ret_sp500,
               alpha               = :alpha,
               veredicto           = :veredicto,
               acierto_absoluto    = :acierto_absoluto,
               direccion_coincide  = :direccion_coincide,
               estado_dato         = :estado_dato,
               calculado_en        = :calculado_en
           WHERE id = :id""",
        {"id": reco_id, "calculado_en": _now(), **campos},
    )
    conn.commit()


def recomendaciones_para_calcular(conn: sqlite3.Connection, solo_pendientes: bool = True):
    """Recomendaciones con el tipo/fecha de su análisis, para resolver precios.

    Si solo_pendientes, omite las que ya tienen estado_dato='ok'.
    """
    sql = (
        "SELECT r.id, r.ticker, r.crecimiento_estimado, r.estado_dato, "
        "       a.tipo, a.fecha "
        "FROM recomendaciones r JOIN analisis a ON a.id = r.analisis_id"
    )
    if solo_pendientes:
        sql += " WHERE r.estado_dato != 'ok'"
    return conn.execute(sql).fetchall()


def insert_recomendaciones(
    conn: sqlite3.Connection, analisis_id: int, recos: list[dict]
) -> None:
    """Inserta las recomendaciones parseadas (campos de mercado quedan NULL)."""
    conn.executemany(
        """INSERT INTO recomendaciones
           (analisis_id, activo, ticker, precio_entrada, factores,
            crecimiento_estimado, confianza, riesgo, estado_dato)
           VALUES (:analisis_id, :activo, :ticker, :precio_entrada, :factores,
                   :crecimiento_estimado, :confianza, :riesgo, 'pendiente')""",
        [
            {
                "analisis_id": analisis_id,
                "activo": r.get("activo"),
                "ticker": r.get("ticker"),
                "precio_entrada": r.get("precio_entrada"),
                "factores": r.get("factores"),
                "crecimiento_estimado": r.get("crecimiento_estimado"),
                "confianza": r.get("confianza"),
                "riesgo": r.get("riesgo"),
            }
            for r in recos
        ],
    )
    conn.commit()
