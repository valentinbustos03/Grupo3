# Grupo3 — Dashboard de análisis bursátil IA vs S&P 500

Dashboard que mide qué tan bien le va a las recomendaciones de mercado generadas
por IA (Claude) **frente al S&P 500** en tres horizontes: diario, semanal y mensual.

La IA genera cada análisis por fuera de este proyecto (una *Routine* de Claude Code
en la nube) y **commitea el HTML a un repo de GitHub** — esa es la **única fuente de
verdad**. Este proyecto es el dashboard: lee esos HTML, los parsea, trae precios de
cierre y del S&P 500 con `yfinance`, calcula veredictos relativos al índice y muestra
todo en una UI hosteada en **Streamlit Community Cloud** (gratis, siempre encendida).
No depende de la PC del autor ni de Gmail.

## Arquitectura

```
Routine Claude (nube)  ──commit HTML──►  Repo GitHub (data/analisis/)  ◄── fuente de verdad
                                               │
                                               ▼  (GitHub API, HTTP)
        ┌──────────────────────── ESTE PROYECTO ────────────────────────┐
        │  ingesta  →  SQLite  →  precios (yfinance)  →  análisis  →  dashboard │
        └────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
                                   Streamlit Cloud (URL pública)
```

## Estructura del código

```
streamlit_app.py            # entry point (Streamlit Cloud lo detecta por convención)
requirements.txt
.streamlit/config.toml      # tema dark
grupo3/
  config.py                 # repo, benchmark, umbral, fecha de corte, paths, token
  db/
    schema.sql              # tablas analisis + recomendaciones
    database.py             # conexión + helpers (upsert idempotente)
  ingesta/
    github_client.py        # lista y descarga los HTML del repo (GitHub API)
    parser.py               # parser tolerante v1 (histórico) y v2 (nuevo)
    ingest.py               # orquesta: GitHub → parser → SQLite
  precios/
    provider.py             # interfaz PriceProvider + YFinanceProvider
    periodos.py             # ventanas por horizonte (diario/semanal/mensual)
  analisis/
    veredicto.py            # alpha y veredicto relativo al S&P 500
    metricas.py             # métricas agregadas (Etapa 2)
    candlestick.py          # candlestick comparativo normalizado (Etapa 2b)
  dashboard/                # UI Streamlit (Etapa 3)
    app.py                  # entrypoint: tema + st.navigation (Panel + Metodología)
    theme.py                # tokens de color, layout Plotly, CSS "Liquid Glass"
    componentes.py          # builders HTML puros (masthead, KPI cards, tabla, badges)
    figuras.py              # figuras Plotly (equity, calibración, candlestick)
    datos.py                # conexión cacheada + filtros + acción Actualizar
    panel.py                # página principal (KPIs, figuras, tabla)
    metodologia.py          # página de documentación del experimento
```

## Setup local

Requiere Python 3.11+. En Debian/Ubuntu, para usar venv:

```bash
sudo apt install python3.12-venv          # solo la primera vez
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Cómo se conecta al repo

La ingesta lee los HTML con la **API de contenidos de GitHub** (HTTP), no clonando
el repo. Motivo: en Streamlit Cloud no hay garantía de tener `git` ni disco
persistente; la API sólo necesita HTTP y, opcionalmente, un token. Para un repo
**público** funciona anónima (con un rate limit bajo); para repos **privados** o más
cuota, se pasa un token (ver *Deploy*).

- Carpeta leída en el repo: `data/analisis/` (configurable en `grupo3/config.py`).
- Nombre de archivo esperado: `AAAA-MM-DD_<tipo>.html` (`tipo` = diario|semanal|mensual).
- Idempotencia: la clave es `(fecha, tipo)`; se reingiere sólo si cambió el contenido
  (se compara el `sha` de git del archivo).

## Formatos de análisis (v1 / v2)

- **v2 (nuevo, estandarizado):** se parsea por atributos `data-*`
  (`[data-analisis]`, `data-tipo`, `data-fecha`, `data-formato-version`, `[data-reco]`,
  `data-activo`, `data-campo="..."`).
- **v1 (histórico, inconsistente):** parser tolerante; lo que no se puede extraer queda
  en `null`. Se guarda **siempre** `formato_version` por análisis, pero es **sólo un
  registro informativo** del formato que tenía el HTML al generarse: no separa ni filtra
  las métricas. Las métricas combinan v1 + v2 (los `null` ya se excluyen porque sólo
  computan recomendaciones con `estado_dato='ok'`).

> El parser se calibra con HTML reales. Pegá un ejemplo v2 y, si tenés, uno v1 viejo.

## Por qué yfinance

Fuente de precios gratuita y **sin API key**, ideal para un experimento académico.
Está detrás de una interfaz `PriceProvider`, así que se puede cambiar por otra fuente
sin tocar el resto del sistema. Benchmark: S&P 500 (`^GSPC`, con fallback a `SPY`).

## Dashboard (Etapa 3)

UI estética "Liquid Glass" (dark glassmorphism, acentos verde/rojo por veredicto),
construida sobre el mockup `design/dashboard-v2.html`. Se corre local con:

```bash
streamlit run streamlit_app.py
```

Tiene **dos páginas** (navegación arriba, `st.navigation`):

- **Panel** — masthead, filtros (horizonte diario/semanal/mensual + nivel de riesgo) y
  botón *Actualizar*; **4 KPI cards** (hit rate vs S&P 500, alpha acumulado, recos
  evaluadas, mejor recomendación); **Fig. 1** curva de retorno acumulado (IA vs S&P 500),
  **Fig. 2** vela comparativa normalizada a base 100, **Fig. 3** calibración (confianza
  declarada vs aciertos reales); y la tabla de recomendaciones con badges por riesgo y
  veredicto.
- **Metodología** — documentación dentro del propio dashboard: qué mide el experimento,
  la *Routine* generadora, la arquitectura, la fórmula del veredicto, la normalización
  del candlestick, el registro de formato v1/v2 y el deploy.

**Cómo se construyó (build híbrido):** Streamlit no hace `backdrop-filter` + aurora
animada de forma nativa, así que el masthead, las KPI cards y la tabla se renderizan
como HTML inyectado con los estilos exactos del mockup (clase `.glass`), mientras que
las 3 figuras usan **Plotly** tematizado (fondo transparente, paleta del tema) para
seguir siendo interactivas, y los filtros + refresh son widgets de Streamlit. Un CSS
global fija la aurora de fondo y oculta el chrome default de Streamlit. Los tokens de
color y el CSS viven en `grupo3/dashboard/theme.py` (una sola fuente de verdad).

## Veredicto (relativo al S&P 500)

```
ret_activo = (cierre_activo / entrada_activo - 1) * 100
ret_sp500  = (cierre_sp500  / entrada_sp500  - 1) * 100
alpha      = ret_activo - ret_sp500

GANO    si alpha >  umbral        (le ganó al índice)
PERDIO  si alpha < -umbral        (quedó por debajo)
NEUTRO  si |alpha| <= umbral      (umbral configurable, default 0.1%)
```

Además se guarda el **acierto absoluto** (`ret_activo > 0`) y si la **dirección** del
crecimiento estimado por el modelo coincidió con el retorno real (calibración).

## Normalización del candlestick (Etapa 2b)

Una acción a ~$195 y el índice a ~5000 puntos no son comparables en escala directa.
Por eso cada serie OHLC se **normaliza a base 100 en la apertura del período**:

```
normalizado = serie / Open[primer día del período] * 100
```

Así ambas velas (activo y S&P 500) arrancan en 100 y se ve en % quién subió/bajó más.
Color del activo: verde si le ganó al índice, rojo si perdió. Librería: Plotly.

## Estrategia de datos (SQLite efímera)

Streamlit Cloud reinicia el contenedor, así que la base SQLite puede perderse. El
diseño la trata como **reconstruible**: en cada arranque (o con el botón *Actualizar*)
se reingieren los HTML del repo y se vuelven a pedir los precios a yfinance. No hay
estado crítico fuera del repo + yfinance.

## Deploy en Streamlit Community Cloud

1. Subí este proyecto a GitHub (mismo repo o uno aparte).
2. En https://share.streamlit.io → *New app* → conectá el repo y la branch.
3. *Main file path*: `streamlit_app.py`.
4. Si el repo de los HTML es **privado** (o querés más cuota de API), en
   *Advanced settings → Secrets* agregá:
   ```toml
   GITHUB_TOKEN = "ghp_xxx"   # token con permiso de lectura al repo
   ```
5. *Deploy*. La URL pública resultante es la que se le pasa al profesor.

## Carga de datos

Los análisis viven en `data/analisis/` del repo, nombrados
`AAAA-MM-DD_<tipo>.html` (el nombre fija fecha y tipo; imprescindible para v1).

- **v2 (≥ 2026-06-19):** la *Routine* de Claude los commitea automáticamente. La
  app los lee por la API de GitHub al tocar **Actualizar**.
- **v1 (≤ 2026-06-18, histórico, carga única):** se cargan una sola vez. Si están
  como texto pegado, se envuelven en `.html` y se cargan localmente para verificar
  antes de pushear:

```bash
# 1) crear el .html a partir del reporte viejo pegado
.venv/bin/python scripts/nuevo_v1.py 2026-06-18 diario < reporte.txt

# 2) ingerir desde disco (sin pushear) + traer precios + calcular veredictos
.venv/bin/python scripts/cargar_local.py

# 3) si los veredictos se ven bien -> commit + push de data/analisis/
```

`scripts/cargar_local.py` usa `ingestar_local()` (lee del disco); en producción la
app usa `ingestar()` (lee de GitHub). Mismo parser y misma persistencia.

## Tests

```bash
.venv/bin/python -m pytest tests/ -q
```

La lógica pura (parser v1/v2, veredicto, ventanas, métricas, orquestación con un
`PriceProvider` falso) se testea sin red. Sólo el smoke de `YFinanceProvider`
toca internet.

> Nota de entorno: si `python3 -m venv` falla por `ensurepip` (Debian/Ubuntu sin
> `python3-venv`), se puede crear el venv sin pip y bootstrappearlo:
> `python3 -m venv --without-pip .venv && .venv/bin/python <(curl -sS https://bootstrap.pypa.io/get-pip.py)`.

## Estado de avance

- [x] Etapa 1 — ingesta GitHub → parser v1/v2 → SQLite (idempotente)
- [x] Etapa 2 — precios yfinance + benchmark S&P 500 + alpha/veredicto + métricas
- [x] Etapa 2b — candlestick comparativo normalizado (base 100)
- [x] Etapa 3 — dashboard "Liquid Glass" (Panel + Metodología) sobre el mockup v2
- [ ] Etapa 4 — automatización refresh + deploy en Streamlit Cloud
