from urllib.parse import parse_qs
import networkx as nx
import reflex as rx
import matplotlib.pyplot as plt
from src.models.calculation import calcular_ruta_critica
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config.db_config import create_connection

@rx.page(route="/grafo", title="Gráficos")
def visualizar_ruta_critica(proyecto_id: str = 98):
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
                return rx.text(f"No se encontraron tareas para el proyecto {proyecto_id}.")

            query_dependencias = """
                SELECT tarea_id, predecesor_id
                FROM dependencias
                WHERE tarea_id IN (SELECT tarea_id FROM tareas WHERE proyecto_id = %s)
            """
            cursor.execute(query_dependencias, (proyecto_id,))
            dependencias = cursor.fetchall()

        G = nx.DiGraph()
        for tarea_id, nombre, duracion in tareas:
            G.add_node(tarea_id, label=nombre, duracion=duracion)

        for tarea_id, predecesor_id in dependencias:
            G.add_edge(predecesor_id, tarea_id)

        ruta_critica = calcular_ruta_critica(proyecto_id)

        if not ruta_critica:
            print(f"No se pudo calcular la ruta crítica para el proyecto {proyecto_id}.")
            return rx.text(f"No se pudo calcular la ruta crítica para el proyecto {proyecto_id}.")

        ruta_nodos = [t[0] for t in tareas if t[1] in ruta_critica.split(" -> ")]
        node_colors = ["orange" if node in ruta_nodos else "lightblue" for node in G.nodes]
        edge_colors = ["red" if (u in ruta_nodos and v in ruta_nodos) else "gray" for u, v in G.edges]

        pos = nx.spring_layout(G)
        plt.figure(figsize=(12, 8))
        nx.draw(G, pos, with_labels=True, node_color=node_colors, edge_color=edge_colors, node_size=3000, font_size=10)
        nx.draw_networkx_labels(G, pos, labels={n: f"{G.nodes[n]['label']} ({G.nodes[n]['duracion']})" for n in G.nodes})
        plt.title(f"Ruta Crítica del Proyecto {proyecto_id}")
        plt.savefig("assets/ruta_critica.png")

        return rx.image(src="/ruta_critica.png")

    except Exception as e:
        print(f"Error al visualizar la Ruta Crítica: {str(e)}")
        return rx.text(f"Error al visualizar la Ruta Crítica: {str(e)}")

    finally:
        if connection:
            connection.close()
