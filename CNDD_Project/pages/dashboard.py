"""Pagina de Dashboard - Muestra Informacion del Usuario y Acceso a Funciones"""

import reflex as rx

class DashboardState(rx.State):
    """Estado del Dashboard - Puede incluir informacion del usuario, etc."""
    username: str = "usuario"
    role:str = "guest"

def dashboard_page() -> rx.Component:
    """Pagina Principal del Dashboard"""
    return rx.vstack(
        #header
        rx.hstack(
            rx.heading('CNDD Project -Dashboard', size='7'),
            rx.spacer(),
            rx.badge(DashboardState.role, size ='2', color_scheme='blue'),
            rx.button(
                'Cerrar Sesion', 
                on_click=rx.redirect('/login'),
                variant='soft',
            ),
            width='100%',
            padding='1rem',
            background = ' white',
            border_bottom = '2px solid var(--gray-6)'
        ),

        # Contenido Principal
        rx.container(
            rx.vstack(    
                rx.heading(
                    f"Bienvenido, {DashboardState.username}",
                    size = '6',
                    margin_top = '2rem',
                ), 
                rx.text(
                f'Tu rol es: {DashboardState.role}',
                size='4',
                color='gray',
            ),

            # Card de acciones rapidas
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.icon('folder', size=32),
                        rx.heading('Archivos en S3', size='4'),
                        rx.text('Gestiona los Archivos', size='2',color='gray'),
                        rx.button('Ver Archivos', width='100%', margin_top='1rem'),
                        align='center',
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.icon('Users', size=32),
                        rx.heading('Archivos en S3', size="4"),
                        rx.text('Administrar Usuarios', size="2", color="gray"),
                        rx.button('Ver Logs', width="100%", margin_top='1rem'),
                        align='center',
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.icon('Activity', size = 32),
                        rx.heading('Logs', size='4'),
                        rx.text('Ver actividad del Sistema', size ='2', color='gray'),
                        rx.button('Ver Logs', width='100%', margin_top='1rem'),
                        align='center',
                    ),
                ),
                columns='3',
                spacing='4',
                margin_top = '2rem',
            ),

            spacing ='4',
        ),
        max_width='1200px',
        padding = '2rem',
    ),
    spacing ='0',
    min_height = '100vh',
    background = 'var( --gray-2)',
)