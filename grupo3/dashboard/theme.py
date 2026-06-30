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
    """Devuelve el bloque <style> completo del tema (fiel al mockup v2)."""
    _GLASS_BG = (
        "radial-gradient(120% 80% at 10% 0%, rgba(255,255,255,.22),"
        " rgba(255,255,255,.05) 50%, rgba(255,255,255,.02) 100%),"
        " linear-gradient(160deg, rgba(255,255,255,.13), rgba(255,255,255,.04))"
    )
    _GLASS_BORDER = "1px solid rgba(255,255,255,.17)"
    _GLASS_SHADOW = (
        "0 20px 56px rgba(0,0,0,.42),"
        " inset 0 1px 0 rgba(255,255,255,.34),"
        " inset 0 -1px 0 rgba(255,255,255,.06)"
    )
    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@600;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {{
  --verde:{VERDE}; --rojo:{ROJO}; --violeta:{VIOLETA}; --cian:{CIAN};
}}

/* === Ocultar sidebar y chrome de Streamlit ========================== */
[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="collapsedControl"],
button[kind="sidebarButton"] {{
  display: none !important;
}}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
html, body, [class*="css"] {{ font-family: 'Inter', system-ui, sans-serif; }}

/* === Fondo + aurora (opacidades del mockup v2) ====================== */
[data-testid="stAppViewContainer"] {{ background: {FONDO}; }}
[data-testid="stAppViewContainer"]::before {{
  content: ""; position: fixed; inset: -8%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(620px 520px at 10% 12%, rgba(167,139,250,.42), transparent 60%),
    radial-gradient(680px 560px at 90%  6%, rgba(56,189,248,.33), transparent 62%),
    radial-gradient(720px 640px at 82% 96%, rgba(74,222,128,.30), transparent 60%),
    radial-gradient(560px 500px at 16% 98%, rgba(248,113,113,.26), transparent 58%);
  animation: auroraShift 22s ease-in-out infinite;
}}
[data-testid="stAppViewContainer"]::after {{
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: linear-gradient(180deg, rgba(5,6,10,.20), rgba(5,6,10,.66));
}}
@keyframes auroraShift {{
  0%   {{ transform: translate3d(0,0,0) scale(1); }}
  50%  {{ transform: translate3d(2%,-1.5%,0) scale(1.06); }}
  100% {{ transform: translate3d(0,0,0) scale(1); }}
}}
.block-container {{
  position: relative; z-index: 1;
  padding: 26px 30px 56px !important;
  max-width: 1300px !important;
}}

/* === Topnav (Panel / Metodología) ================================== */
.topnav {{
  display: flex; gap: 8px; justify-content: flex-end;
  margin-bottom: 14px;
}}
.topnav a {{
  text-decoration: none; padding: 5px 16px; border-radius: 999px;
  font-size: 13px; font-weight: 600;
  transition: background .15s, color .15s;
}}
.topnav a.active {{
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22); color: #fff;
}}
.topnav a:not(.active) {{
  background: transparent; border: 1px solid rgba(255,255,255,.10);
  color: rgba(255,255,255,.55);
}}

/* === Masthead (glass card del header) =============================== */
.mh-anchor {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.mh-anchor) {{
  position: relative; overflow: hidden;
  background:
    radial-gradient(140% 120% at 12% -10%, rgba(255,255,255,.26),
      rgba(255,255,255,.06) 45%, rgba(255,255,255,.02) 100%),
    linear-gradient(160deg, rgba(255,255,255,.13), rgba(255,255,255,.04));
  backdrop-filter: blur(48px) saturate(200%);
  -webkit-backdrop-filter: blur(48px) saturate(200%);
  border: 1px solid rgba(255,255,255,.22) !important;
  border-radius: 28px !important;
  box-shadow: 0 22px 60px rgba(0,0,0,.50),
    inset 0 1.5px 0 rgba(255,255,255,.50),
    inset 0 -1px 0 rgba(255,255,255,.08);
  padding: 28px 32px 22px !important; margin-bottom: 20px !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.mh-anchor)::before {{
  content: ""; position: absolute; top: -40%; left: -10%;
  width: 60%; height: 180%;
  background: linear-gradient(105deg, transparent, rgba(255,255,255,.12), transparent);
  transform: skewX(-18deg); pointer-events: none;
}}
/* divisor interno del masthead */
.mh-sep {{
  border: none; border-top: 1px solid rgba(255,255,255,.10);
  margin: 16px 0 12px;
}}

/* Controles derecha del masthead */
.ctl-label {{
  font-size: 11px; letter-spacing: .1em; text-transform: uppercase;
  color: rgba(255,255,255,.55); font-weight: 700;
  margin: 0 0 8px; text-align: right;
}}
[data-testid="stSegmentedControl"] {{ justify-content: flex-end; }}
[data-testid="stSegmentedControl"] [role="radiogroup"] {{
  gap: 4px;
  background: rgba(255,255,255,.07);
  border: 1px solid rgba(255,255,255,.16);
  border-radius: 16px; padding: 5px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.22), 0 8px 24px rgba(0,0,0,.3);
}}
[data-testid="stSegmentedControl"] button {{
  border: 0 !important; border-radius: 12px !important;
  background: transparent !important;
  color: rgba(255,255,255,.7) !important; font-weight: 600 !important;
}}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[data-selected="true"],
[data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] {{
  background: rgba(255,255,255,.14) !important; color: #fff !important;
}}
.pill-wrap {{ margin-top: 14px; display: flex; justify-content: flex-end; }}

/* Selectbox dentro del glass card */
[data-testid="stVerticalBlockBorderWrapper"]:has(.mh-anchor) [data-testid="stSelectbox"] > div > div {{
  background: rgba(255,255,255,.07) !important;
  border: 1px solid rgba(255,255,255,.16) !important;
  border-radius: 12px !important;
  color: rgba(255,255,255,.85) !important;
}}

/* Botón Actualizar — ghost pill */
[data-testid="stVerticalBlockBorderWrapper"]:has(.mh-anchor) button[kind="secondary"] {{
  background: rgba(255,255,255,.08) !important;
  border: 1px solid rgba(255,255,255,.20) !important;
  border-radius: 12px !important;
  color: rgba(255,255,255,.85) !important;
  font-weight: 600 !important;
  transition: background .15s !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:has(.mh-anchor) button[kind="secondary"]:hover {{
  background: rgba(255,255,255,.14) !important;
  border-color: rgba(255,255,255,.30) !important;
}}

/* === KPI cards ====================================================== */
.kpi-grid {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  margin-bottom: 20px;
}}

/* === Chart/Table glass containers (anchor: .gc) ==================== */
.gc {{ display: none; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(.gc) {{
  position: relative; overflow: hidden;
  background: {_GLASS_BG};
  backdrop-filter: blur(42px) saturate(180%);
  -webkit-backdrop-filter: blur(42px) saturate(180%);
  border: {_GLASS_BORDER} !important;
  border-radius: 28px !important;
  box-shadow: {_GLASS_SHADOW};
  padding: 22px 24px 16px !important; margin-bottom: 20px !important;
}}

/* === Tabla ledger =================================================== */
.ledger {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
.ledger th {{
  text-align: left; font-weight: 700; color: rgba(255,255,255,.5);
  font-size: 11px; letter-spacing: .05em; text-transform: uppercase;
  padding: 0 12px 11px; border-bottom: 1px solid rgba(255,255,255,.12);
}}
.ledger td {{
  padding: 13px 12px; border-bottom: 1px solid rgba(255,255,255,.07);
  color: rgba(255,255,255,.86);
}}
.ledger td.num {{
  font-family: 'JetBrains Mono', monospace; text-align: right;
}}
.ledger tr:hover td {{ background: rgba(255,255,255,.04); }}

/* Barra de confianza */
.conf-bar-wrap {{
  display: flex; align-items: center; gap: 9px;
}}
.conf-bar {{
  flex: 1; height: 6px; background: rgba(255,255,255,.12);
  border-radius: 3px; overflow: hidden; max-width: 100px;
}}
.conf-bar-fill {{
  height: 100%; background: {VERDE}; border-radius: 3px;
}}

/* Badges */
.badge {{
  display: inline-block; padding: 4px 11px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600; border: 1px solid; white-space: nowrap;
}}

.pos {{ color: {VERDE}; }} .neg {{ color: {ROJO}; }}

/* === Metodología ==================================================== */
.doc h2 {{ color: #fff; font-size: 22px; margin: 4px 0 8px; }}
.doc p, .doc li {{
  color: rgba(255,255,255,.78); line-height: 1.6; font-size: 15px;
}}
.doc code {{
  background: rgba(255,255,255,.08); padding: 1px 6px; border-radius: 6px;
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
}}
.flow {{
  font-family: 'JetBrains Mono', monospace;
  color: rgba(255,255,255,.82); font-size: 13.5px; line-height: 1.9;
}}
</style>"""


def inject_css() -> None:
    """Inyecta el CSS del tema (idempotente por rerun de Streamlit)."""
    import streamlit as st  # import perezoso: build_css es testeable sin Streamlit

    st.markdown(build_css(), unsafe_allow_html=True)
