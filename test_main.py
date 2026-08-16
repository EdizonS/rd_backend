import pytest
from main import calcular_credito, generar_amortizacion
from pydantic import ValidationError
from schemas import SimulacionInput
"""
PRUEBAS PARA VALIDAR EL BACK
"""
# Paramentros para probar la funcionalidad de calcular el credito
@pytest.mark.parametrize(
        "vehiculo, valor_vehiculo, cuota_inicial, plazo, valor_financiado",
        [
            ("moto", 3000000, 300000, 1, 2700000),        # plazo mínimo: 1 mes
            ("bicicleta", 15000000, 3000000, 60, 12000000), # plazo largo: 60 meses
            ("moto", 500001, 0, 12, 500001),                # el mínimo permitido, sin cuota inicial
            ("bicicleta", 2000000, 1999999, 3, 1),          # cuota inicial casi igual al valor (caso límite)
            ("moto", 10000000, 5000000, 36, 5000000),       # financiamiento al 50%
        ]
)
def test_calcular_credito(vehiculo, valor_vehiculo, cuota_inicial, plazo, valor_financiado):
    resultado = calcular_credito(vehiculo, valor_vehiculo, cuota_inicial, plazo)
    assert resultado["valor_financiado"] == valor_financiado
    assert resultado["cuota_mensual"] > 0

#Parametros para validar la amortización en la ultima cuota
@pytest.mark.parametrize(
        "valor_financiado, cuota_mensual, plazo, saldo_final",
        [
            (2700000, 2700000 * 1.02, 1, 0),   # un solo mes — el caso límite que mencioné arriba
            (800000, 140000, 6, 0),
            (12000000, 250000, 60, 0),
            (5000000, 500000, 12, 0),
            (1, 1, 1, 0),                        # valores mínimos posibles, caso extremo

        ]
)
def test_generar_amortizacion_saldo_final_es_cero(valor_financiado, cuota_mensual, plazo,saldo_final):
    tabla = generar_amortizacion(valor_financiado, cuota_mensual, plazo)
    assert tabla[-1]["saldo"] == saldo_final

#Parametros para validar las filas de la tabla de amortizacion con base al plazo
@pytest.mark.parametrize(
        "valor_financiado, cuota_mensual, plazo, meses",
        [
            (2700000, 2700000, 1, 1),      # plazo de 1 mes → debe generar exactamente 1 fila
            (800000, 140000, 6, 6),
            (12000000, 250000, 60, 60),
            (5000000, 500000, 12, 12),
            (500000, 500000, 2, 2),
        ]
)
def test_generar_amortizacion_numero_de_filas_correcto(valor_financiado, cuota_mensual, plazo, meses):
    tabla = generar_amortizacion(valor_financiado, cuota_mensual, plazo)
    assert len(tabla) == meses

"""
PRUEBAS PARA VERIFICAR VALIDACIONES
"""
def test_rechaza_valor_vehiculo_menor_a_500000():
    with pytest.raises(ValidationError):
        SimulacionInput(tipo_vehiculo="moto", valor_vehiculo=100000, cuota_inicial=0, plazo_meses=12)

def test_rechaza_cuota_inicial_mayor_al_valor_vehiculo():
    with pytest.raises(ValidationError):
        SimulacionInput(tipo_vehiculo="moto", valor_vehiculo=1000000, cuota_inicial=2000000, plazo_meses=12)

def test_rechaza_plazo_cero():
    with pytest.raises(ValidationError):
        SimulacionInput(tipo_vehiculo="moto", valor_vehiculo=1000000, cuota_inicial=0, plazo_meses=0)