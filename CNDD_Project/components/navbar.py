"""
Componente de navegación (navbar)
"""

import reflex as rx
from ..state import GlobalState


def navbar(page_title: str = "CNDD Project") -> rx.Component:
    """
    Navbar reutilizable para todas las páginas.
    
    Args:
        page_title: Título de la página actual
    """
    return rx.hstack(
        # Logo y título
        rx.hstack(
            rx.icon("cloud", size=24, color="blue"),
            rx.heading(page_title, size="6"),
            spacing="3",
            align="center",
        ),
        
        rx.spacer(),
        
        # Navegación central
        rx.hstack(
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("layout-dashboard", size=16),
                        rx.text("Dashboard"),
                        spacing="2",
                        align="center",
                    ),
                    variant="ghost",
                    size="2",
                ),
                href="/dashboard",
            ),
            rx.link(
                rx.button(
                    rx.hstack(
                        rx.icon("folder", size=16),
                        rx.text("Archivos"),
                        spacing="2",
                        align="center",
                    ),
                    variant="ghost",
                    size="2",
                ),
                href="/files",
            ),
            rx.cond(
                GlobalState.role == "admin",
                rx.link(
                    rx.button(
                        rx.hstack(
                            rx.icon("shield", size=16),
                            rx.text("Admin"),
                            spacing="2",
                            align="center",
                        ),
                        variant="ghost",
                        size="2",
                    ),
                    href="/admin",
                ),
            ),
            spacing="2",
            align="center",
        ),
        
        rx.spacer(),
        
        # Usuario y logout
        rx.hstack(
            # Email del usuario
            rx.hstack(
                rx.icon("user", size=16),
                rx.text(
                    rx.cond(
                        GlobalState.name != "",
                        GlobalState.name,
                        GlobalState.username
                    ),
                    size="2",
                    weight="medium",
                ),
                spacing="2",
                align="center",
            ),
            
            # Badge del rol
            rx.badge(
                GlobalState.role,
                size="2",
                color_scheme="blue",
                variant="soft",
            ),
            
            # Separador
            rx.divider(orientation="vertical", height="20px"),
            
            # Botón de logout
            rx.button(
                rx.hstack(
                    rx.icon("log-out", size=16),
                    rx.text("Salir"),
                    spacing="2",
                    align="center",
                ),
                on_click=GlobalState.logout,
                variant="soft",
                color_scheme="red",
                size="2",
            ),
            
            spacing="3",
            align="center",
        ),
        
        width="100%",
        padding="1rem 2rem",
        background="white",
        border_bottom="1px solid var(--gray-6)",
        align="center",
    )

"""
### Guarda y recarga el navegador

El navbar ahora debería verse así:
```
[☁️ Dashboard]  |  [Dashboard] [Archivos] [Admin]  |  [👤 tu@email.com] [admin] | [🚪 Salir]
"""