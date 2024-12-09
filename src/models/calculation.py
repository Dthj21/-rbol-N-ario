import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from config.db_config import create_connection

def calcular_ruta_critica(proyecto_id: int):
    try:
        connection = create_connection()
        if not connection:
            raise ConnectionError("Error al conectar a la base de datos.")

        with connection.cursor() as cursor:
            query_tareas = """
                SELECT tarea_id, nombre, duracion_pert
                FROM tareas
                WHERE proyecto_id = %s
            """
            cursor.execute(query_tareas, (proyecto_id,))
            tareas = cursor.fetchall()

            if not tareas:
                print(f"No se encontraron tareas para el proyecto {proyecto_id}.")
                return None

            query_dependencias = """
                SELECT tarea_id, predecesor_id
                FROM dependencias
                WHERE tarea_id IN (SELECT tarea_id FROM tareas WHERE proyecto_id = %s)
            """
            cursor.execute(query_dependencias, (proyecto_id,))
            dependencias = cursor.fetchall()

        tareas_dict = {t[0]: {"nombre": t[1], "duracion_pert": t[2]} for t in tareas}
        dependencias_dict = {t[0]: [] for t in tareas}
        for tarea_id, predecesor_id in dependencias:
            if predecesor_id is not None:
                dependencias_dict[tarea_id].append(predecesor_id)

        sucesores_dict = {tarea_id: [] for tarea_id in tareas_dict}
        for tarea_id, predecesor_id in dependencias:
            if predecesor_id is not None:
                sucesores_dict[predecesor_id].append(tarea_id)

        print("\nDiccionario de sucesores:", sucesores_dict)
        print("\nDiccionario de dependencias:", dependencias_dict)

        tiempos = {tarea_id: {"inicio_temprano": 0, "finalizacion_temprana": 0,
                              "inicio_tardio": float('inf'), "finalizacion_tardio": float('inf')}
                   for tarea_id in tareas_dict}

        # Cálculo de tiempos tempranos
        print("\nCálculo de tiempos tempranos:")
        for tarea_id in tareas_dict:
            duracion = tareas_dict[tarea_id]["duracion_pert"]
            inicio_temprano = max(
                [tiempos[predecesor_id]["finalizacion_temprana"] for predecesor_id in dependencias_dict[tarea_id]] or [0]
            )
            tiempos[tarea_id]["inicio_temprano"] = inicio_temprano
            tiempos[tarea_id]["finalizacion_temprana"] = inicio_temprano + duracion
            print(f"Tarea {tarea_id} ({tareas_dict[tarea_id]['nombre']}): Inicio Temprano = {inicio_temprano}, Finalización Temprana = {inicio_temprano + duracion}")

        # Cálculo de tiempos tardíos
        # Cálculo de tiempos tardíos
        print("\nCálculo de tiempos tardíos:")
        tareas_ordenadas = sorted(tareas_dict.keys(), reverse=True)  # Ordenar de manera inversa
        for tarea_id in tareas_ordenadas:
            duracion = tareas_dict[tarea_id]["duracion_pert"]
            if not sucesores_dict[tarea_id]:
        # Si no tiene sucesores, igualar el tiempo tardío a la finalización temprana
                tiempos[tarea_id]["finalizacion_tardio"] = tiempos[tarea_id]["finalizacion_temprana"]
                tiempos[tarea_id]["inicio_tardio"] = tiempos[tarea_id]["finalizacion_tardio"] - duracion
            else:
        # Si tiene sucesores, tomar el tiempo tardío mínimo de sus sucesores
                finalizacion_tardio = min(
                    [tiempos[sucesor_id]["inicio_tardio"] for sucesor_id in sucesores_dict[tarea_id]]
                )
                tiempos[tarea_id]["finalizacion_tardio"] = finalizacion_tardio
                tiempos[tarea_id]["inicio_tardio"] = finalizacion_tardio - duracion

            print(f"Tarea {tarea_id} ({tareas_dict[tarea_id]['nombre']}): Inicio Tardío = {tiempos[tarea_id]['inicio_tardio']}, Finalización Tardía = {tiempos[tarea_id]['finalizacion_tardio']}")

        # Cálculo de holguras y ruta crítica
        print("\nCálculo de holguras:")
        ruta_critica = []
        for tarea_id, tiempo in tiempos.items():
            holgura = tiempo["inicio_tardio"] - tiempo["inicio_temprano"]
            tiempo["holgura"] = holgura
            print(f"Tarea {tarea_id}: Holgura = {holgura}")
            if holgura == 0:
                ruta_critica.append(tareas_dict[tarea_id]["nombre"])

        ruta_critica_str = " -> ".join(ruta_critica)
        print(f"\nRuta crítica del proyecto {proyecto_id}: {ruta_critica_str}")


        if not ruta_critica_str:
            print(f"No se ha podido calcular la ruta crítica para el proyecto {proyecto_id}.")
            return None
        
        with connection.cursor() as cursor:
            query_ruta_critica = """
                INSERT INTO rutas_criticas (proyecto_id, ruta_critica)
                VALUES (%s, %s)
                ON CONFLICT (proyecto_id) DO UPDATE SET ruta_critica = EXCLUDED.ruta_critica
            """
            cursor.execute(query_ruta_critica, (proyecto_id, ruta_critica_str))
            connection.commit()

        print(f"Ruta Crítica del proyecto {proyecto_id}: {ruta_critica_str}")
        return ruta_critica_str

    except Exception as e:
        print(f"Error al calcular la Ruta Crítica: {str(e)}")
        return None
    finally:
        if connection:
            connection.close()


def obtener_rutas_criticas(proyecto_id: int = None):
    try:
        connection = create_connection()
        if not connection:
            print("Error al conectar a la base de datos.")
            return None

        with connection.cursor() as cursor:
            if proyecto_id:
                query = "SELECT proyecto_id, ruta_critica FROM rutas_criticas WHERE proyecto_id = %s"
                cursor.execute(query, (proyecto_id,))
            else:
                query = "SELECT proyecto_id, ruta_critica FROM rutas_criticas"
                cursor.execute(query)

            rutas_criticas = cursor.fetchall()
            for proyecto_id, ruta_critica in rutas_criticas:
                print(f"Proyecto {proyecto_id}: {ruta_critica}")

            return rutas_criticas

    except Exception as e:
        print(f"Error al obtener rutas críticas: {str(e)}")
    finally:
        if connection:
            connection.close()

proyecto_id = 87

ruta_critica = calcular_ruta_critica(proyecto_id)

if ruta_critica:
    print(f"La Ruta Crítica para el proyecto {proyecto_id} es: {ruta_critica}")
else:
    print(f"No se pudo calcular la ruta crítica para el proyecto {proyecto_id}.")

obtener_rutas_criticas()
