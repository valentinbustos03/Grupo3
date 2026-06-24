"""Crea data/analisis/AAAA-MM-DD_<tipo>.html a partir de un reporte v1 pegado.

El texto viejo se envuelve en un .html mínimo (en <pre>, para conservar los
saltos de línea que la heurística v1 necesita). El nombre del archivo fija
fecha y tipo (de ahí los toma el parser).

Uso:
    .venv/bin/python scripts/nuevo_v1.py 2026-06-18 diario < reporte.txt
    pbpaste | .venv/bin/python scripts/nuevo_v1.py 2026-06-11 diario
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grupo3 import config              # noqa: E402
from grupo3.ingesta import texto_a_html  # noqa: E402

_TIPOS = {"diario", "semanal", "mensual"}


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in _TIPOS:
        print("uso: nuevo_v1.py AAAA-MM-DD diario|semanal|mensual < texto")
        sys.exit(1)

    fecha, tipo = sys.argv[1], sys.argv[2]
    texto = sys.stdin.read()
    if not texto.strip():
        print("error: no llegó texto por stdin")
        sys.exit(1)

    dest = config.ROOT / config.DATA_DIR / f"{fecha}_{tipo}.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(texto_a_html(texto), encoding="utf-8")
    print(f"escrito {dest}")


if __name__ == "__main__":
    main()
