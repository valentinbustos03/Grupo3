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
  dashboard/
    app.py                  # UI Streamlit
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
  en `null`. Se guarda **siempre** `formato_version` por análisis y las métricas se
  filtran por esa columna para **no mezclar series** (hay una fecha de corte experimental).

> El parser se calibra con HTML reales. Pegá un ejemplo v2 y, si tenés, uno v1 viejo.

## Por qué yfinance

Fuente de precios gratuita y **sin API key**, ideal para un experimento académico.
Está detrás de una interfaz `PriceProvider`, así que se puede cambiar por otra fuente
sin tocar el resto del sistema. Benchmark: S&P 500 (`^GSPC`, con fallback a `SPY`).

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
- [ ] Etapa 3 — dashboard fintech dark (sobre el mockup aprobado)
- [ ] Etapa 4 — automatización refresh + deploy
