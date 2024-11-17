import pandas as pd
import reflex as rx
from typing import List

class State(rx.State):
    success_message: str = "" 

    @rx.event
    async def upload(self, files: List[rx.UploadFile]):
        """Handle the upload of file(s).

        Args:
        files: The uploaded files.
        """
        try:
            for file in files:
                upload_data = await file.read()
                outfile = rx.get_upload_dir() / file.filename

                with outfile.open("wb") as file_object:
                    file_object.write(upload_data)
            
            self.success_message = f"Archivo(s) '{', '.join([file.filename for file in files])}' guardado(s) exitosamente."
        except Exception as e:
            self.success_message = f"Error al guardar archivo(s): {str(e)}"

@rx.page(route="/carga", title="Carga de archivos")
def carga_csv() -> rx.Component:
    color = "blue"
    return rx.box(
        rx.vstack(
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
                        "Drag and drop files here or click to select files",
                        text_align="center",         
                        font_size="1em",             
                        margin="10px 250px 15px",
                        color="black",
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
            rx.hstack(
                rx.foreach(
                    rx.selected_files("upload1"), rx.text  
                )
            ),
            rx.button(
                "Upload to database",
                on_click=State.upload(
                    rx.upload_files(upload_id="upload1"),
                ),
                color="white",  
                bg=color,       
                padding="0.5em 2em",  
                border_radius="8px",  
                width="fit-content",  
                margin="1em auto",  
            ),
            rx.text(
                State.success_message,
                color=rx.cond(
                    State.success_message.contains("guardado"),
                    "green",
                    "red"
                ),
                text_align="center",  
                font_size="1.2em",    
                margin="1em",         
            )
        ),
        bg="#385481",           
        padding="2em",         
        width="100%",          
        height="100vh",        
        align_items="center",  
        justify_content="center",  
        spacing="2em",          
    )
