"""Parser de los HTML de análisis. Tolera dos formatos.

formato_version=2 (NUEVO, estandarizado): selectores con atributos data-*.
    [data-analisis] data-tipo, data-fecha, data-formato-version
    [data-reco] data-activo
    [data-campo="activo|precio_entrada|factores|crecimiento_estimado|confianza|riesgo"]

formato_version=1 (HISTÓRICO, inconsistente): best-effort sobre el texto plano
    (ver grupo3/ingesta/parser_v1.py). Lo que no se puede inferir queda en None.

Devuelve:
    {tipo, fecha, formato_version, recomendaciones: [ {activo, ticker,
     precio_entrada, factores, crecimiento_estimado, confianza, riesgo}, ... ]}
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from grupo3.ingesta import parser_v1
from grupo3.ingesta.parser_v1 import num, ticker, norm_riesgo, norm_fecha

# Nombre de archivo estándar: AAAA-MM-DD_<tipo>.html (fuente confiable de tipo/fecha).
_RE_ARCHIVO = re.compile(r"(\d{4}-\d{2}-\d{2})_(diario|semanal|mensual)", re.IGNORECASE)


def parse_html(html: str, ruta_archivo: str | None = None) -> dict:
    soup = BeautifulSoup(html, "lxml")
    cont = soup.select_one("[data-analisis]")

    formato_version = _detectar_version(cont)
    meta_archivo = _desde_archivo(ruta_archivo)

    if cont is not None and formato_version >= 2:
        data = _parse_v2(cont)
    else:
        data = _parse_v1(soup)

    # El nombre de archivo AAAA-MM-DD_<tipo>.html es la fuente CANÓNICA de fecha y
    # tipo (el texto puede traer fechas ruidosas: rangos de semana, día de cierre,
    # etc.). Si el nombre las define, mandan; si no, caemos a lo parseado del HTML.
    data["tipo"] = meta_archivo.get("tipo") or data.get("tipo")
    data["fecha"] = meta_archivo.get("fecha") or data.get("fecha")
    data["formato_version"] = formato_version
    return data


# --- Detección --------------------------------------------------------------
def _detectar_version(cont) -> int:
    if cont is not None and cont.has_attr("data-formato-version"):
        try:
            return int(cont["data-formato-version"])
        except (ValueError, TypeError):
            pass
    return 2 if cont is not None else 1


def _desde_archivo(ruta_archivo: str | None) -> dict:
    if not ruta_archivo:
        return {}
    m = _RE_ARCHIVO.search(ruta_archivo)
    if not m:
        return {}
    return {"fecha": m.group(1), "tipo": m.group(2).lower()}


# --- formato_version = 2 ----------------------------------------------------
def _parse_v2(cont) -> dict:
    tipo = (cont.get("data-tipo") or "").strip().lower() or None
    fecha = norm_fecha(cont.get("data-fecha"))

    recos = []
    for nodo in cont.select("[data-reco]"):
        data_activo = nodo.get("data-activo")
        recos.append(
            {
                "activo": _campo(nodo, "activo") or data_activo,
                "ticker": ticker(data_activo) or ticker(_campo(nodo, "activo")),
                "precio_entrada": num(_campo(nodo, "precio_entrada")),
                "factores": _campo(nodo, "factores"),
                "crecimiento_estimado": num(_campo(nodo, "crecimiento_estimado")),
                "confianza": num(_campo(nodo, "confianza")),
                "riesgo": norm_riesgo(_campo(nodo, "riesgo")) or _campo(nodo, "riesgo"),
            }
        )
    return {"tipo": tipo, "fecha": fecha, "recomendaciones": recos}


def _campo(nodo, campo: str) -> str | None:
    el = nodo.select_one(f'[data-campo="{campo}"]')
    if el is None:
        return None
    txt = el.get_text(" ", strip=True)
    return txt or None


# --- formato_version = 1 (histórico, best-effort sobre texto plano) ---------
def _parse_v1(soup) -> dict:
    texto = soup.get_text("\n")
    return {
        "tipo": None,                                  # se completa desde el nombre de archivo
        "fecha": parser_v1.fecha_v1(texto),
        "recomendaciones": parser_v1.extraer_recos_v1(texto),
    }
