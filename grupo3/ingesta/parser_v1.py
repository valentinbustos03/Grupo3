"""Heurísticas para análisis HISTÓRICOS (formato_version=1).

Los HTML viejos son INCONSISTENTES (texto libre, emojis, tablas variables, sin
atributos data-*). Este módulo es PURO (sólo ``re``, sin BeautifulSoup) para
poder testearlo aislado y para que el parser principal lo reutilice sobre el
``get_text()`` del HTML.

Filosofía: "parseá lo que puedas y marcá lo faltante como null". Para el cálculo
de alpha basta el TICKER (los precios reales los trae yfinance según el período;
la fecha y el tipo salen del nombre de archivo AAAA-MM-DD_<tipo>.html).
"""
from __future__ import annotations

import re

# --- Tickers ---------------------------------------------------------------
# A) Prefijo de bolsa explícito:  "NASDAQ: QQQ", "NYSE: ACN", "NYSE Arca: SPY".
_PAT_TICKER_BOLSA = re.compile(
    r"(?:NASDAQ|NYSE(?:\s*Arca)?|NYSEARCA|AMEX|BATS|CBOE|BCBA)\s*:\s*([A-Z][A-Z0-9.]{0,5})"
)
# B) Ticker como primer token de un título de empresa/ETF:
#    "XLE Energy Select Sector SPDR ETF", "CVX Chevron Corporation".
_PAT_TICKER_TITULO = re.compile(
    r"(?m)^\s*([A-Z]{2,5})\b[^\n]*?"
    r"(?:ETF|Inc\.?|Corporation|Corp\.?|Trust|Shares|PLC|Company|Devices|"
    r"Select|iShares|SPDR|Holdings|Technologies|Group)"
)
# Falsos positivos frecuentes que NO son tickers.
_NO_TICKERS = {
    "ETF", "EEUU", "USD", "USA", "RSI", "ATR", "EPS", "IPO", "WTI", "BCE",
    "FED", "CEO", "PIB", "GDP", "FOMC", "SEC", "API", "ESG", "IA", "AI",
}

# --- Riesgo ----------------------------------------------------------------
_PAT_RIESGO = re.compile(
    r"\b(muy\s+segura|muy\s+riesgosa|segura|moderad[oa]|riesgosa)\b", re.IGNORECASE
)
_RIESGO_CANON = {
    "muy segura": "Muy segura",
    "segura": "Segura",
    "moderado": "Moderado",
    "moderada": "Moderado",
    "riesgosa": "Riesgosa",
    "muy riesgosa": "Muy Riesgosa",
}

# --- Fechas (varios formatos en español) -----------------------------------
_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
_PAT_FECHA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_PAT_FECHA_SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")          # DD/MM/YYYY
_PAT_FECHA_TXT = re.compile(
    r"\b(\d{1,2})\s+de\s+([a-záé]+)\s+de\s+(\d{4})\b", re.IGNORECASE
)


def norm_riesgo(texto: str | None) -> str | None:
    """Normaliza a uno de los 5 niveles canónicos. None si no matchea."""
    if not texto:
        return None
    m = _PAT_RIESGO.search(texto)
    if not m:
        return None
    clave = re.sub(r"\s+", " ", m.group(1).lower())
    return _RIESGO_CANON.get(clave)


# --- Normalizadores compartidos (los usa también el parser v2) -------------
_PAT_NUM = re.compile(r"[-+]?\d*\.?\d+")
_PAT_TICKER_PAREN = re.compile(r"\(([A-Z][A-Z0-9.\-^]{0,9})\)")
_PAT_TICKER_PLANO = re.compile(r"[A-Z][A-Z0-9.\-^]{0,9}")


def num(texto: str | None) -> float | None:
    """Extrae un número de un texto con %, $, +, comas, espacios. None si no hay."""
    if texto is None:
        return None
    t = texto.replace("%", "").replace("$", "").replace(",", "").strip()
    m = _PAT_NUM.search(t)
    return float(m.group(0)) if m else None


def ticker(texto: str | None) -> str | None:
    """Extrae el ticker. Prioriza símbolo entre paréntesis: 'Apple (AAPL)'."""
    if not texto:
        return None
    m = _PAT_TICKER_PAREN.search(texto)
    if m:
        return m.group(1)
    t = texto.strip()
    if _PAT_TICKER_PLANO.fullmatch(t):
        return t
    return None


def norm_fecha(texto: str | None) -> str | None:
    """Normaliza una fecha a ISO si encuentra el patrón AAAA-MM-DD; si no, el texto."""
    if not texto:
        return None
    m = _PAT_FECHA_ISO.search(texto)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else texto.strip() or None


def fecha_v1(texto: str) -> str | None:
    """Intenta una fecha ISO desde texto libre. None si no encuentra."""
    m = _PAT_FECHA_ISO.search(texto)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = _PAT_FECHA_TXT.search(texto)
    if m:
        mes = _MESES.get(m.group(2).lower())
        if mes:
            return f"{int(m.group(3)):04d}-{mes:02d}-{int(m.group(1)):02d}"
    m = _PAT_FECHA_SLASH.search(texto)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None


def _tickers(texto: str) -> list[tuple[str, int]]:
    """Tickers candidatos como (ticker, posición), únicos, en orden de aparición."""
    encontrados: dict[str, int] = {}
    for pat in (_PAT_TICKER_BOLSA, _PAT_TICKER_TITULO):
        for m in pat.finditer(texto):
            t = m.group(1)
            if t in _NO_TICKERS:
                continue
            if t not in encontrados:           # conserva la primera aparición
                encontrados[t] = m.start(1)
    return sorted(encontrados.items(), key=lambda kv: kv[1])


def _riesgo_cercano(texto: str, pos: int, ventana: int = 1200) -> str | None:
    """Primer nivel de riesgo que aparece tras la posición del ticker."""
    return norm_riesgo(texto[pos: pos + ventana])


def extraer_recos_v1(texto: str) -> list[dict]:
    """Extrae recomendaciones best-effort de un análisis histórico.

    Devuelve dicts con la misma forma que el parser v2; los campos que no se
    pueden inferir con confianza quedan en None (precio/factores/crecimiento/
    confianza). Ticker y riesgo se infieren por heurística.
    """
    recos = []
    for ticker, pos in _tickers(texto):
        recos.append(
            {
                "activo": ticker,
                "ticker": ticker,
                "precio_entrada": None,
                "factores": None,
                "crecimiento_estimado": None,
                "confianza": None,
                "riesgo": _riesgo_cercano(texto, pos),
            }
        )
    return recos
