# Roda - Backend (Simulador de crédito para movilidad eléctrica)

## 1. Descripción del proyecto
A través de esta plataforma, los usuarios pueden acceder a bicicletas y motos eléctricas mediante planes de financiación simples y accesibles. La aplicación permite simular préstamos o financiamiento de vehículos eléctricos, ver de inmediato el resumen y la tabla de amortización completa (sin necesidad de registrarse), y opcionalmente registrar una solicitud de crédito formal con sus datos personales.

> El flujo respeta la intención de la HU-01: el usuario puede conocer el valor estimado de sus cuotas y el resumen del financiamiento **antes de tomar una decisión**, es decir, sin haber entregado datos personales todavía.

## 2. Tecnologías utilizadas
- **Python 3.13**
- **FastAPI** — framework para construir la API REST
- **Uvicorn** — servidor ASGI para correr la aplicación
- **SQLAlchemy** — ORM para interactuar con PostgreSQL sin escribir SQL manual
- **PostgreSQL** — base de datos relacional
- **Pydantic** — validación de datos de entrada/salida
- **python-dotenv** — manejo de variables de entorno
- **pytest** — pruebas unitarias automatizadas

## 3. Estructura del proyecto
```
Backend/
├── .env                  # variables de entorno (no se sube al repo)
├── .gitignore
├── database.py           # conexión a PostgreSQL con SQLAlchemy
├── main.py                # endpoints y lógica de cálculo financiero
├── models.py               # modelo de datos (tabla solicitud_credito)
├── schemas.py               # validación de datos con Pydantic
├── test_main.py              # pruebas unitarias
└── requirements.txt
```

## 4. Instalación paso a paso
```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Backend

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# En Windows (PowerShell):
venv\Scripts\Activate.ps1
# En Mac/Linux:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

## 5. Variables de entorno
Crear un archivo `.env` en la raíz de `Backend/` con el siguiente contenido:
```
DATABASE_URL=postgresql://roda_user:tu_password@localhost:5432/roda_creditos
```
> Nota: si la contraseña contiene caracteres especiales (como `#`), deben codificarse en formato URL (ej: `#` → `%23`).

## 6. Configuración de PostgreSQL
Conectarse como usuario administrador:

```bash
psql -U postgres
```

Dentro de la consola de `psql`:
```sql
CREATE DATABASE roda_creditos;
CREATE USER roda_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE roda_creditos TO roda_user;

-- Necesario en PostgreSQL 15+, donde los permisos sobre el esquema public
-- ya no se otorgan automáticamente a usuarios nuevos:
\c roda_creditos
GRANT ALL ON SCHEMA public TO roda_user;

```
Las tablas se crean automáticamente al levantar la aplicación (ver `Base.metadata.create_all()` en `main.py`), no es necesario ejecutar un script SQL manual.

## 7. Ejecutar el proyecto
Con el entorno virtual activado y parado en `Backend/`:
```bash
uvicorn main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.
Documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`.

## 8. Endpoints disponibles

### `POST /simular`
Calcula un crédito sin persistirlo en base de datos.

**Request:**
```json
{
  "tipo_vehiculo": "moto",
  "valor_vehiculo": 5000000,
  "cuota_inicial": 1000000,
  "plazo_meses": 12
}
```

**Response:**
```json
{
  "tipo_vehiculo": "moto",
  "valor_vehiculo": 5000000,
  "cuota_inicial": 1000000,
  "plazo_meses": 12,
  "valor_financiado": 4000000,
  "cuota_mensual": 375385.3,
  "total_intereses": 504623.6,
  "total_a_pagar": 4504623.6
}
```

### `POST /amortizacion`
Calcula y devuelve la tabla de amortización completa **a partir de los datos de la simulación**, sin necesidad de haber registrado una solicitud. Este endpoint es el que permite cumplir la HU-01: ver el detalle completo del crédito antes de decidir si se registra o no.

**Request:** igual al de `/simular` (`tipo_vehiculo`, `valor_vehiculo`, `cuota_inicial`, `plazo_meses`).

**Response:**
```json
[
  {
    "numero_cuota": 1,
    "cuota_mensual": 375385.3,
    "interes": 75077.06,
    "abono_capital": 300308.24,
    "saldo": 3699691.76
  }
]
```

### `POST /solicitudes`
Registra una solicitud de crédito completa (datos personales + datos del vehículo) y la persiste en PostgreSQL. El backend recalcula todos los valores financieros internamente — nunca confía en montos que pudieran venir ya calculados desde el frontend. Una misma persona (mismo correo) puede registrar varias solicitudes, ya que el correo no está restringido como único — cotizar varias veces antes de decidir es un caso de uso válido.

**Request:** igual al de `/simular`, más los datos personales (`nombre`, `apellido`, `correo`, `telefono`, `ciudad`).

**Response:** el registro completo guardado, incluyendo `id` y `fecha_solicitud`.

### `GET /solicitudes/{id}/amortizacion`
Devuelve la tabla de amortización de una solicitud **ya registrada**, recalculada a partir de los datos guardados (no se persiste la tabla en base de datos, ver sección 13). Se mantiene como endpoint auxiliar para consultar solicitudes existentes; el flujo principal de simulación usa `POST /amortizacion`.

## 9. Modelo de datos
Tabla `solicitud_credito`:

| Campo | Tipo | Descripción |
|---|---|---|
| id | Integer (PK) | Identificador autogenerado |
| nombre, apellido, correo, telefono, ciudad | String | Datos del solicitante |
| tipo_vehiculo | String | "bicicleta" o "moto" |
| valor_vehiculo, cuota_inicial | Float | Datos ingresados por el usuario |
| plazo_meses | Integer | Plazo del crédito en meses |
| valor_financiado, cuota_mensual, total_intereses, total_a_pagar | Float | Calculados por el backend |
| fecha_solicitud | DateTime | Se asigna automáticamente al crear el registro |

## 10. Lógica de negocio: cálculo financiero
El crédito se calcula con el sistema de amortización francés (cuota fija), usando una tasa fija mensual derivada de una tasa efectiva anual del 25% (por debajo de la tasa de usura vigente en Colombia que para el segundo semestre del 2026 es del 29.66%).

```
tasa_mensual = (1 + tasa_efectiva_anual) ^ (1/12) - 1

valor_financiado = valor_vehiculo - cuota_inicial

cuota_mensual = valor_financiado * [tasa_mensual * (1 + tasa_mensual)^n] 
                / [(1 + tasa_mensual)^n - 1]
```

donde `n` es el plazo en meses.

Para la tabla de amortización, mes a mes se calcula el interés sobre saldo, el abono a capital, y el nuevo saldo. En la última cuota, el abono a capital se ajusta para que el saldo cierre exactamente en 0 (evita residuos de redondeo de punto flotante).

## 11. Validaciones implementadas

| Validación | Dónde se aplica |
|---|---|
| valor_vehiculo >= $500.000 COP | Backend (Pydantic) |
| cuota_inicial < valor_vehiculo | Backend (Pydantic) |
| Todos los campos obligatorios | Backend (Pydantic, por definición de tipo) |
| plazo_meses > 0 | Backend (Pydantic) |
| cuota_inicial ≥ 0 | Backend (Pydantic) |
| Correo con formato válido | Backend (`EmailStr`) |
| Teléfono solo dígitos | Backend (`field_validator`) |

## 12. Pruebas automatizadas

El proyecto incluye 19 pruebas unitarias sobre la lógica de cálculo (`calcular_credito`, `generar_amortizacion`) y las validaciones de Pydantic, cubriendo casos normales y casos límite (plazo de 1 mes, financiamiento del 100%, cuota inicial igual al valor del vehículo, rechazo de datos inválidos).

Para ejecutarlas:

```bash
pytest -v
```

## 13. Decisiones técnicas y supuestos

- **Tasa de interés fija (25% EA):** el enunciado no especifica una tasa, así que se definió como constante de negocio en el backend, documentada y justificada contra la tasa de usura vigente.
- **La tabla de amortización no se persiste en base de datos:** se recalcula a partir de los datos ya guardados de la solicitud (valor financiado, cuota, plazo) cada vez que se consulta. Esto evita una tabla adicional y un JOIN innecesario para el alcance de esta prueba.
- **No se gestiona el ciclo de vida de pagos** (marcar cuotas como pagadas, mora, etc.) porque no está contemplado en las historias de usuario del enunciado — solo se pide simular y registrar, no administrar pagos reales.
- **CORS habilitado para `http://localhost:5173` (desarrollo local) y `https://rd-frontend.vercel.app` (frontend en producción).**
- **`POST /amortizacion` como endpoint separado de `/simular`:** en una primera versión, la tabla de amortización solo se podía consultar tras registrar una solicitud (`GET /solicitudes/{id}/amortizacion`), lo cual obligaba al usuario a entregar sus datos personales antes de ver el detalle completo del crédito — contradiciendo la HU-01, que pide conocer cuotas y resumen *antes de tomar una decisión*. Se separó el cálculo de la tabla de la persistencia, permitiendo verla directamente desde los datos de la simulación.
- **`correo` sin restricción de unicidad:** inicialmente se marcó como único en el modelo, pero eso impedía que una misma persona registrara más de una solicitud (por ejemplo, para comparar planes con distinto plazo o vehículo). Se corrigió para permitir múltiples solicitudes por correo.

## 14. Alcance y limitaciones conocidas

- No se testean los endpoints HTTP de forma automatizada (solo la lógica de cálculo pura); un test de integración con `TestClient` de FastAPI y una base de datos de prueba sería la mejora natural siguiente.
- No hay autenticación ni autorización — no fue definido en el alcance de la prueba.
- El frontend valida en tiempo real como apoyo de UX, pero la validación real e inquebrantable ocurre siempre en el backend.

## 15. Despliegue

- Backend en producción: https://roda-backend-jr4j.onrender.com
- Documentación Swagger: https://roda-backend-jr4j.onrender.com/docs

> Nota: al estar en el plan gratuito de Render, el servicio puede "dormir" tras un periodo de inactividad — la primera petición después de eso puede tardar 30-60 segundos en responder.
> Nota: la base de datos gratuita de Render expira el 14 de septiembre de 2026.