"""Tests de las ventanas temporales por horizonte (sin dependencias externas)."""
from grupo3.precios import periodos


def test_diario_mismo_dia():
    assert periodos.rango("diario", "2025-06-20") == ("2025-06-20", "2025-06-20")


def test_semanal_lunes_a_domingo():
    # 2025-06-20 es viernes -> lunes 16, domingo 22.
    assert periodos.rango("semanal", "2025-06-20") == ("2025-06-16", "2025-06-22")


def test_mensual_primer_a_ultimo_dia():
    assert periodos.rango("mensual", "2025-06-15") == ("2025-06-01", "2025-06-30")


def test_mensual_febrero_bisiesto():
    assert periodos.rango("mensual", "2024-02-10") == ("2024-02-01", "2024-02-29")
