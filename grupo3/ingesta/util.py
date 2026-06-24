"""Utilidades de ingesta."""
from __future__ import annotations

from html import escape


def texto_a_html(texto: str) -> str:
    """Envuelve texto plano (un reporte v1 pegado) en un .html mínimo.

    Usa <pre> para preservar los saltos de línea, que la heurística v1 necesita
    (varios tickers se detectan al inicio de línea). El archivo resultante no
    tiene atributos data-*, así que se clasifica como formato_version=1.
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es"><head><meta charset="utf-8"></head>\n'
        f"<body><pre>{escape(texto)}</pre></body></html>\n"
    )
