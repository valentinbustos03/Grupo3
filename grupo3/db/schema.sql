-- Esquema SQLite del dashboard.
-- Se separan dos series por formato_version (corte experimental): las métricas
-- filtran siempre por formato_version para no mezclar v1 (histórico) con v2.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS analisis (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo             TEXT    NOT NULL CHECK (tipo IN ('diario','semanal','mensual')),
    fecha            TEXT    NOT NULL,              -- ISO AAAA-MM-DD
    formato_version  INTEGER NOT NULL,             -- 1 (histórico) | 2 (nuevo)
    ruta_archivo     TEXT    NOT NULL,
    hash_contenido   TEXT,                          -- detecta re-ingesta del mismo archivo
    creado_en        TEXT    NOT NULL,
    UNIQUE (fecha, tipo)                            -- idempotencia: 1 análisis por fecha+tipo
);

CREATE TABLE IF NOT EXISTS recomendaciones (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    analisis_id          INTEGER NOT NULL REFERENCES analisis(id) ON DELETE CASCADE,
    -- Datos parseados del HTML (en v1 pueden venir NULL: parser tolerante)
    activo               TEXT,
    ticker               TEXT,                       -- símbolo normalizado para yfinance
    precio_entrada       REAL,
    factores             TEXT,
    crecimiento_estimado REAL,                       -- % estimado por el modelo
    confianza            REAL,                       -- %
    riesgo               TEXT,                       -- Muy segura|Segura|Moderado|Riesgosa|Muy Riesgosa
    -- Datos de mercado (Etapa 2, yfinance)
    precio_entrada_real  REAL,                       -- apertura del período
    precio_cierre_real   REAL,                       -- cierre del período
    sp500_entrada        REAL,
    sp500_cierre         REAL,
    -- Cálculos (Etapa 2)
    ret_activo           REAL,                       -- %
    ret_sp500            REAL,                       -- %
    alpha                REAL,                       -- ret_activo - ret_sp500
    veredicto            TEXT,                       -- GANO|PERDIO|NEUTRO
    acierto_absoluto     INTEGER,                    -- bool: ret_activo > 0
    direccion_coincide   INTEGER,                    -- bool: signo(estimado)==signo(real)
    estado_dato          TEXT DEFAULT 'pendiente',   -- pendiente|ok|sin_dato
    calculado_en         TEXT
);

CREATE INDEX IF NOT EXISTS idx_reco_analisis ON recomendaciones(analisis_id);
CREATE INDEX IF NOT EXISTS idx_analisis_tipo ON analisis(tipo, formato_version);
