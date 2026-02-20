"""
Página de gestión de archivos S3
"""

import reflex as rx
from typing import List
from ..utils.S3_manager import S3Manager
#from ..components.navbar import navbar


class FilesState(rx.State):
    """Estado de la página de archivos."""
    
    # Datos del usuario (se establecerán desde login)
    username: str = "usuario@ejemplo.com"
    role: str = "solo-lectura"
    
    # Estado de la interfaz
    selected_bucket: str = ""
    available_buckets: List[str] = []
    files: List[dict] = []
    loading: bool = False
    error_message: str = ""
    success_message: str = ""
    search_query: str = ""
    
    def on_mount(self):
        """Inicializar al cargar la página."""
        self.load_buckets()
    
    def load_buckets(self):
        """Cargar buckets disponibles según el rol."""
        try:
            s3 = S3Manager()
            self.available_buckets = s3.get_available_buckets(self.role)
            
            # Seleccionar el primer bucket por defecto
            if self.available_buckets:
                self.selected_bucket = self.available_buckets[0]
                self.load_files()
        except Exception as e:
            self.error_message = f"Error cargando buckets: {str(e)}"
    
    def select_bucket(self, bucket: str):
        """Cambiar el bucket seleccionado."""
        self.selected_bucket = bucket
        self.load_files()
    
    def load_files(self):
        """Cargar archivos del bucket seleccionado."""
        if not self.selected_bucket:
            return
        
        self.loading = True
        self.error_message = ""
        self.success_message = ""
        
        try:
            s3 = S3Manager()
            success, files, error = s3.list_files(self.selected_bucket)
            
            if success:
                self.files = files
                total = len(files)
                self.success_message = f"Se encontraron {total} archivos"
            else:
                self.error_message = error
                self.files = []
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
            self.files = []
        finally:
            self.loading = False
    
    def set_search_query(self, query: str):
        """Actualizar búsqueda."""
        self.search_query = query
    
    @rx.var
    def filtered_files(self) -> List[dict]:
        """Filtrar archivos según búsqueda."""
        if not self.search_query:
            return self.files
        
        query = self.search_query.lower()
        return [
            f for f in self.files 
            if query in f['name'].lower()
        ]
    
    def refresh_files(self):
        """Refrescar lista de archivos."""
        self.load_files()
    
    @rx.var
    def can_upload(self) -> bool:
        """Verificar si el usuario puede subir archivos."""
        return self.role in ['admin', 'lectura-escritura', 'solo-carga']
    
    @rx.var
    def can_download(self) -> bool:
        """Verificar si el usuario puede descargar archivos."""
        return self.role in ['admin', 'lectura-escritura', 'solo-descarga']
    
    @rx.var
    def can_delete(self) -> bool:
        """Verificar si el usuario puede eliminar archivos."""
        return self.role in ['admin', 'lectura-escritura']


def files_page() -> rx.Component:
    """Página de gestión de archivos."""
    return rx.vstack(
        # Navbar
        navbar("Gestión de Archivos"),
        
        # Contenido principal
        rx.container(
            rx.vstack(
                # Selector de bucket y búsqueda
                rx.hstack(
                    # Selector de bucket
                    rx.vstack(
                        rx.text("Bucket:", size="2", weight="medium"),
                        rx.select(
                            FilesState.available_buckets,
                            value=FilesState.selected_bucket,
                            on_change=FilesState.select_bucket,
                            size="3",
                        ),
                        align="start",
                        spacing="1",
                    ),
                    
                    # Barra de búsqueda
                    rx.vstack(
                        rx.text("Buscar:", size="2", weight="medium"),
                        rx.input(
                            placeholder="Buscar archivos...",
                            value=FilesState.search_query,
                            on_change=FilesState.set_search_query,
                            size="3",
                            width="300px",
                        ),
                        align="start",
                        spacing="1",
                    ),
                    
                    rx.spacer(),
                    
                    # Botones de acción
                    rx.hstack(
                        rx.button(
                            rx.icon("refresh-cw", size=18),
                            "Refrescar",
                            on_click=FilesState.refresh_files,
                            variant="soft",
                            size="3",
                        ),
                        rx.cond(
                            FilesState.can_upload,
                            rx.button(
                                rx.icon("upload", size=18),
                                "Subir archivo",
                                size="3",
                            ),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    
                    width="100%",
                    padding="1rem",
                    align="center",
                ),
                
                # Mensajes de error/éxito
                rx.cond(
                    FilesState.error_message != "",
                    rx.callout(
                        FilesState.error_message,
                        icon="triangle-alert",
                        color_scheme="red",
                    ),
                ),
                rx.cond(
                    FilesState.success_message != "",
                    rx.callout(
                        FilesState.success_message,
                        icon="check-circle",
                        color_scheme="green",
                    ),
                ),
                
                # Indicador de carga
                rx.cond(
                    FilesState.loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding="2rem",
                    ),
                ),
                
                # Tabla de archivos
                rx.cond(
                    ~FilesState.loading,
                    rx.cond(
                        FilesState.filtered_files,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nombre"),
                                    rx.table.column_header_cell("Tamaño"),
                                    rx.table.column_header_cell("Última modificación"),
                                    rx.table.column_header_cell("Acciones"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    FilesState.filtered_files,
                                    lambda file: rx.table.row(
                                        rx.table.cell(
                                            rx.hstack(
                                                rx.icon("file", size=18),
                                                rx.text(file['name']),
                                                spacing="2",
                                            ),
                                        ),
                                        rx.table.cell(
                                            rx.text(f"{file['size_mb']} MB"),
                                        ),
                                        rx.table.cell(
                                            rx.text(file['last_modified']),
                                        ),
                                        rx.table.cell(
                                            rx.hstack(
                                                rx.cond(
                                                    FilesState.can_download,
                                                    rx.icon_button(
                                                        rx.icon("download", size=16),
                                                        size="1",
                                                        variant="soft",
                                                        color_scheme="blue",
                                                    ),
                                                ),
                                                rx.cond(
                                                    FilesState.can_delete,
                                                    rx.icon_button(
                                                        rx.icon("trash-2", size=16),
                                                        size="1",
                                                        variant="soft",
                                                        color_scheme="red",
                                                    ),
                                                ),
                                                spacing="2",
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            variant="surface",
                            width="100%",
                        ),
                        # Sin archivos
                        rx.center(
                            rx.vstack(
                                rx.icon("folder-open", size=48, color="gray"),
                                rx.text(
                                    "No hay archivos en este bucket",
                                    size="4",
                                    color="gray",
                                ),
                                spacing="4",
                                align="center",
                                padding="3rem",
                            ),
                        ),
                    ),
                ),
                
                spacing="4",
                width="100%",
            ),
            max_width="1400px",
            padding="2rem",
        ),
        
        spacing="0",
        min_height="100vh",
        background="var(--gray-2)",
        on_mount=FilesState.on_mount,
    )
    """Página de gestión de archivos."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.heading("Gestión de Archivos S3", size="7"),
            rx.spacer(),
            rx.badge(FilesState.role, size="2", color_scheme="blue"),
            rx.button(
                "Dashboard",
                on_click=rx.redirect("/dashboard"),
                variant="soft",
            ),
            width="100%",
            padding="1rem",
            background="white",
            border_bottom="1px solid var(--gray-6)",
        ),
        
        # Contenido principal
        rx.container(
            rx.vstack(
                # Selector de bucket y búsqueda
                rx.hstack(
                    # Selector de bucket
                    rx.vstack(
                        rx.text("Bucket:", size="2", weight="medium"),
                        rx.select(
                            FilesState.available_buckets,
                            value=FilesState.selected_bucket,
                            on_change=FilesState.select_bucket,
                            size="3",
                        ),
                        align="start",
                        spacing="1",
                    ),
                    
                    # Barra de búsqueda
                    rx.vstack(
                        rx.text("Buscar:", size="2", weight="medium"),
                        rx.input(
                            placeholder="Buscar archivos...",
                            value=FilesState.search_query,
                            on_change=FilesState.set_search_query,
                            size="3",
                            width="300px",
                        ),
                        align="start",
                        spacing="1",
                    ),
                    
                    rx.spacer(),
                    
                    # Botones de acción
                    rx.hstack(
                        rx.button(
                            rx.icon("refresh-cw", size=18),
                            "Refrescar",
                            on_click=FilesState.refresh_files,
                            variant="soft",
                            size="3",
                        ),
                        rx.cond(
                            FilesState.can_upload(),
                            rx.button(
                                rx.icon("upload", size=18),
                                "Subir archivo",
                                size="3",
                            ),
                        ),
                        spacing="2",
                        align="center",
                    ),
                    
                    width="100%",
                    padding="1rem",
                    align="center",
                ),
                
                # Mensajes de error/éxito
                rx.cond(
                    FilesState.error_message != "",
                    rx.callout(
                        FilesState.error_message,
                        icon="triangle-alert",
                        color_scheme="red",
                    ),
                ),
                rx.cond(
                    FilesState.success_message != "",
                    rx.callout(
                        FilesState.success_message,
                        icon="check-circle",
                        color_scheme="green",
                    ),
                ),
                
                # Indicador de carga
                rx.cond(
                    FilesState.loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding="2rem",
                    ),
                ),
                
                # Tabla de archivos
                rx.cond(
                    ~FilesState.loading,
                    rx.cond(
                        FilesState.filtered_files.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nombre"),
                                    rx.table.column_header_cell("Tamaño"),
                                    rx.table.column_header_cell("Última modificación"),
                                    rx.table.column_header_cell("Acciones"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    FilesState.filtered_files,
                                    lambda file: rx.table.row(
                                        rx.table.cell(
                                            rx.hstack(
                                                rx.icon("file", size=18),
                                                rx.text(file['name']),
                                                spacing="2",
                                            ),
                                        ),
                                        rx.table.cell(
                                            rx.text(f"{file['size_mb']} MB"),
                                        ),
                                        rx.table.cell(
                                            rx.text(file['last_modified']),
                                        ),
                                        rx.table.cell(
                                            rx.hstack(
                                                rx.cond(
                                                    FilesState.can_download(),
                                                    rx.icon_button(
                                                        rx.icon("download", size=16),
                                                        size="1",
                                                        variant="soft",
                                                        color_scheme="blue",
                                                    ),
                                                ),
                                                rx.cond(
                                                    FilesState.can_delete(),
                                                    rx.icon_button(
                                                        rx.icon("trash-2", size=16),
                                                        size="1",
                                                        variant="soft",
                                                        color_scheme="red",
                                                    ),
                                                ),
                                                spacing="2",
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            variant="surface",
                            width="100%",
                        ),
                        # Sin archivos
                        rx.center(
                            rx.vstack(
                                rx.icon("folder-open", size=48, color="gray"),
                                rx.text(
                                    "No hay archivos en este bucket",
                                    size="4",
                                    color="gray",
                                ),
                                spacing="4",
                                align="center",
                                padding="3rem",
                            ),
                        ),
                    ),
                ),
                
                spacing="4",
                width="100%",
            ),
            max_width="1400px",
            padding="2rem",
        ),
        
        spacing="0",
        min_height="100vh",
        background="var(--gray-2)",
        on_mount=FilesState.on_mount,
    )