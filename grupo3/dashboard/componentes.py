"""Builders de HTML del dashboard (puros). Devuelven strings con clases del tema."""
from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

import pandas as pd

from grupo3 import config
from grupo3.dashboard import theme

_VEREDICTO_TXT = {"GANO": "GANÓ", "PERDIO": "PERDIÓ", "NEUTRO": "NEUTRO"}


def _na(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v))


def _pct(v, signo: bool = False) -> str:
    if _na(v):
        return "—"
    return f"{v:+.2f}%" if signo else f"{v:.2f}%"


def _money(v) -> str:
    return "—" if _na(v) else f"{v:,.2f}"


def badge_riesgo(nivel: str | None) -> str:
    if _na(nivel):
        color = theme.NEUTRO
        return (f'<span class="badge" style="color:{color};border-color:{color}55;'
                f'background:{color}1a">—</span>')
    color = theme.RIESGO_COLOR.get(nivel, theme.NEUTRO)
    return (f'<span class="badge" style="color:{color};border-color:{color}66;'
            f'background:{color}1f">{html.escape(str(nivel))}</span>')


def badge_veredicto(v: str | None) -> str:
    color = theme.VEREDICTO_COLOR.get(v, theme.NEUTRO)
    txt = _VEREDICTO_TXT.get(v, "—")
    return (f'<span class="badge" style="color:{color};border-color:{color}66;'
            f'background:{color}1f">{txt}</span>')


def _logo_html() -> str:
    """Logo de ``assets/logo.*`` embebido; si no existe, placeholder con hueco."""
    for name in ("logo.svg", "logo.png", "logo.webp", "logo.jpg"):
        p = Path(config.ROOT) / "assets" / name
        if p.exists():
            if p.suffix == ".svg":
                return f'<div class="logo-slot has-logo">{p.read_text(encoding="utf-8")}</div>'
            mime = mimetypes.guess_type(str(p))[0] or "image/png"
            data = base64.b64encode(p.read_bytes()).decode()
            return ('<div class="logo-slot has-logo">'
                    f'<img src="data:{mime};base64,{data}" alt="Grupo3"></div>')
    return '<div class="logo-slot">logo</div>'


def masthead() -> str:
    """Marca Grupo3 (con logo) — estilos inline EXACTOS del mockup v2."""
    return (
        '<div style="position:relative; display:flex; align-items:center; gap:18px;">'
        f'{_logo_html()}'
        '<div>'
        '<div style="font-size:11.5px; letter-spacing:.18em; text-transform:uppercase;'
        ' color:rgba(255,255,255,.55); font-weight:700;">Experimento de inversión</div>'
        "<div style=\"display:flex; align-items:baseline; gap:1px; margin-top:8px;"
        " padding-bottom:6px; font-family:'IBM Plex Serif',serif;\">"
        '<span style="font-size:62px; font-weight:700; letter-spacing:-.01em;'
        ' line-height:1.1; color:#fff; text-shadow:0 4px 26px rgba(0,0,0,.35);">Grupo</span>'
        '<span style="font-size:62px; font-weight:700; letter-spacing:-.01em;'
        ' line-height:1.1; background:linear-gradient(125deg,#fff 0%,#a78bfa 42%,#4ade80 100%);'
        ' -webkit-background-clip:text; background-clip:text;'
        ' -webkit-text-fill-color:transparent;'
        ' filter:drop-shadow(0 6px 30px rgba(167,139,250,.55));">3</span>'
        '</div>'
        '<div style="margin-top:8px; font-size:14px; color:rgba(255,255,255,.66);'
        ' max-width:540px;">Recomendaciones de IA frente al benchmark '
        '<span style="color:rgba(255,255,255,.92); font-weight:600;">S&amp;P 500</span>'
        ' · panel de resultados</div>'
        '</div></div>'
    )


def status_pill(ia_en_ventaja: bool | None) -> str:
    """Pill de estado IA vs índice — estilo inline del mockup (vacío si None)."""
    if ia_en_ventaja is None:
        return ""
    if ia_en_ventaja:
        accent, glow, soft, border, txt = (
            theme.VERDE, "rgba(74,222,128,.55)", "rgba(74,222,128,.12)",
            "rgba(74,222,128,.35)", "IA en ventaja")
    else:
        accent, glow, soft, border, txt = (
            theme.ROJO, "rgba(248,113,113,.55)", "rgba(248,113,113,.12)",
            "rgba(248,113,113,.35)", "IA por debajo")
    return (f'<div style="display:inline-flex; align-items:center; gap:8px; padding:5px 13px;'
            f' border-radius:999px; background:{soft}; border:1px solid {border};">'
            f'<span style="width:8px; height:8px; border-radius:50%; background:{accent};'
            f' box-shadow:0 0 12px {glow};"></span>'
            f'<span style="font-size:12px; font-weight:600; color:rgba(255,255,255,.85);">'
            f'{txt}</span></div>')


# Estilos inline de las KPI cards, copiados del mockup v2.
_KPI_CARD = (
    "position:relative; overflow:hidden;"
    " background:radial-gradient(130% 90% at 15% 0%, rgba(255,255,255,.20),"
    " rgba(255,255,255,.04) 45%, rgba(255,255,255,.02) 100%),"
    " linear-gradient(160deg, rgba(255,255,255,.10), rgba(255,255,255,.03));"
    " backdrop-filter:blur(40px) saturate(180%);"
    " -webkit-backdrop-filter:blur(40px) saturate(180%);"
    " border:1px solid rgba(255,255,255,.18); border-radius:26px;"
    " box-shadow:0 18px 50px rgba(0,0,0,.40), inset 0 1px 0 rgba(255,255,255,.35),"
    " inset 0 -1px 0 rgba(255,255,255,.06); padding:20px 22px;")
_KPI_LBL = ("font-size:11.5px; letter-spacing:.06em; text-transform:uppercase;"
            " color:rgba(255,255,255,.6); font-weight:700;")
_KPI_VAL = ("margin-top:14px; font-size:40px; font-weight:800; letter-spacing:-.02em;"
            " font-family:'JetBrains Mono',monospace;")
_KPI_NOTE = "margin-top:8px; font-size:12.5px; color:rgba(255,255,255,.55); line-height:1.4;"


def _kpi(label: str, value_html: str, note: str, value_style: str = "color:#fff;") -> str:
    return (f'<div style="{_KPI_CARD}">'
            f'<div style="{_KPI_LBL}">{label}</div>'
            f'<div style="{_KPI_VAL} {value_style}">{value_html}</div>'
            f'<div style="{_KPI_NOTE}">{note}</div></div>')


def kpi_cards(resumen: dict) -> str:
    hit = resumen.get("hit_rate")
    alpha = resumen.get("alpha_acumulado")
    n = resumen.get("n") or 0
    ticker = resumen.get("mejor_ticker")
    m_alpha = resumen.get("mejor_alpha")

    hit_v = "—" if _na(hit) else f"{hit:.0f}%"
    if _na(alpha):
        alpha_v, alpha_style = "—", "color:#fff;"
    else:
        col = theme.VERDE if alpha >= 0 else theme.ROJO
        glow = "rgba(74,222,128,.45)" if alpha >= 0 else "rgba(248,113,113,.45)"
        alpha_v = f"{alpha:+.2f}%"
        alpha_style = f"color:{col}; text-shadow:0 0 28px {glow};"
    if _na(ticker):
        mejor_v = "—"
    elif _na(m_alpha):
        mejor_v = html.escape(str(ticker))
    else:
        col = theme.VERDE if m_alpha >= 0 else theme.ROJO
        mejor_v = (f'<span style="font-size:30px">{html.escape(str(ticker))}</span> '
                   f'<span style="font-size:25px; color:{col}">{m_alpha:+.2f}%</span>')

    cards = "".join([
        _kpi("Hit rate vs. S&amp;P 500", hit_v,
             "de las recomendaciones le ganaron al índice"),
        _kpi("Alpha acumulado", alpha_v, "rendimiento sobre el benchmark", alpha_style),
        _kpi("Análisis evaluados", f"{n}", "recomendaciones con veredicto cerrado"),
        _kpi("Mejor recomendación", mejor_v, "mayor alpha del período"),
    ])
    return f'<div class="kpi-grid">{cards}</div>'


def estado_vacio(mensaje: str) -> str:
    return (f'<div class="glass" style="text-align:center;color:rgba(255,255,255,.6)">'
            f'{html.escape(mensaje)}</div>')


def tabla_recos(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return estado_vacio("Sin recomendaciones evaluadas para este filtro. —")
    filas = []
    for _, r in df.iterrows():
        ticker = r.get("ticker") or r.get("activo") or "—"
        alpha = r.get("alpha")
        alpha_cls = "" if _na(alpha) else (" pos" if alpha >= 0 else " neg")
        filas.append(
            "<tr>"
            f'<td><b>{html.escape(str(ticker))}</b></td>'
            f'<td class="num">{_money(r.get("precio_entrada"))}</td>'
            f'<td class="num">{_pct(r.get("crecimiento_estimado"), signo=True)}</td>'
            f'<td class="num">{_pct(r.get("ret_activo"), signo=True)}</td>'
            f'<td class="num{alpha_cls}">{_pct(alpha, signo=True)}</td>'
            f'<td class="num">{_pct(r.get("confianza"))}</td>'
            f'<td>{badge_riesgo(r.get("riesgo"))}</td>'
            f'<td>{badge_veredicto(r.get("veredicto"))}</td>'
            "</tr>"
        )
    cabecera = (
        "<tr><th>Activo</th><th>P. entrada</th><th>Crec. est.</th>"
        "<th>Retorno real</th><th>Alpha</th><th>Confianza</th>"
        "<th>Riesgo</th><th>Veredicto</th></tr>"
    )
    return (f'<div class="glass"><table class="ledger"><thead>{cabecera}</thead>'
            f'<tbody>{"".join(filas)}</tbody></table></div>')
