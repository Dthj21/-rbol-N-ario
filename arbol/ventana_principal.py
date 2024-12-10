import reflex as rx
from arbol.carga_csv import FormState
from config.db_config import obtener_proyectos
from arbol.grafo_cpm import visualizar_ruta_critica

@rx.page(route="/principal", title="Principal")
def ventana_principal() -> rx.Component:
    proyectos = FormState.proyectos

    return rx.section(
        rx.flex(
            rx.box(height="20px"),
            rx.flex(
                rx.heading(
                    "Ventana principal para los cálculos del árbol N-ario",
                    size="lg",
                    text_align="center",
                    color="white",
                ),
                rx.box(height="20px"),
                rx.button(
                    "Agregar nuevo cálculo",
                    backgroundColor="#4CAF50",
                    color="white",
                    padding="10px 20px",
                    border_radius="5px",
                    _hover={"backgroundColor": "#45A049"},
                    on_click=rx.redirect("/carga"),
                    align_self="center",
                ),
                direction="column",
                align="center",
            ),
            rx.box(height="30px"),
            rx.box(
                rx.text(
                    "Proyectos",
                    font_size="lg",
                    font_weight="bold",
                    margin_bottom="10px",
                    text_align="center",
                    color="white",
                ),
                rx.box(
                    rx.hstack(
                        rx.text("Nombre", font_weight="bold", text_align="center", flex="2", color="black"),
                        rx.text("Descripción", font_weight="bold", text_align="center", flex="4", color="black"),
                        rx.text("Fecha de Creación", font_weight="bold", text_align="center", flex="2", color="black"),
                        rx.text("Acciones", font_weight="bold", text_align="center", flex="1", color="black"),
                        style={
                            "borderBottom": "2px solid #ddd",
                            "padding": "10px",
                            "backgroundColor": "#f2f2f2",
                        },
                    ),
                    rx.foreach(
                        proyectos,
                        lambda proyecto: rx.hstack(
                            rx.text(
                                proyecto["nombre"],
                                text_align="left",
                                flex="2",
                                color="#333",
                            ),
                            rx.text(
                                proyecto["descripcion"],
                                text_align="left",
                                flex="4",
                                color="#333",
                            ),
                            rx.text(
                                proyecto["fecha_creacion"],
                                text_align="center",
                                flex="2",
                                color="#333",
                            ),
                            rx.button(
                                "Ver Gráfico",
                                backgroundColor="#2196F3",
                                color="white",
                                padding="5px",
                                border_radius="3px",
                                _hover={"backgroundColor": "#0b7dda"},
                                on_click=rx.redirect(f"/grafo?proyecto_id={proyecto['proyecto_id']}"),
                                flex="1",
                            ),
                            style={
                                "borderBottom": "1px solid #ddd",
                                "padding": "10px",
                                "backgroundColor": "white",
                            },
                        ),
                    ),
                ),
                style={
                    "border": "1px solid #ccc",
                    "borderRadius": "5px",
                    "overflow": "hidden",
                    "backgroundColor": "white",
                },
                padding="10px",
                margin="0 auto",
                width="90%",
            ),
        ),
        direction="column",
        gap="20px",
        style={
            "backgroundColor": "#385481",
            "padding": "20px",
            "minHeight": "100vh",
        },
    )
