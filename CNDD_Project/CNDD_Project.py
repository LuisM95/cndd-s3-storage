"""
CNDD Project - Aplicación de gestión S3
"""

import reflex as rx
from .pages.login import login_page
from .pages.dashboard import dashboard_page
from .pages.files import files_page
from .pages.admin import admin_page

from .state import GlobalState

def index() -> rx.Component:
    """Pagina Principal - redirige al login"""
    return rx.center(
        rx.vstack(
            rx.heading('CNDD Project ', size='9'),
            rx.text('Redireccionando ... ', size='4', color='gray'),
            rx.spinner(size='3', margin_top='2rem'),
            spacing='4',
            align='center',
            min_height='100vh',
        ),
        on_mount=rx.redirect('/login')
    )

#Crear Aplicacion Reflex
app = rx.App()

app.add_page(index, route='/')
app.add_page(login_page, route='/login')
app.add_page(dashboard_page, route='/dashboard')
app.add_page(files_page, route='/files')
app.add_page(admin_page, route='/admin')
    