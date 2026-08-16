from pydantic import BaseModel, EmailStr, field_validator, model_validator, ConfigDict
from datetime import datetime

#/simular
class SimulacionInput(BaseModel):
    tipo_vehiculo: str
    valor_vehiculo: float
    cuota_inicial: float
    plazo_meses: int

    # Configuramoslas validaciones de los campos del modelo
    @field_validator("valor_vehiculo")
    @classmethod
    def validar_valor_vehiculo(cls, valor):
        if valor < 500000:
            raise ValueError("El valor del vehículo debe ser mayor o igual a $500.000 COP")
        return valor
    
    @field_validator("plazo_meses")
    @classmethod
    def validar_plazo(cls, plazo):
            if plazo <= 0:
                raise ValueError("El numero de meses debe ser mayor a 0")
            return plazo
    
    @model_validator(mode="after")
    def validar_cuota_inicial(self):
        if self.cuota_inicial >= self.valor_vehiculo:
            raise ValueError("La cuota inicial debe ser menor al valor del vehículo")
        if self.cuota_inicial < 0:
            raise ValueError("La cuota inicial no puede ser negativa")
        return self

#/Solicitud ingresada
class SolicitudInput(SimulacionInput):
    nombre: str
    apellido: str
    correo: EmailStr
    telefono: str
    ciudad: str
    
    @field_validator("telefono")
    @classmethod
    def validacion_telefono(cls, valor):
        if not valor.isdigit():
            raise ValueError("El telefono debe contener unicamente numeros")
        return valor

#/Solicitud calculada
class SolicitudOutput(SolicitudInput):
    id: int
    valor_financiado: float
    cuota_mensual: float
    total_intereses: float
    total_a_pagar: float
    fecha_solicitud: datetime

    #Configuración para que Pydantic pueda trabajar con objetos ORM(O) de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)