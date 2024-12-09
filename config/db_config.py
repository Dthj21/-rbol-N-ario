import psycopg2
from psycopg2 import OperationalError
import os
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import reflex as rx
from typing import Optional
from sqlmodel import Field

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


def obtener_proyectos():
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
            query = "SELECT nombre, descripcion, fecha_creacion, proyecto_id FROM proyectos"
            cursor.execute(query)

            # Convertir las tuplas en un diccionario
            proyectos = [
                {"nombre": row[0], "descripcion": row[1], "fecha_creacion": row[2], "proyecto_id": row[3]}
                for row in cursor.fetchall()
            ]
            return proyectos

    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return []
    finally:
        if connection:
            connection.close()



def eliminar_proyecto(proyecto_id):
    """
    Elimina un proyecto de la base de datos basado en su ID.

    Args:
        proyecto_id (int): ID único del proyecto a eliminar.
    """
    connection = None
    try:
        # Leer las credenciales de la base de datos desde las variables de entorno
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_DATABASE")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        # Conectar a la base de datos
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )

        # Crear un cursor para ejecutar la consulta
        with connection.cursor() as cursor:
            # Consulta SQL para eliminar el proyecto
            query = "DELETE FROM proyectos WHERE proyecto_id = %s"
            cursor.execute(query, (proyecto_id,))  # Pasamos el ID del proyecto

            # Confirmar los cambios
            connection.commit()

            # Verificar que se eliminó el proyecto
            cursor.execute("SELECT COUNT(*) FROM proyectos WHERE proyecto_id = %s", (proyecto_id,))
            count = cursor.fetchone()[0]
            if count == 0:
                print(f"El proyecto con ID {proyecto_id} fue eliminado exitosamente.")
            else:
                print(f"No se pudo eliminar el proyecto con ID {proyecto_id}.")

    except psycopg2.Error as e:
        # Manejo de errores
        print(f"Error al eliminar el proyecto con ID {proyecto_id}: {e}")
    finally:
        # Cerrar la conexión si está abierta
        if connection:
            connection.close()
