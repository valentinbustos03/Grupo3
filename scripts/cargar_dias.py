"""Carga el batch de dias.txt: v1 (tablas históricas) + v2 (emails de la Routine).

Genera un .html por (fecha, tipo) en data/analisis/:
  - v1 (<= 2026-06-18): cortito etiquetado envuelto en <pre> => formato_version=1.
  - v2 (>= 2026-06-19): HTML con atributos data-* => formato_version=2.

Los v1 se transcriben a mano desde las tablas de dias.txt (formatos inconsistentes:
emojis, columnas variables, ticker en 2ª columna, decimales coma). El crecimiento
estimado se toma como el PUNTO MEDIO del rango informado (representa el estimado
central del modelo; para la calibración importa el signo).

Los v2 se auto-extraen de los emails MIME de dias.txt (estructura HTML uniforme),
porque esos mails NO traen data-* y hay que reconstruirlos.

No pisa archivos ya existentes en data/analisis/.

Uso:  .venv/bin/python scripts/cargar_dias.py
"""
from __future__ import annotations

import html as _html
import quopri
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup            # noqa: E402

from grupo3 import config                # noqa: E402
from grupo3.ingesta import texto_a_html  # noqa: E402

DEST = config.ROOT / config.DATA_DIR


# --- v1: transcripción de las tablas (ticker, riesgo, crec_medio, confianza) ---
# fecha, tipo -> lista de (ticker, riesgo, crecimiento_estimado_%, confianza_%)
V1: dict[tuple[str, str], list[tuple]] = {
    ("2026-06-02", "diario"): [
        ("HPE", "Moderado", 8.5, 55), ("MRVL", "Riesgosa", 5.5, 48),
        ("NVDA", "Segura", 3.5, 65),
    ],
    ("2026-06-03", "diario"): [
        ("MRVL", "Riesgosa", 4.5, 62), ("SOXL", "Muy Riesgosa", 6.5, 55),
        ("QQQ", "Moderado", 1.0, 72),
    ],
    ("2026-06-04", "diario"): [
        ("NVDA", "Moderado", 1.6, 65), ("USO", "Riesgosa", 2.15, 60),
        ("HPE", "Moderado", 1.15, 68),
    ],
    ("2026-06-05", "diario"): [
        ("HPE", "Moderado", 3.5, 62), ("DIA", "Segura", 1.2, 71),
        ("SOXL", "Riesgosa", 8.5, 44),
    ],
    ("2026-06-08", "semanal"): [
        ("XLE", "Segura", 3.0, 68), ("XLV", "Moderado", 2.0, 62),
        ("NVDA", "Riesgosa", 5.0, 51),
    ],
    ("2026-06-09", "diario"): [
        ("MU", "Moderado", 2.0, 62), ("SOXX", "Moderado", 1.15, 68),
        ("GLW", "Riesgosa", 1.0, 55),
    ],
    ("2026-06-10", "diario"): [
        ("ORCL", "Moderado", 2.75, 62), ("QQQ", "Riesgosa", 2.0, 57),
        ("XLE", "Segura", 1.3, 66),
    ],
    ("2026-06-12", "diario"): [
        ("QQQ", "Segura", 1.2, 72), ("NVDA", "Moderado", 2.3, 62),
        ("SOXL", "Riesgosa", 4.5, 52),
    ],
    ("2026-06-15", "diario"): [
        ("SPCX", "Riesgosa", 7.0, 55), ("DAL", "Moderado", 4.5, 70),
        ("QQQ", "Segura", 2.0, 65),
    ],
    ("2026-06-15", "semanal"): [
        ("NVDA", "Riesgosa", 4.0, 62), ("QQQ", "Moderado", 2.0, 70),
        ("MSFT", "Segura", 2.25, 68),
    ],
    ("2026-06-16", "diario"): [
        ("MU", "Riesgosa", 2.5, 60), ("SMH", "Moderado", 1.3, 68),
        ("SPCX", "Muy Riesgosa", 1.0, 42),
    ],
    ("2026-06-17", "diario"): [
        ("NVDA", "Moderado", 2.3, 63), ("SPY", "Segura", 0.75, 73),
        ("SOXL", "Muy Riesgosa", 3.75, 41),
    ],
}


def _cortito(recos: list[tuple]) -> str:
    lineas = [
        f"{tk} | riesgo: {ri} | estimado: {cr:+g}% | confianza: {co}%"
        for tk, ri, cr, co in recos
    ]
    return "\n".join(lineas) + "\n"


def escribir_v1() -> list[str]:
    escritos = []
    for (fecha, tipo), recos in V1.items():
        dest = DEST / f"{fecha}_{tipo}.html"
        if dest.exists():
            continue
        dest.write_text(texto_a_html(_cortito(recos)), encoding="utf-8")
        escritos.append(dest.name)
    return escritos


# --- v2: auto-extracción de los emails MIME ---------------------------------
_PLANTILLA_RECO = """  <div data-reco data-activo="{ticker}"
       style="border:1px solid #232833;border-radius:10px;padding:16px;margin-bottom:12px">
    <strong data-campo="activo" style="font-size:18px;color:#fff">{nombre}</strong>
    <span data-campo="riesgo" style="margin-left:8px">{riesgo}</span>
    <p style="margin:8px 0 4px;color:#8a909a">Precio entrada:
       <span data-campo="precio_entrada" style="color:#e6e8eb">{precio}</span></p>
    <p style="margin:4px 0;color:#8a909a">Factores:
       <span data-campo="factores" style="color:#e6e8eb">{factores}</span></p>
    <div style="display:flex;gap:16px;margin-top:8px">
      <span style="color:#8a909a">Crec. estimado:
        <b data-campo="crecimiento_estimado" style="color:#4ade80">{crecimiento}</b></span>
      <span style="color:#8a909a">Confianza:
        <b data-campo="confianza" style="color:#e6e8eb">{confianza}</b></span>
    </div>
  </div>
"""

_PLANTILLA_DOC = """<div data-analisis data-tipo="{tipo}" data-fecha="{fecha}" data-formato-version="2"
     style="font-family:Inter,Arial,sans-serif;max-width:640px;margin:auto;color:#e6e8eb;padding:24px;border-radius:12px">
  <h2 style="margin:0 0 4px;color:#fff">Análisis bursátil — {tipo_cap}</h2>
  <p style="margin:0 0 20px;color:#8a909a">Fecha: {fecha}</p>
{recos}</div>
"""


def _decode_qp(texto: str) -> str:
    return quopri.decodestring(texto.encode("utf-8")).decode("utf-8", "replace")


def _ticker(nombre: str) -> str:
    # "MU — Micron Technology" / "MU" -> "MU".
    return re.split(r"[—\-—\s]", nombre.strip(), 1)[0].strip()


def _parse_email(bloque: str) -> dict | None:
    """Extrae fecha, tipo y recos de un email MIME de la Routine. None si no aplica."""
    m_html = re.search(
        r"Content-Type: text/html.*?\n\n(.*?)(?:\n------=_Part|\Z)",
        bloque, re.DOTALL,
    )
    if not m_html:
        return None
    soup = BeautifulSoup(_decode_qp(m_html.group(1)), "lxml")

    texto = soup.get_text(" ")
    m_fecha = re.search(r"(\d{4}-\d{2}-\d{2})", texto)
    m_tipo = re.search(r"\b(Diario|Semanal|Mensual)\b", texto, re.IGNORECASE)
    if not m_fecha or not m_tipo:
        return None
    fecha, tipo = m_fecha.group(1), m_tipo.group(1).lower()

    recos = []
    for div in soup.find_all("div"):
        # Una reco tiene EXACTAMENTE un "Precio entrada:"; el wrapper del email
        # tiene 3 (los englobaría a todos) y el div de contexto, 0.
        if div.get_text().count("Precio entrada:") != 1:
            continue
        strong = div.find("strong")
        if not strong:
            continue
        t = div.get_text(" ")
        m_pre = re.search(r"Precio entrada:\s*([\d.,]+)", t)
        m_cre = re.search(r"Crec\.?\s*estimado:\s*([+-]?[\d.,]+)\s*%", t)
        m_con = re.search(r"Confianza:\s*([\d.,]+)\s*%", t)
        # riesgo: primer <span> hermano del <strong>
        badge = strong.find_next("span")
        riesgo = badge.get_text(strip=True) if badge else ""
        # factores: el <span> dentro del <p> que contiene "Factores:"
        factores = ""
        for p in div.find_all("p"):
            if "Factores:" in p.get_text():
                sp = p.find("span")
                factores = sp.get_text(" ", strip=True) if sp else ""
                break
        recos.append({
            "ticker": _ticker(strong.get_text()),
            "nombre": strong.get_text(strip=True),
            "riesgo": riesgo,
            "precio": (m_pre.group(1).replace(",", "") if m_pre else ""),
            "crecimiento": (m_cre.group(1) + "%" if m_cre else ""),
            "confianza": (m_con.group(1) if m_con else ""),
            "factores": _html.escape(factores),
        })
    if not recos:
        return None
    return {"fecha": fecha, "tipo": tipo, "recos": recos}


def escribir_v2(dias_txt: str) -> list[str]:
    escritos = []
    bloques = re.split(r"(?=^Received: from)", dias_txt, flags=re.MULTILINE)
    for b in bloques:
        if "Content-Type: text/html" not in b:
            continue
        data = _parse_email(b)
        if not data:
            continue
        dest = DEST / f"{data['fecha']}_{data['tipo']}.html"
        if dest.exists():
            continue
        cuerpo = "".join(
            _PLANTILLA_RECO.format(
                ticker=r["ticker"], nombre=r["nombre"], riesgo=r["riesgo"],
                precio=r["precio"], factores=r["factores"],
                crecimiento=r["crecimiento"], confianza=r["confianza"] + "%",
            )
            for r in data["recos"]
        )
        doc = _PLANTILLA_DOC.format(
            tipo=data["tipo"], tipo_cap=data["tipo"].capitalize(),
            fecha=data["fecha"], recos=cuerpo,
        )
        dest.write_text(doc, encoding="utf-8")
        escritos.append(dest.name)
    return escritos


def main() -> None:
    dias = (config.ROOT / "dias.txt").read_text(encoding="utf-8")
    v1 = escribir_v1()
    v2 = escribir_v2(dias)
    print(f"v1 escritos ({len(v1)}): {', '.join(sorted(v1)) or '—'}")
    print(f"v2 escritos ({len(v2)}): {', '.join(sorted(v2)) or '—'}")


if __name__ == "__main__":
    main()
