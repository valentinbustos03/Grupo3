"""Ingesta de análisis desde GitHub o disco local."""
from grupo3.ingesta.github_client import listar_html, descargar_raw
from grupo3.ingesta.parser import parse_html
from grupo3.ingesta.ingest import ingestar, ingestar_local
from grupo3.ingesta.util import texto_a_html

__all__ = [
    "listar_html",
    "descargar_raw",
    "parse_html",
    "ingestar",
    "ingestar_local",
    "texto_a_html",
]
