"""Ingesta de análisis desde GitHub."""
from grupo3.ingesta.github_client import listar_html, descargar_raw
from grupo3.ingesta.parser import parse_html
from grupo3.ingesta.ingest import ingestar

__all__ = ["listar_html", "descargar_raw", "parse_html", "ingestar"]
