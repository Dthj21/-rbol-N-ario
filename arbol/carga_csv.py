import reflex as rx
import csv
from io import StringIO
from config.db_config import create_connection, obtener_proyecto_id, obtener_proyectos
from typing import List, Dict
from datetime import datetime
from src.models.calculation import calcular_ruta_critica


class FormState(rx.State):
    form_data: dict = {}
    proyecto_id: int = 0
    success_message: str = ""

    proyectos: List[Dict[str, str | datetime | int]] = []

    async def update_proyectos(self):
        self.proyectos = obtener_proyectos()

    async def handle_submit(self, form_data: dict):
        """Maneja el envío del formulario y guarda los datos en la base de datos."""
        self.form_data = form_data
        query = """
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (%s, %s, %s)
            RETURNING proyecto_id;
        """
        try:
            connection = create_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        query,
                        (
                            form_data.get("name_project"),
                            form_data.get("description"),
                            datetime.now(),
                        ),
                    )
                    self.proyecto_id = cursor.fetchone()[0]
                    connection.commit()
                    print(f"Proyecto creado con ID: {self.proyecto_id}")

                    self.success_message = f"Proyecto creado con ID: {self.proyecto_id}"

                    await self.update_proyectos()

            else:
                print("No se pudo establecer la conexión con la base de datos.")
        except Exception as e:
            print(f"Error al insertar el proyecto: {e}")
            self.proyecto_id = 0
        finally:
            if connection:
                connection.close()

    async def delete_proyecto(self, id: int):
        """Elimina un proyecto de la base de datos."""
        query = """
            DELETE FROM proyectos
            WHERE proyecto_id = %s;
        """
        try:
            connection = create_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, (id,))
                    connection.commit()
                    print(f"Proyecto con ID {id} ha sido eliminado.")

                    self.success_message = f"Proyecto con ID {id} ha sido eliminado."
                    await self.update_proyectos()

            else:
                print("No se pudo establecer la conexión con la base de datos.")
        except Exception as e:
            print(f"Error al eliminar el proyecto: {e}")
        finally:
            if connection:
                connection.close()

    @staticmethod
    def form_name():
        return rx.vstack(
            rx.form(
                rx.vstack(
                    rx.input(
                        placeholder="Nombre del proyecto",
                        name="name_project",
                        required=True,
                    ),
                    rx.input(
                        placeholder="Descripción",
                        name="description",
                        required=True,
                    ),
                    rx.button("Submit", type="submit"),
                ),
                on_submit=FormState.handle_submit,
                reset_on_submit=True,
            ),
        )


class State(rx.State):
    success_message: str = ""
    proyecto_id: int = 0

    def get_proyecto_id(self):
        proyecto_id = obtener_proyecto_id()
        print(f"El último proyecto_id es: {proyecto_id}")

        if not proyecto_id:
            self.success_message = "El proyecto_id no ha sido asignado. Por favor, crea un proyecto primero."
            return None
        return proyecto_id

    @rx.event
    async def upload(self, files: List[rx.UploadFile]):
        connection = None
        try:
            self.proyecto_id = self.get_proyecto_id()
            if not self.proyecto_id:
                return 

            connection = create_connection()
            if connection:
                for file in files:
                    upload_data = await file.read()
                    contenido_csv = upload_data.decode("utf-8")

                    csv_reader = csv.DictReader(StringIO(contenido_csv))
                    for row in csv_reader:
                        query_tarea = """
                            INSERT INTO tareas (
                                proyecto_id, nombre, duracion_optimista,
                                duracion_mas_probable, duracion_pesimista
                            ) VALUES (%s, %s, %s, %s, %s)
                            RETURNING tarea_id
                        """
                        with connection.cursor() as cursor:
                            cursor.execute(query_tarea, (
                                self.proyecto_id,
                                row["Actividad "],
                                int(row["Optimista"]),
                                int(row["Mas probable"]),
                                int(row["Pesimista"]),
                            ))
                            tarea_id = cursor.fetchone()[0]

                        predecesores = row.get("Predecesores", "").split(",")
                        for predecesor in predecesores:
                            predecesor = predecesor.strip()
                            if predecesor:
                                query_predecesor = """
                                    SELECT tarea_id FROM tareas
                                    WHERE proyecto_id = %s AND nombre = %s
                                """
                                with connection.cursor() as cursor:
                                    cursor.execute(query_predecesor, (self.proyecto_id, predecesor))
                                    result = cursor.fetchone()
                                    if result:
                                        predecesor_id = result[0]

                                        query_dependencia = """
                                            INSERT INTO dependencias (tarea_id, predecesor_id)
                                            VALUES (%s, %s)
                                        """
                                        with connection.cursor() as cursor:
                                            cursor.execute(query_dependencia, (tarea_id, predecesor_id))
                                    else:
                                        print(f"Advertencia: No se encontró el predecesor '{predecesor}' para la tarea '{row['Actividad ']}'.")

                        connection.commit()
                
                self.success_message = "Datos guardados exitosamente en la base de datos.\n"

                ruta_critica = calcular_ruta_critica(self.proyecto_id)
                print("Ruta crítica calculada:", ruta_critica)

                self.success_message += "Ruta crítica calculada exitosamente."
                
            else:
                self.success_message = "Error al conectar a la base de datos."
        except Exception as e:
            self.success_message = f"Error al procesar el archivo: {str(e)}"
        finally:
            if connection:
                connection.close()



@rx.page(route="/carga", title="Carga de archivos")
def carga_csv() -> rx.Component:
    color = "blue"
    return rx.box(
        rx.vstack(
            FormState.form_name(),
            rx.divider(),
            rx.upload(
                rx.vstack(
                    rx.button(
                        "Selecciona el archivo",
                        color=color,
                        bg="white",
                        border=f"2px solid {color}",
                        margin="0 auto",
                        padding="0.5em 1em",
                        border_radius="8px",
                    ),
                    rx.text(
                        "Arrastra y suelta archivos aquí o haz clic para seleccionar",
                        text_align="center",
                        font_size="1em",
                        color="black",
                        margin="1px 250px",
                    ),
                ),
                multiple=True,
                id="upload1",
                border="3px solid #0000FF",
                border_radius="12px",
                padding="2em",
                width="50%",
                margin="0 auto",
                bg="white",
            ),
            rx.hstack(rx.foreach(rx.selected_files("upload_id"), rx.text)),
            rx.button(
                "Subir y Calcular",
                on_click=lambda: State.upload(rx.upload_files(upload_id="upload1")),
                margin="1em auto",
                color="white",
                bg=color,
                padding="0.5em 2em",
                border_radius="8px",
                width="fit-content",
            ),
            rx.text(
                State.success_message,
                color="white",
                text_align="center",
                font_size="1.2em",
            ),
        ),
        bg="#385481",
        padding="2em",
        width="100%",
        height="100vh",
        align_items="center",
        justify_content="center",
        spacing="2em",
    )
