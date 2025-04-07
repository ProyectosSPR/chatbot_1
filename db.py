from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
import os
from dotenv import load_dotenv
import logging



os.environ.pop("DATABASE_URL", None)  # Eliminar DATABASE_URL si existe# Eliminar la variable de entorno si existe
# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Variables globales
pool: ConnectionPool = None
checkpointer: PostgresSaver = None

def init_db():
    global pool, checkpointer
    try:
        pool = ConnectionPool(conninfo=DATABASE_URL, max_size=20)
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        logging.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logging.error(f"Error al inicializar la base de datos: {e}")
        raise
