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
import unicodedata

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
# C) Título de recomendación NUMERADO con el ticker entre paréntesis:
#    "🥇 1. ARM Holdings (ARM)", " 2. NVIDIA (NVDA)", "3. Invesco QQQ Trust (QQQ)".
#    El número de ranking al inicio de línea evita capturar menciones sueltas del
#    cuerpo del texto (p. ej. "Oracle (ORCL)"), que NO son recomendaciones.
_PAT_TICKER_RANK = re.compile(
    r"(?m)^\W*\d{1,2}[.)]\s+.*?\(([A-Z][A-Z0-9.\-^]{0,9})\)"
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
    for pat in (_PAT_TICKER_BOLSA, _PAT_TICKER_TITULO, _PAT_TICKER_RANK):
        for m in pat.finditer(texto):
            t = m.group(1)
            if t in _NO_TICKERS:
                continue
            if t not in encontrados:           # conserva la primera aparición
                encontrados[t] = m.start(1)
    return sorted(encontrados.items(), key=lambda kv: kv[1])


# --- Campos numéricos tolerantes (coma o punto decimal) --------------------
def _num_loose(texto: str | None) -> float | None:
    """Número con coma o punto decimal. '0,8'->0.8, '7.420,10'->7420.1, '2.5'->2.5."""
    if not texto:
        return None
    m = re.search(r"[+-]?\d[\d.,]*", texto)
    if not m:
        return None
    s = m.group(0)
    if "," in s and "." in s:          # europeo: '.' miles, ',' decimal
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:                       # sólo coma => decimal
        s = s.replace(",", ".")
    s = s.rstrip(".")
    try:
        return float(s)
    except ValueError:
        return None


# --- Extracción de campos en PROSA (reportes viejos sin formato fijo) -------
_PAT_CONFIANZA = re.compile(r"confianza\D{0,40}?(\d{1,3})\s*%", re.IGNORECASE)
# Exige la palabra "crecimiento" (evita capturar otros % sueltos, p.ej. futuros).
# Toma el PRIMER número aunque venga como rango ("8–14%", "+2.5% / +4.0%"): para
# la calibración de dirección sólo importa el signo.
_PAT_CRECIMIENTO = re.compile(
    r"crecimiento\D{0,40}?([+-]?\d[\d.,]*)"
    r"(?:\s*[-–—/]\s*[+-]?\d[\d.,]*)?\s*%",
    re.IGNORECASE,
)


def _confianza_prosa(v: str) -> float | None:
    m = _PAT_CONFIANZA.search(v)
    return float(m.group(1)) if m else None


def _crecimiento_prosa(v: str) -> float | None:
    m = _PAT_CRECIMIENTO.search(v)
    return _num_loose(m.group(1)) if m else None


def _extraer_prosa(texto: str) -> list[dict]:
    """Heurística sobre texto libre: ticker + riesgo + (confianza/crecimiento si hay).

    Para cada ticker, la ventana de búsqueda va hasta el ticker siguiente, así un
    campo no se "roba" del bloque de la reco vecina.
    """
    tickers = _tickers(texto)
    recos = []
    for i, (sym, pos) in enumerate(tickers):
        fin = tickers[i + 1][1] if i + 1 < len(tickers) else len(texto)
        v = texto[pos:fin]
        recos.append(
            {
                "activo": sym,
                "ticker": sym,
                "precio_entrada": None,        # layout de precio poco fiable en prosa
                "factores": None,
                "crecimiento_estimado": _crecimiento_prosa(v),
                "confianza": _confianza_prosa(v),
                "riesgo": norm_riesgo(v),
            }
        )
    return recos


# --- Formato CORTITO etiquetado (carga manual del batch histórico) ----------
# Una reco por línea; el ticker es el primer token (o entre paréntesis) y el
# resto son pares "etiqueta: valor" separados por '|'. Orden libre, opcionales:
#   QQQ | riesgo: Segura | estimado: +0.8% | confianza: 78% | entrada: 730
_BOLSAS = {"NASDAQ", "NYSE", "NYSEARCA", "ARCA", "AMEX", "BATS", "CBOE", "BCBA"}
_LABELS = {
    "riesgo": "riesgo",
    "confianza": "confianza",
    "estimado": "crecimiento_estimado",
    "estimacion": "crecimiento_estimado",
    "crecimiento": "crecimiento_estimado",
    "entrada": "precio_entrada",
    "precio": "precio_entrada",
    "nombre": "activo",
    "activo": "activo",
    "factores": "factores",
}
_PAT_SEG_LABEL = re.compile(r"\s*([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s*:\s*(.*)")


def _sin_acentos(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _ticker_de_segmento(seg: str) -> str | None:
    m = _PAT_TICKER_PAREN.search(seg)
    if m and m.group(1) not in _NO_TICKERS:
        return m.group(1)
    m = _PAT_TICKER_BOLSA.search(seg)
    if m:
        return m.group(1)
    for tok in re.findall(r"\b[A-Z][A-Z0-9.\-^]{0,9}\b", seg):
        if tok not in _NO_TICKERS and tok not in _BOLSAS:
            return tok
    return None


def _parse_cortito(linea: str) -> dict | None:
    """Parsea una línea 'TICKER | etiqueta: valor | ...'. None si no aplica."""
    partes = [p.strip() for p in linea.split("|")]
    if len(partes) < 2:
        return None
    sym = _ticker_de_segmento(partes[0])
    if not sym:
        return None
    reco = {
        "activo": sym, "ticker": sym, "precio_entrada": None,
        "factores": None, "crecimiento_estimado": None,
        "confianza": None, "riesgo": None,
    }
    nombre, visto = None, False
    for seg in partes[1:]:
        m = _PAT_SEG_LABEL.match(seg)
        if not m:
            continue
        clave = _LABELS.get(_sin_acentos(m.group(1).lower()))
        if not clave:
            continue
        val, visto = m.group(2).strip(), True
        if clave == "riesgo":
            reco["riesgo"] = norm_riesgo(val) or (val or None)
        elif clave == "crecimiento_estimado":
            reco["crecimiento_estimado"] = _num_loose(val)
        elif clave == "confianza":
            reco["confianza"] = _num_loose(val)
        elif clave == "precio_entrada":
            reco["precio_entrada"] = _num_loose(val)
        elif clave == "factores":
            reco["factores"] = val or None
        elif clave == "activo":
            nombre = val or None
    if not visto:
        return None
    if nombre:
        reco["activo"] = nombre
    return reco


def extraer_recos_v1(texto: str) -> list[dict]:
    """Extrae recomendaciones de un análisis histórico (formato_version=1).

    Dos caminos:
    1) CORTITO etiquetado (una reco por línea, pares 'etiqueta: valor' con '|'):
       se parsea con precisión (ticker, riesgo, crecimiento, confianza, precio).
    2) PROSA libre (reportes viejos): best-effort. Ticker y riesgo por heurística;
       confianza y crecimiento si aparecen etiquetados. Lo no inferible queda None.
    """
    cortito = [r for r in (_parse_cortito(l) for l in texto.splitlines()) if r]
    if cortito:
        return cortito
    return _extraer_prosa(texto)
