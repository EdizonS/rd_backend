from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine, Base
from models import Solicitud_credito
from schemas import SimulacionInput, SolicitudInput, SolicitudOutput
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine) # Crea las tablas en la base de datos si no existen, utilizando la metadata de SQLAlchemy y el motor de la base de datos definido en engine.

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://rd-frontend.vercel.app"],
    allow_methods = ["*"],
    allow_headers = ["*"]
)

def efectiva_anual_a_mensual(Tasa_EA: float):
    """
    Convierte la tasa Efectiva Anual a su equivalente mensual, en este ejemplo como no tenemos la tasa efectiva anual, 
    se toma como ejemplo una tasa del 25% la cual es inferior a la tasa de usura en Colombia, que es del 29.66% para el segundo semestre del año 2026.
    """   
    tasa_decimal = Tasa_EA / 100
    mensual_efectiva = (1 + tasa_decimal) ** (1 / 12) - 1
    return mensual_efectiva

TASA_MENSUAL = efectiva_anual_a_mensual(25.0) # Pasamos en este llamado el valor de la tasa efectiva anual.

def calcular_credito(tipo_vehiculo: str, valor_vehiculo: float, cuota_inicial: float, plazo_meses: int):
    # Lógica para calcular el crédito
    valor_financiado = round(valor_vehiculo - cuota_inicial,2)
    cuota_mensual = round(valor_financiado * (TASA_MENSUAL * (1 + TASA_MENSUAL) ** plazo_meses) / ((1 + TASA_MENSUAL) ** plazo_meses - 1),2)
    total_a_pagar = round(cuota_mensual * plazo_meses,2)
    total_intereses = round(total_a_pagar - valor_financiado,2)
    return {
        "tipo_vehiculo": tipo_vehiculo,
        "valor_vehiculo": valor_vehiculo,
        "cuota_inicial": cuota_inicial,
        "plazo_meses": plazo_meses,
        "valor_financiado": valor_financiado,
        "cuota_mensual": cuota_mensual,
        "total_intereses": total_intereses,
        "total_a_pagar": total_a_pagar
        }

def generar_amortizacion(valor_financiado: float, cuota_mensual: float, plazo_meses: int):
    # Lógica para generar la tabla de amortización
    tabla = []
    saldo = valor_financiado

    # Para calcular del mes 1 al mes n, se hace un ciclo for que recorra el rango de 1 a plazo_meses + 1
    for mes in range(1, plazo_meses + 1):
        interes_mes = round(saldo * TASA_MENSUAL,2)
        abono_capital = round(cuota_mensual - interes_mes,2)

        if mes == plazo_meses:
            abono_capital = saldo  # Ajuste del último abono para que el saldo llegue a cero
            cuota_mensual_final = abono_capital + interes_mes
        else:
            cuota_mensual_final = cuota_mensual

        saldo = round(saldo - abono_capital,2)

        tabla.append({
            "numero_cuota": mes,
            "cuota_mensual": cuota_mensual_final,
            "interes": interes_mes,
            "abono_capital": abono_capital,
            "saldo": saldo
            })
    return tabla

# ENDPOINTS
@app.post("/simular")
def simular(datos: SimulacionInput):
    resultado = calcular_credito(datos.tipo_vehiculo,datos.valor_vehiculo, datos.cuota_inicial, datos.plazo_meses)
    return resultado

@app.post("/solicitudes")
def solicitar(datos: SolicitudInput, db: Session = Depends(get_db)):
    credito = calcular_credito(datos.tipo_vehiculo, datos.valor_vehiculo, datos.cuota_inicial, datos.plazo_meses)
    Solicitud = Solicitud_credito(
        nombre=datos.nombre,
        apellido=datos.apellido,
        correo=datos.correo,
        telefono=datos.telefono,
        ciudad=datos.ciudad,
        tipo_vehiculo=datos.tipo_vehiculo,
        valor_vehiculo=datos.valor_vehiculo,
        cuota_inicial=datos.cuota_inicial,
        plazo_meses=datos.plazo_meses,
        valor_financiado=credito["valor_financiado"],
        cuota_mensual=credito["cuota_mensual"],
        total_intereses=credito["total_intereses"],
        total_a_pagar=credito["total_a_pagar"]
    )
    db.add(Solicitud)
    db.commit()
    db.refresh(Solicitud)
    return Solicitud

@app.post("/amortizacion")
def amortizar(datos: SimulacionInput):
    credito = calcular_credito(datos.tipo_vehiculo, datos.valor_vehiculo, datos.cuota_inicial, datos.plazo_meses)
    return generar_amortizacion(credito["valor_financiado"], credito["cuota_mensual"], datos.plazo_meses)

# Este endPoint sirve para cuando se quiera consultar la amortización de una solicitud ya registrada
@app.get("/solicitudes/{id}/amortizacion")
def obtener_amortizacion(id: int, db:Session = Depends(get_db)):
    solicitud = db.query(Solicitud_credito).filter(Solicitud_credito.id == id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    else: 
        return generar_amortizacion(solicitud.valor_financiado, solicitud.cuota_mensual, solicitud.plazo_meses)