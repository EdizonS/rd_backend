from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) # Crea el motor de la base de datos utilizando la URL proporcionada en el archivo .env
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Crea una clase de sesión que se utilizará para interactuar con la base de datos
Base = declarative_base() # Crea una clase base para los modelos de la base de datos

def get_db(): # No se le pasan parametros aqui por que se utiliza como dependencia en las rutas de FastAPI, es allí donde se le pasan los parametros necesarios en cada función que la llama
    try:
        db = SessionLocal() # Abre la sesion
        yield db            # La pasa a la funcion que la llama
    finally:
        db.close()          # Cierra la sesion al terminar la funcion que la llama