import pandas as pd
import reflex as rx

nba_data = pd.read_csv(
    "/home/diego/Descargas/actividades.csv"
)
nba_data.columns = nba_data.columns.str.strip()

@rx.page(route="/principal", title="Principal")
def ventana_principal() -> rx.Component:
    return rx.section(
        rx.flex(
            rx.box(height="1px", margin_top="-30px"),
            rx.heading(
                "Ventana principal para los cálculos del árbol N-ario",
                size="6",
                align="center",
                color="white",
            ),
            rx.box(height="10px"),
            rx.button(
                "Agregar nuevo cálculo",
                backgroundColor="white",
                color="black",
                width="200px",
                margin="1px 50% 1px 45%",
                radius="large",
                on_click=rx.redirect("/carga"),
            ),
            rx.box(height="10px"),
            rx.data_table(
                data=nba_data[["Actividad", "Predecesores", "Duracion", "Optimista", "Mas probable", "Pesimista"]],
                pagination=True,
                search=True,
                sort=True,
            ),
            direction="column",
            gap="20px",
        ),
        style={
            "backgroundColor": "#385481", 
            "padding": "20px",            
            "minHeight": "100vh",
        },
 )