"""Tests de la ingesta local desde disco (sin red)."""
from pathlib import Path

from grupo3 import db
from grupo3.ingesta import ingestar_local, texto_a_html

FX = Path(__file__).parent / "fixtures"


def test_ingestar_local_v1_y_v2(tmp_path):
    data = tmp_path / "analisis"
    data.mkdir()
    # v2 (atributos data-*)
    (data / "2025-06-20_diario.html").write_text(
        (FX / "2025-06-20_diario.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    # v1 (texto viejo envuelto en .html)
    (data / "2026-06-18_diario.html").write_text(
        texto_a_html((FX / "v1" / "2026-06-18_diario.txt").read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    conn = db.connect(str(tmp_path / "t.db"))
    db.init_db(conn)

    r = ingestar_local(conn, carpeta=data)
    assert r["nuevos"] == 2
    assert r["errores"] == []
    assert conn.execute("SELECT COUNT(*) FROM analisis").fetchone()[0] == 2

    # El v1 extrajo los tickers por heurística.
    tickers = {row[0] for row in conn.execute(
        "SELECT ticker FROM recomendaciones WHERE ticker IS NOT NULL")}
    assert {"QQQ", "NVDA", "ACN"} <= tickers

    # Idempotencia: re-correr no duplica ni reprocesa.
    r2 = ingestar_local(conn, carpeta=data)
    assert r2["nuevos"] == 0
    assert r2["sin_cambios"] == 2


def test_ingestar_local_carpeta_inexistente(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_db(conn)
    r = ingestar_local(conn, carpeta=tmp_path / "no_existe")
    assert r["vistos"] == 0
    assert r["errores"]                       # reporta, no rompe
