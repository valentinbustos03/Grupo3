"""Builders de HTML del dashboard (puros). Devuelven strings con clases del tema."""
from __future__ import annotations

import html

import pandas as pd

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


def masthead() -> str:
    return (
        '<div class="glass">'
        '<p class="masthead-kicker">Experimento de inversión · Grupo 3</p>'
        '<h1 class="masthead-title">Recomendaciones de IA vs S&amp;P 500</h1>'
        '<p class="masthead-sub">Cada análisis genera 3 recomendaciones; el '
        'veredicto es <b>relativo al S&amp;P 500</b> (alpha) en el horizonte '
        'elegido. Datos del experimento, no es asesoramiento financiero.</p>'
        '</div>'
    )


def _kpi(label: str, value_html: str, note: str) -> str:
    return (f'<div class="glass"><p class="kpi-label">{label}</p>'
            f'<p class="kpi-value">{value_html}</p>'
            f'<p class="kpi-note">{note}</p></div>')


def kpi_cards(resumen: dict) -> str:
    hit = resumen.get("hit_rate")
    alpha = resumen.get("alpha_acumulado")
    n = resumen.get("n") or 0
    ticker = resumen.get("mejor_ticker")
    m_alpha = resumen.get("mejor_alpha")

    hit_html = "—" if _na(hit) else f'{hit:.0f}<span class="muted">%</span>'
    if _na(alpha):
        alpha_html = "—"
    else:
        cls = "pos" if alpha >= 0 else "neg"
        alpha_html = f'<span class="{cls}">{alpha:+.2f}%</span>'
    ticker_html = "—" if _na(ticker) else html.escape(str(ticker))

    cards = "".join([
        _kpi("Hit rate vs S&amp;P 500", hit_html,
             "de las recomendaciones le ganaron al índice"),
        _kpi("Alpha acumulado", alpha_html, "suma de alphas vs el benchmark"),
        _kpi("Recomendaciones", f'{n}', "evaluadas con veredicto cerrado"),
        _kpi("Mejor recomendación", ticker_html,
             "—" if _na(m_alpha) else f"{m_alpha:+.2f}% de alpha en el período"),
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
