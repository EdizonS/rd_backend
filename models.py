from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy import func
from database import Base

class Solicitud_credito (Base):
    __tablename__ = "solicitud_credito"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, index=True)  # Columna 'id' de tipo Integer, clave primaria e índice
    nombre = Column(String, nullable=False)  # Columna 'nombre' de tipo String
    apellido = Column(String, nullable=False)  # Columna 'apellido' de tipo String
    correo = Column(String, index=True, nullable=False)  # Columna 'correo' de tipo String, única, índice y no nula
    telefono = Column(String, nullable=False)  # Columna 'telefono' de tipo String
    ciudad = Column(String, nullable=False)  # Columna 'ciudad' de tipo String
    tipo_vehiculo = Column(String, nullable=False)  # Columna 'Tipo_vehiculo' de tipo String
    valor_vehiculo = Column(Float, nullable=False)  # Columna 'valor_vehiculo' de tipo float
    cuota_inicial = Column(Float, nullable=False)  # Columna 'cuota_inicial' de tipo float
    plazo_meses = Column(Integer, nullable=False)  # Columna 'plazo' de tipo Integer
    valor_financiado = Column(Float, nullable=False)  # Columna 'valor_financiado' de tipo float por los decimales que pueden salir al calcular
    cuota_mensual = Column(Float, nullable=False)  # Columna 'cuota' de tipo float
    total_intereses = Column(Float, nullable=False)  # Columna 'total_interes' de tipo float
    total_a_pagar = Column(Float, nullable=False)  # Columna 'total_pagar' de tipo float
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())  # Columna 'fecha_solicitud' de tipo DateTime con la funcion automatica de obtener la fecha y hora actual al momento de crear el registro