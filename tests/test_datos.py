"""Filtro puro de la capa de datos (sin Streamlit ni red)."""
import pandas as pd

from grupo3.dashboard import datos


def _df():
    return pd.DataFrame(
        {"ticker": ["A", "B", "C"], "riesgo": ["Moderado", "Riesgosa", "Moderado"]}
    )


def test_aplicar_filtros_por_riesgo():
    out = datos.aplicar_filtros(_df(), "Moderado")
    assert list(out["ticker"]) == ["A", "C"]


def test_aplicar_filtros_todos_no_filtra():
    assert len(datos.aplicar_filtros(_df(), "Todos")) == 3
    assert len(datos.aplicar_filtros(_df(), None)) == 3
