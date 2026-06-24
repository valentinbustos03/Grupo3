"""Carga local: ingiere los .html de data/analisis/ desde DISCO y calcula veredictos.

Pensado para la carga única del batch histórico v1 (o dev local) SIN tener que
pushear primero al repo. Después de verificar, se pushea y la app en la nube los
lee por la API de GitHub.

Uso:
    .venv/bin/python scripts/cargar_local.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grupo3 import db                              # noqa: E402
from grupo3.analisis import metricas, recalcular   # noqa: E402
from grupo3.ingesta import ingestar_local          # noqa: E402


def main() -> None:
    conn = db.connect()
    db.init_db(conn)

    print("→ Ingesta local desde data/analisis/ ...")
    r_ing = ingestar_local(conn)
    print(f"  vistos={r_ing['vistos']} nuevos={r_ing['nuevos']} "
          f"actualizados={r_ing['actualizados']} sin_cambios={r_ing['sin_cambios']}")
    for e in r_ing["errores"]:
        print(f"  ⚠ {e}")

    print("→ Precios (yfinance) + alpha/veredictos ...")
    r_cal = recalcular(conn)
    print(f"  ok={r_cal['ok']} sin_dato={r_cal['sin_dato']} pendientes={r_cal['pendientes']}")

    df = metricas.df_recomendaciones(conn, solo_ok=False)
    print("\n→ Recomendaciones cargadas:")
    cols = ["fecha", "tipo", "ticker", "riesgo", "alpha", "veredicto", "estado_dato"]
    print(df[cols].to_string(index=False) if not df.empty else "  (vacío)")


if __name__ == "__main__":
    main()
