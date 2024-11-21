import psycopg2
from psycopg2 import OperationalError
import os
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    connection = None
    try:
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_DATABASE")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        print("Conexión exitosa")
        return connection
    except OperationalError as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def close_connection(connection):
    if connection:
        connection.close()
        print("Conexión cerrada")

connection = create_connection()

if connection:
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Versión de la base de datos: {db_version}")
    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
    finally:
        close_connection(connection)

def obtener_proyecto_id():
    connection = None
    try:
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_DATABASE")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT proyecto_id FROM proyectos ORDER BY proyecto_id DESC LIMIT 1;")
            proyecto_id = cursor.fetchone()

            if proyecto_id:
                return proyecto_id[0]
            else:
                return None

    except Exception as e:
        print(f"Error al obtener el proyecto_id: {e}")
        return None
    finally:
        if connection:
            connection.close()
