"""Tema 'Liquid Glass': tokens de color, layout Plotly y CSS inyectado.

El CSS recrea el mockup v2 (design/dashboard-v2.html): fondo near-black con
aurora animada, glass cards con backdrop-filter, y oculta el chrome default de
Streamlit. ``build_css`` es puro (testeable); ``inject_css`` lo manda a la UI.
"""
from __future__ import annotations

# --- Tokens ------------------------------------------------------------------
FONDO = "#05060a"
VERDE = "#4ade80"      # GANÓ
ROJO = "#f87171"       # PERDIÓ
NEUTRO = "#9ca3af"
VIOLETA = "#a78bfa"
CIAN = "#38bdf8"
AMBAR = "#fbbf24"
NARANJA = "#fb923c"
GRIS = "#6b7280"
TEXTO = "#e6edf3"

RIESGO_COLOR = {
    "Muy segura": "#4ade80",
    "Segura": "#a3e635",
    "Moderado": "#fbbf24",
    "Riesgosa": "#fb923c",
    "Muy Riesgosa": "#f87171",
}
VEREDICTO_COLOR = {"GANO": VERDE, "PERDIO": ROJO, "NEUTRO": NEUTRO}


def rgba(hex_color: str, alpha: float) -> str:
    """Token hex ``#rrggbb`` -> string ``rgba(r,g,b,alpha)``.

    Plotly no acepta hex con alpha (#rrggbbaa); para tintes translúcidos
    derivados de la paleta se convierte acá, manteniendo una sola fuente de
    verdad del color.
    """
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# --- Plotly ------------------------------------------------------------------
def plotly_layout() -> dict:
    """Kwargs comunes para ``fig.update_layout`` (no incluye títulos de eje)."""
    return {
        "template": "plotly_dark",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, system-ui, sans-serif",
                 "color": "rgba(255,255,255,.78)"},
        "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.04,
                   "x": 0, "bgcolor": "rgba(0,0,0,0)"},
        "margin": {"l": 50, "r": 24, "t": 30, "b": 40},
        "xaxis": {"gridcolor": "rgba(255,255,255,.06)",
                  "zerolinecolor": "rgba(255,255,255,.12)"},
        "yaxis": {"gridcolor": "rgba(255,255,255,.06)",
                  "zerolinecolor": "rgba(255,255,255,.12)"},
        "hoverlabel": {"font": {"family": "Inter, sans-serif"}},
    }


# --- CSS ---------------------------------------------------------------------
def build_css() -> str:
    """Devuelve el bloque <style> completo del tema."""
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

:root {{
  --verde: {VERDE}; --rojo: {ROJO}; --violeta: {VIOLETA}; --cian: {CIAN};
}}

/* Fondo + reset del chrome de Streamlit */
[data-testid="stAppViewContainer"] {{ background: {FONDO}; }}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
[data-testid="stSidebarNav"] {{ padding-top: .5rem; }}
html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}

/* Aurora fija detrás de todo */
[data-testid="stAppViewContainer"]::before {{
  content: ""; position: fixed; inset: -8%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(620px 520px at 10% 12%, rgba(167,139,250,.30), transparent 60%),
    radial-gradient(680px 560px at 90% 6%, rgba(56,189,248,.22), transparent 60%),
    radial-gradient(720px 640px at 50% 110%, rgba(74,222,128,.12), transparent 60%);
  animation: auroraShift 22s ease-in-out infinite;
}}
@keyframes auroraShift {{
  0% {{ transform: translate3d(0,0,0) scale(1); }}
  50% {{ transform: translate3d(2%,-1.5%,0) scale(1.06); }}
  100% {{ transform: translate3d(0,0,0) scale(1); }}
}}
.block-container {{ position: relative; z-index: 1; padding-top: 2.2rem; max-width: 1180px; }}

/* Glass card reutilizable */
.glass {{
  position: relative; overflow: hidden;
  background:
    radial-gradient(130% 90% at 15% 0%, rgba(255,255,255,.16), rgba(255,255,255,.03) 50%, rgba(255,255,255,.02) 100%),
    linear-gradient(160deg, rgba(255,255,255,.09), rgba(255,255,255,.03));
  backdrop-filter: blur(22px) saturate(160%);
  -webkit-backdrop-filter: blur(22px) saturate(160%);
  border: 1px solid rgba(255,255,255,.16); border-radius: 22px;
  box-shadow: 0 20px 60px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.18);
  padding: 22px 24px; margin-bottom: 18px;
}}

/* Masthead */
.masthead-kicker {{ font-size: 12px; letter-spacing: .18em; text-transform: uppercase;
  color: rgba(255,255,255,.55); margin: 0 0 6px; }}
.masthead-title {{ font-size: 54px; font-weight: 700; line-height: 1.05; margin: 0;
  letter-spacing: -.01em;
  background: linear-gradient(125deg, #ffffff 0%, {VIOLETA} 42%, {VERDE} 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; }}
.masthead-sub {{ color: rgba(255,255,255,.6); margin: 10px 0 0; font-size: 15px; }}

/* KPI cards */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 6px; }}
.kpi-label {{ font-size: 12px; letter-spacing: .08em; text-transform: uppercase;
  color: rgba(255,255,255,.55); margin: 0 0 10px; }}
.kpi-value {{ font-family: 'JetBrains Mono', monospace; font-size: 34px; font-weight: 700;
  line-height: 1; margin: 0; }}
.kpi-note {{ font-size: 12.5px; color: rgba(255,255,255,.5); margin: 10px 0 0; }}
.pos {{ color: {VERDE}; }} .neg {{ color: {ROJO}; }} .muted {{ color: rgba(255,255,255,.7); }}

/* Tabla ledger */
.ledger {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
.ledger th {{ text-align: left; font-weight: 600; color: rgba(255,255,255,.55);
  font-size: 11.5px; letter-spacing: .06em; text-transform: uppercase;
  padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,.12); }}
.ledger td {{ padding: 11px 12px; border-bottom: 1px solid rgba(255,255,255,.06);
  color: rgba(255,255,255,.86); }}
.ledger td.num {{ font-family: 'JetBrains Mono', monospace; text-align: right; }}
.ledger tr:hover td {{ background: rgba(255,255,255,.03); }}

/* Badges */
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600; border: 1px solid; white-space: nowrap; }}

/* Metodología */
.doc h2 {{ color: #fff; font-size: 22px; margin: 4px 0 8px; }}
.doc p, .doc li {{ color: rgba(255,255,255,.78); line-height: 1.6; font-size: 15px; }}
.doc code {{ background: rgba(255,255,255,.08); padding: 1px 6px; border-radius: 6px;
  font-family: 'JetBrains Mono', monospace; font-size: 13px; }}
.flow {{ font-family: 'JetBrains Mono', monospace; color: rgba(255,255,255,.82);
  font-size: 13.5px; line-height: 1.9; }}
</style>"""


def inject_css() -> None:
    """Inyecta el CSS del tema (idempotente por rerun de Streamlit)."""
    import streamlit as st  # import perezoso: build_css es testeable sin Streamlit

    st.markdown(build_css(), unsafe_allow_html=True)
