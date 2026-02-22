"""
Página de administración (solo para admin)
"""

import reflex as rx
from typing import List
from ..utils.aws_cognito import CognitoAuth
from ..utils.opensearch_client import OpenSearchClient


class AdminState(rx.State):
    """Estado de la página de admin."""
    
    # Usuario actual
    username: str = "admin@ejemplo.com"
    role: str = "admin"
    
    # Pestaña activa
    active_tab: str = "users"
    
    # === SECCIÓN: CREAR USUARIOS ===
    new_username: str = ""
    new_password: str = ""
    new_email: str = ""
    new_group: str = "solo-lectura"
    create_loading: bool = False
    create_message: str = ""
    create_error: str = ""
    
    # === SECCIÓN: LOGS ===
    logs: List[dict] = []
    logs_loading: bool = False
    logs_error: str = ""
    search_query: str = ""
    
    # Estadísticas
    total_events: int = 0
    top_events: List[dict] = []
    
    def on_mount(self):
        """Inicializar al cargar."""
        # Verificar que sea admin
        if self.role != "admin":
            return rx.redirect("/dashboard")
        
        # Cargar logs por defecto
        self.load_recent_logs()
    
    def set_tab(self, tab: str):
        """Cambiar pestaña activa."""
        self.active_tab = tab
    
    # === FUNCIONES: CREAR USUARIOS ===
    
    def set_new_username(self, value: str):
        """Actualizar nuevo username."""
        self.new_username = value
        self.create_message = ""
        self.create_error = ""
    
    def set_new_password(self, value: str):
        """Actualizar nueva contraseña."""
        self.new_password = value
    
    def set_new_email(self, value: str):
        """Actualizar nuevo email."""
        self.new_email = value
    
    def set_new_group(self, value: str):
        """Actualizar nuevo grupo."""
        self.new_group = value
    
    def create_user(self):
        """Crear nuevo usuario."""
        # Validar campos
        if not self.new_email or not self.new_password:
            self.create_error = "Email y contraseña son requeridos"
            return
        
        self.create_loading = True
        self.create_message = ""
        self.create_error = ""
        
        try:
            cognito = CognitoAuth()
            success, error = cognito.create_user(
                username=self.new_email,
                password=self.new_password,
                email=self.new_email,
                group=self.new_group
            )
            
            if success:
                self.create_message = f"Usuario '{self.new_email}' creado exitosamente"
                # Limpiar formulario
                self.new_username = ""
                self.new_password = ""
                self.new_email = ""
                self.new_group = "solo-lectura"
            else:
                self.create_error = error
        
        except Exception as e:
            self.create_error = f"Error: {str(e)}"
        
        finally:
            self.create_loading = False
    
    # === FUNCIONES: LOGS ===
    
    def set_search_query(self, query: str):
        """Actualizar búsqueda de logs."""
        self.search_query = query
    
    def load_recent_logs(self):
        """Cargar logs recientes."""
        self.logs_loading = True
        self.logs_error = ""
        
        try:
            opensearch = OpenSearchClient()
            success, logs, error = opensearch.get_recent_logs(limit=100)
            
            if success:
                self.logs = logs
                
                # Obtener estadísticas
                success_stats, stats, error_stats = opensearch.get_event_stats()
                if success_stats:
                    self.total_events = stats.get('total_events', 0)
                    self.top_events = stats.get('top_events', [])
            else:
                self.logs_error = error
                self.logs = []
        
        except Exception as e:
            self.logs_error = f"Error: {str(e)}"
            self.logs = []
        
        finally:
            self.logs_loading = False
    
    def search_logs(self):
        """Buscar logs según query."""
        if not self.search_query:
            self.load_recent_logs()
            return
        
        self.logs_loading = True
        self.logs_error = ""
        
        try:
            opensearch = OpenSearchClient()
            success, logs, error = opensearch.search_logs(
                query=self.search_query,
                size=100
            )
            
            if success:
                self.logs = logs
            else:
                self.logs_error = error
                self.logs = []
        
        except Exception as e:
            self.logs_error = f"Error: {str(e)}"
            self.logs = []
        
        finally:
            self.logs_loading = False
    
    @rx.var
    def filtered_logs(self) -> List[dict]:
        """Filtrar logs."""
        return self.logs[:50]  # Limitar a 50 para performance


def admin_page() -> rx.Component:
    """Página de administración."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.heading("Panel de Administración", size="7"),
            rx.spacer(),
            rx.badge("admin", size="2", color_scheme="red"),
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
        
        # Contenido
        rx.container(
            rx.vstack(
                # Pestañas
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Crear Usuarios", value="users"),
                        rx.tabs.trigger("Ver Logs", value="logs"),
                    ),
                    
                    # Pestaña: Crear Usuarios
                    rx.tabs.content(
                        rx.vstack(
                            rx.heading("Crear Nuevo Usuario", size="5"),
                            
                            rx.card(
                                rx.vstack(
                                    # Email
                                    rx.text("Email (será el username):", size="3", weight="medium"),
                                    rx.input(
                                        placeholder="usuario@ejemplo.com",
                                        value=AdminState.new_email,
                                        on_change=AdminState.set_new_email,
                                        size="3",
                                        width="100%",
                                    ),
                                    
                                    # Contraseña
                                    rx.text("Contraseña:", size="3", weight="medium", margin_top="1rem"),
                                    rx.input(
                                        placeholder="Mínimo 8 caracteres",
                                        type="password",
                                        value=AdminState.new_password,
                                        on_change=AdminState.set_new_password,
                                        size="3",
                                        width="100%",
                                    ),
                                    
                                    # Grupo/Rol
                                    rx.text("Rol:", size="3", weight="medium", margin_top="1rem"),
                                    rx.select(
                                        ["solo-lectura", "lectura-escritura", "solo-carga", "solo-descarga", "admin"],
                                        value=AdminState.new_group,
                                        on_change=AdminState.set_new_group,
                                        size="3",
                                    ),
                                    
                                    # Mensajes
                                    rx.cond(
                                        AdminState.create_error != "",
                                        rx.callout(
                                            AdminState.create_error,
                                            icon="triangle-alert",
                                            color_scheme="red",
                                            margin_top="1rem",
                                        ),
                                    ),
                                    rx.cond(
                                        AdminState.create_message != "",
                                        rx.callout(
                                            AdminState.create_message,
                                            icon="check-circle",
                                            color_scheme="green",
                                            margin_top="1rem",
                                        ),
                                    ),
                                    
                                    # Botón crear
                                    rx.button(
                                        rx.cond(
                                            AdminState.create_loading,
                                            rx.hstack(
                                                rx.spinner(size="3"),
                                                rx.text("Creando..."),
                                                spacing="2",
                                            ),
                                            rx.text("Crear Usuario"),
                                        ),
                                        on_click=AdminState.create_user,
                                        size="3",
                                        width="100%",
                                        margin_top="1.5rem",
                                    ),
                                    
                                    spacing="2",
                                ),
                                max_width="500px",
                            ),
                            
                            spacing="4",
                            align="start",
                        ),
                        value="users",
                        padding="2rem",
                    ),
                    
                    # Pestaña: Ver Logs
                    rx.tabs.content(
                        rx.vstack(
                            # Búsqueda y estadísticas
                            rx.hstack(
                                rx.input(
                                    placeholder="Buscar en logs...",
                                    value=AdminState.search_query,
                                    on_change=AdminState.set_search_query,
                                    size="3",
                                    width="400px",
                                ),
                                rx.button(
                                    rx.icon("search", size=18),
                                    "Buscar",
                                    on_click=AdminState.search_logs,
                                    size="3",
                                ),
                                rx.button(
                                    rx.icon("refresh-cw", size=18),
                                    "Refrescar",
                                    on_click=AdminState.load_recent_logs,
                                    variant="soft",
                                    size="3",
                                ),
                                
                                rx.spacer(),
                                
                                rx.badge(
                                    f"Total eventos: {AdminState.total_events}",
                                    size="2",
                                    color_scheme="blue",
                                ),
                                
                                width="100%",
                                align="center",
                            ),
                            
                            # Mensaje de error
                            rx.cond(
                                AdminState.logs_error != "",
                                rx.callout(
                                    AdminState.logs_error,
                                    icon="triangle-alert",
                                    color_scheme="red",
                                ),
                            ),
                            
                            # Indicador de carga
                            rx.cond(
                                AdminState.logs_loading,
                                rx.center(
                                    rx.spinner(size="3"),
                                    padding="2rem",
                                ),
                            ),
                            
                            # Tabla de logs
                            rx.cond(
                                ~AdminState.logs_loading,
                                rx.cond(
                                    AdminState.filtered_logs.length() > 0,
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell("Timestamp"),
                                                rx.table.column_header_cell("Evento"),
                                                rx.table.column_header_cell("Usuario"),
                                                rx.table.column_header_cell("IP"),
                                                rx.table.column_header_cell("Recurso"),
                                            ),
                                        ),
                                        rx.table.body(
                                            rx.foreach(
                                                AdminState.filtered_logs,
                                                lambda log: rx.table.row(
                                                    rx.table.cell(rx.text(log['timestamp'])),
                                                    rx.table.cell(rx.badge(log['event_name'], size="1")),
                                                    rx.table.cell(rx.text(log['user'])),
                                                    rx.table.cell(rx.text(log['source_ip'])),
                                                    rx.table.cell(rx.text(log['resource'], size="1")),
                                                ),
                                            ),
                                        ),
                                        variant="surface",
                                        width="100%",
                                    ),
                                    rx.center(
                                        rx.text("No se encontraron logs", color="gray"),
                                        padding="3rem",
                                    ),
                                ),
                            ),
                            
                            spacing="4",
                            width="100%",
                        ),
                        value="logs",
                        padding="2rem",
                    ),
                    
                    default_value="users",
                    width="100%",
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
        on_mount=AdminState.on_mount,
    )

