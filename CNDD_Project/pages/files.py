"""
Página de gestión de archivos S3
"""

import reflex as rx
from typing import List
from ..utils.S3_manager import S3Manager
from ..components.navbar import navbar


class FilesState(rx.State):
    """Estado de la página de archivos."""
    
    # Datos del usuario (sincronizados desde GlobalState)
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
    
    async def on_mount(self):
        """Inicializar al cargar la página."""
        from ..state import GlobalState
        
        # Obtener estado global
        global_state = await self.get_state(GlobalState)
        
        # Sincronizar datos del usuario
        self.username = global_state.username or "usuario@ejemplo.com"
        self.role = global_state.role or "solo-lectura"
        
        # Cargar buckets
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
            else:
                self.error_message = "No tienes acceso a ningún bucket"
        except Exception as e:
            self.error_message = f"Error cargando buckets: {str(e)}"
    
    def select_bucket(self, bucket: str):
        """Cambiar el bucket seleccionado."""
        self.selected_bucket = bucket
        self.error_message = ""
        self.success_message = ""
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
                if total > 0:
                    # Usar texto estático con "s"
                    self.success_message = f"Se encontraron {total} archivos"
                else:
                    self.success_message = "El bucket está vacío"
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
        self.search_query = ""
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
    
    @rx.var
    def bucket_count(self) -> int:
        """Número de buckets disponibles."""
        return len(self.available_buckets)
    
    @rx.var
    def file_count(self) -> int:
        """Número de archivos (filtrados)."""
        return len(self.filtered_files)


def files_page() -> rx.Component:
    """Página de gestión de archivos."""
    return rx.vstack(
        # Navbar
        navbar("Gestión de Archivos"),
        
        # Contenido principal
        rx.container(
            rx.vstack(
                # Header con información
                rx.hstack(
                    rx.vstack(
                        rx.heading("Archivos S3", size="6"),
                        rx.text(
                            f"Gestiona tus archivos en los buckets disponibles",
                            size="2",
                            color="gray",
                        ),
                        align="start",
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.badge(
                            f"{FilesState.bucket_count} buckets",
                            size="2",
                            color_scheme="blue",
                            variant="soft",
                        ),
                        rx.badge(
                             f"{FilesState.file_count} archivos",
                            size="2",
                            color_scheme="green",
                            variant="soft",
                        ),
                        spacing="2",
                    ),
                    width="100%",
                    align="center",
                    padding_bottom="1rem",
                ),
                
                # Controles: Selector de bucket y búsqueda
                rx.card(
                    rx.hstack(
                        # Selector de bucket
                        rx.vstack(
                            rx.text("Bucket:", size="2", weight="medium"),
                            rx.select(
                                FilesState.available_buckets,
                                value=FilesState.selected_bucket,
                                on_change=FilesState.select_bucket,
                                size="3",
                                placeholder="Selecciona un bucket",
                            ),
                            align="start",
                            spacing="1",
                            flex="1",
                        ),
                        
                        # Barra de búsqueda
                        rx.vstack(
                            rx.text("Buscar:", size="2", weight="medium"),
                            rx.input(
                                placeholder="Buscar archivos por nombre...",
                                value=FilesState.search_query,
                                on_change=FilesState.set_search_query,
                                size="3",
                                width="100%",
                            ),
                            align="start",
                            spacing="1",
                            flex="2",
                        ),
                        
                        # Botones de acción
                        rx.vstack(
                            rx.text(" ", size="2"),  # Spacer para alinear
                            rx.hstack(
                                rx.button(
                                    rx.hstack(
                                        rx.icon("refresh-cw", size=18),
                                        rx.text("Refrescar"),
                                        spacing="2",
                                    ),
                                    on_click=FilesState.refresh_files,
                                    variant="soft",
                                    size="3",
                                ),
                                rx.cond(
                                    FilesState.can_upload,
                                    rx.button(
                                        rx.hstack(
                                            rx.icon("upload", size=18),
                                            rx.text("Subir archivo"),
                                            spacing="2",
                                        ),
                                        size="3",
                                    ),
                                ),
                                spacing="2",
                            ),
                            align="end",
                            spacing="1",
                        ),
                        
                        width="100%",
                        spacing="4",
                        align="end",
                    ),
                    size="2",
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
                        icon="info",
                        color_scheme="blue",
                        variant="soft",
                    ),
                ),
                
                # Indicador de carga
                rx.cond(
                    FilesState.loading,
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3"),
                            rx.text("Cargando archivos...", size="2", color="gray"),
                            spacing="3",
                            align="center",
                        ),
                        padding="3rem",
                    ),
                ),
                
                # Tabla de archivos
                rx.cond(
                    ~FilesState.loading,
                    rx.cond(
                        FilesState.filtered_files,
                        rx.card(
                            rx.box(
                                rx.table.root(
                                    rx.table.header(
                                        rx.table.row(
                                            rx.table.column_header_cell(
                                                rx.hstack(
                                                    rx.icon("file", size=16),
                                                    rx.text("Nombre"),
                                                    spacing="2",
                                                ),
                                            ),
                                            rx.table.column_header_cell(
                                                rx.hstack(
                                                    rx.icon("hard-drive", size=16),
                                                    rx.text("Tamaño"),
                                                    spacing="2",
                                                ),
                                            ),
                                            rx.table.column_header_cell(
                                                rx.hstack(
                                                    rx.icon("clock", size=16),
                                                    rx.text("Última modificación"),
                                                    spacing="2",
                                                ),
                                            ),
                                            rx.table.column_header_cell(
                                                rx.hstack(
                                                    rx.icon("settings", size=16),
                                                    rx.text("Acciones"),
                                                    spacing="2",
                                                ),
                                            ),
                                        ),
                                    ),
                                    rx.table.body(
                                        rx.foreach(
                                            FilesState.filtered_files,
                                            lambda file: rx.table.row(
                                                rx.table.cell(
                                                    rx.hstack(
                                                        rx.icon("file-text", size=18, color="blue"),
                                                        rx.text(
                                                            file['name'],
                                                            weight="medium",
                                                        ),
                                                        spacing="2",
                                                        align="center",
                                                    ),
                                                ),
                                                rx.table.cell(
                                                    rx.badge(
                                                        f"{file['size_mb']} MB",
                                                        size="1",
                                                        variant="soft",
                                                    ),
                                                ),
                                                rx.table.cell(
                                                    rx.text(
                                                        file['last_modified'],
                                                        size="2",
                                                        color="gray",
                                                    ),
                                                ),
                                                rx.table.cell(
                                                    rx.hstack(
                                                        rx.cond(
                                                            FilesState.can_download,
                                                            rx.tooltip(
                                                                rx.icon_button(
                                                                    rx.icon("download", size=16),
                                                                    size="1",
                                                                    variant="soft",
                                                                    color_scheme="blue",
                                                                ),
                                                                content="Descargar archivo",
                                                            ),
                                                        ),
                                                        rx.cond(
                                                            FilesState.can_delete,
                                                            rx.tooltip(
                                                                rx.icon_button(
                                                                    rx.icon("trash-2", size=16),
                                                                    size="1",
                                                                    variant="soft",
                                                                    color_scheme="red",
                                                                ),
                                                                content="Eliminar archivo",
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
                                width="100%",
                                overflow_x="auto",
                            ),
                            size="2",
                        ),
                        # Estado vacío
                        rx.center(
                            rx.vstack(
                                rx.icon("folder-open", size=64, color="gray"),
                                rx.heading(
                                    "No hay archivos",
                                    size="5",
                                    color="gray",
                                ),
                                rx.text(
                                    rx.cond(
                                        FilesState.search_query != "",
                                        f"No se encontraron archivos que coincidan con '{FilesState.search_query}'",
                                        "Este bucket está vacío",
                                    ),
                                    size="3",
                                    color="gray",
                                ),
                                spacing="4",
                                align="center",
                                padding="4rem",
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