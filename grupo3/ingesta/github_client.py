"""Lectura de los HTML desde el repo de GitHub vía la API de contenidos.

Por qué la API y no clonar: en Streamlit Cloud no hay garantía de tener git ni
disco persistente. La API de contenidos sólo necesita HTTP + (opcional) un token,
es simple y robusta. Para repos públicos funciona anónima (con rate limit bajo);
para privados o más cuota, se pasa un token vía secrets/env.
"""
from __future__ import annotations

import requests

from grupo3 import config

_API = "https://api.github.com/repos/{owner}/{repo}/contents/{path}"
_TIMEOUT = 20


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = config.github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def listar_html() -> list[dict]:
    """Lista los .html de DATA_DIR en el repo.

    Devuelve dicts con: name, path, sha, download_url.
    Si la carpeta no existe todavía (404), devuelve lista vacía.
    """
    url = _API.format(
        owner=config.GITHUB_OWNER, repo=config.GITHUB_REPO, path=config.DATA_DIR
    )
    resp = requests.get(
        url, headers=_headers(), params={"ref": config.GITHUB_BRANCH}, timeout=_TIMEOUT
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return [
        {
            "name": item["name"],
            "path": item["path"],
            "sha": item["sha"],          # sha de git: sirve como hash_contenido
            "download_url": item["download_url"],
        }
        for item in resp.json()
        if item.get("type") == "file" and item["name"].lower().endswith(".html")
    ]


def descargar_raw(download_url: str) -> str:
    """Descarga el contenido crudo de un HTML."""
    resp = requests.get(download_url, headers=_headers(), timeout=_TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.encoding or "utf-8"
    return resp.text
