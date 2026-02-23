"""
Página de Dashboard
"""

import reflex as rx


class DashboardState(rx.State):
    """Estado del dashboard."""
    username: str = "Usuario"
    name: str = ""
    role: str = "guest"
    
    async def on_mount(self):
        """Cargar datos del usuario al montar la página."""
        from ..state import GlobalState
        
        # Obtener estado global
        global_state = await self.get_state(GlobalState)
        
        # Sincronizar datos
        self.username = global_state.username or "Usuario"
        self.name = global_state.name or ""
        self.role = global_state.role or "guest"


def dashboard_page() -> rx.Component:
    """Página principal del dashboard."""
    from ..components.navbar import navbar
    
    return rx.vstack(
        # Navbar
        navbar("Dashboard"),
        
        # Contenido principal
        rx.container(
            rx.vstack(
                # Saludo personalizado
                rx.vstack(
                    rx.heading(
                        rx.cond(
                            DashboardState.name != "",
                            f"¡Bienvenido, {DashboardState.name}!",
                            "¡Bienvenido!"
                        ),
                        size="7",
                        margin_top="2rem",
                    ),
                    rx.text(
                        f"Rol: {DashboardState.role}",
                        size="4",
                        color="gray",
                    ),
                    spacing="2",
                    align="start",
                ),
                
                # Cards de acciones
                rx.flex(
                    # Card: Archivos
                    rx.card(
                        rx.vstack(
                            rx.icon("folder", size=32, color="blue"),
                            rx.heading("Gestión de Archivos", size="4"),
                            rx.text("Gestiona archivos en S3", size="2", color="gray"),
                            rx.button(
                                rx.hstack(
                                    rx.icon("arrow-right", size=16),
                                    rx.text("Ver archivos"),
                                    spacing="2",
                                ),
                                on_click=rx.redirect("/files"),
                                width="100%", 
                                margin_top="1rem"
                            ),
                            align="center",
                            spacing="3",
                        ),
                        size="3",
                        flex="1",
                        min_width="250px",
                    ),
                    
                    # Card: Usuarios (solo admin)
                    rx.cond(
                        DashboardState.role == "admin",
                        rx.card(
                            rx.vstack(
                                rx.icon("users", size=32, color="green"),
                                rx.heading("Gestión de Usuarios", size="4"),
                                rx.text("Crear y administrar usuarios", size="2", color="gray"),
                                rx.button(
                                    rx.hstack(
                                        rx.icon("arrow-right", size=16),
                                        rx.text("Panel Admin"),
                                        spacing="2",
                                    ),
                                    on_click=rx.redirect("/admin"),
                                    width="100%", 
                                    margin_top="1rem"
                                ),
                                align="center",
                                spacing="3",
                            ),
                            size="3",
                            flex="1",
                            min_width="250px",
                        ),
                    ),
                    
                    # Card: Logs (solo admin)
                    rx.cond(
                        DashboardState.role == "admin",
                        rx.card(
                            rx.vstack(
                                rx.icon("activity", size=32, color="orange"),
                                rx.heading("Logs del Sistema", size="4"),
                                rx.text("Ver auditoría con OpenSearch", size="2", color="gray"),
                                rx.button(
                                    rx.hstack(
                                        rx.icon("arrow-right", size=16),
                                        rx.text("Ver logs"),
                                        spacing="2",
                                    ),
                                    on_click=rx.redirect("/admin"),
                                    width="100%", 
                                    margin_top="1rem"
                                ),
                                align="center",
                                spacing="3",
                            ),
                            size="3",
                            flex="1",
                            min_width="250px",
                        ),
                    ),
                    
                    # Card: Perfil del usuario
                    rx.card(
                        rx.vstack(
                            rx.icon("user", size=32, color="purple"),
                            rx.heading("Mi Perfil", size="4"),
                            rx.vstack(
                                rx.cond(
                                    DashboardState.name != "",
                                    rx.hstack(
                                        rx.icon("user", size=16, color="gray"),
                                        rx.text(DashboardState.name, size="2"),
                                        spacing="2",
                                        align="center",
                                    ),
                                ),
                                rx.hstack(
                                    rx.icon("mail", size=16, color="gray"),
                                    rx.text(DashboardState.username, size="2"),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.icon("shield", size=16, color="gray"),
                                    rx.badge(
                                        DashboardState.role,
                                        size="1",
                                        color_scheme="blue",
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                spacing="2",
                                align="start",
                                width="100%",
                            ),
                            rx.badge(
                                rx.hstack(
                                    rx.icon("circle_check", size=14),
                                    rx.text("Sesión activa"),
                                    spacing="1",
                                ),
                                color_scheme="green",
                                margin_top="1rem",
                            ),
                            align="center",
                            spacing="3",
                        ),
                        size="3",
                        flex="1",
                        min_width="250px",
                    ),
                    
                    spacing="4",
                    wrap="wrap",
                    margin_top="2rem",
                ),
                
                # Información de permisos según rol
                rx.card(
                    rx.vstack(
                        rx.heading(
                            rx.hstack(
                                rx.icon("key", size=20),
                                rx.text("Permisos de tu rol"),
                                spacing="2",
                            ),
                            size="5",
                        ),
                        
                        # Permisos según rol
                        rx.cond(
                            DashboardState.role == "admin",
                            rx.vstack(
                                rx.text("✅ Acceso completo a todos los buckets (Pública, Proyectos, RRHH, Logs)", size="2"),
                                rx.text("✅ Subir, descargar y eliminar archivos", size="2"),
                                rx.text("✅ Crear y gestionar usuarios", size="2"),
                                rx.text("✅ Ver logs de auditoría en OpenSearch", size="2"),
                                spacing="2",
                                align="start",
                            ),
                        ),
                        rx.cond(
                            DashboardState.role == "lectura-escritura",
                            rx.vstack(
                                rx.text("✅ Acceso a buckets: Pública y Proyectos", size="2"),
                                rx.text("✅ Subir, descargar y eliminar archivos", size="2"),
                                rx.text("❌ No puede acceder a bucket RRHH", size="2"),
                                rx.text("❌ No puede gestionar usuarios", size="2"),
                                rx.text("❌ No puede ver logs de auditoría", size="2"),
                                spacing="2",
                                align="start",
                            ),
                        ),
                        rx.cond(
                            DashboardState.role == "solo-lectura",
                            rx.vstack(
                                rx.text("✅ Acceso solo a bucket Pública", size="2"),
                                rx.text("✅ Solo listar archivos (sin descargar)", size="2"),
                                rx.text("❌ No puede descargar archivos", size="2"),
                                rx.text("❌ No puede subir archivos", size="2"),
                                rx.text("❌ No puede eliminar archivos", size="2"),
                                spacing="2",
                                align="start",
                            ),
                        ),
                        rx.cond(
                            DashboardState.role == "solo-carga",
                            rx.vstack(
                                rx.text("✅ Acceso a buckets: Pública y Proyectos", size="2"),
                                rx.text("✅ Listar y subir archivos", size="2"),
                                rx.text("❌ No puede descargar archivos", size="2"),
                                rx.text("❌ No puede eliminar archivos", size="2"),
                                spacing="2",
                                align="start",
                            ),
                        ),
                        rx.cond(
                            DashboardState.role == "solo-descarga",
                            rx.vstack(
                                rx.text("✅ Acceso a buckets: Pública y Proyectos", size="2"),
                                rx.text("✅ Listar y descargar archivos", size="2"),
                                rx.text("❌ No puede subir archivos", size="2"),
                                rx.text("❌ No puede eliminar archivos", size="2"),
                                spacing="2",
                                align="start",
                            ),
                        ),
                        
                        spacing="3",
                        align="start",
                    ),
                    margin_top="2rem",
                    size="2",
                ),
                
                # Información adicional
                rx.card(
                    rx.vstack(
                        rx.heading(
                            rx.hstack(
                                rx.icon("info", size=20),
                                rx.text("Información del Sistema"),
                                spacing="2",
                            ),
                            size="5",
                        ),
                        rx.grid(
                            rx.vstack(
                                rx.text("Buckets S3", size="1", color="gray", weight="medium"),
                                rx.text("4 buckets configurados", size="2"),
                                spacing="1",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Autenticación", size="1", color="gray", weight="medium"),
                                rx.text("AWS Cognito", size="2"),
                                spacing="1",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Auditoría", size="1", color="gray", weight="medium"),
                                rx.text("CloudTrail + OpenSearch", size="2"),
                                spacing="1",
                                align="start",
                            ),
                            rx.vstack(
                                rx.text("Región", size="1", color="gray", weight="medium"),
                                rx.text("us-east-2 (Ohio)", size="2"),
                                spacing="1",
                                align="start",
                            ),
                            columns="4",
                            spacing="4",
                        ),
                        spacing="3",
                        align="start",
                    ),
                    margin_top="1rem",
                    size="2",
                ),
                
                spacing="4",
            ),
            max_width="1200px",
            padding="2rem",
        ),
        
        spacing="0",
        min_height="100vh",
        background="var(--gray-2)",
        on_mount=DashboardState.on_mount,
    )