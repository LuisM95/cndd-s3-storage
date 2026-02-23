""" Pagina de Login """

import reflex as rx 
from ..utils.aws_cognito import CognitoAuth

class LoginState(rx.State):
    """ Estado de la pagina de Login """

    username:str = ''
    password:str = ''
    loading:bool = False
    error_message:str = ''
    show_password:bool = False

    def set_username(self, value:str):
        """Actualizar username"""
        self.username = value
        self.error_message = ''

    def set_password(self, value:str):
        """Actualizar password"""
        self.password = value
        self.error_message = ''

    def toggle_password(self):
        """Mostrar/Ocultar password"""
        self.show_password = not self.show_password

    async def handle_login(self):
        """Manejar el login."""
        # Validar campos
        if not self.username or not self.password:
            self.error_message = "Por favor ingresa usuario y contraseña"
            return
        
        self.loading = True
        self.error_message = ""
        
        try:
            # Autenticar con Cognito
            cognito = CognitoAuth()
            success, user_data, error = cognito.authenticate(
                self.username, 
                self.password
            )
            
            if success:
                # Importar GlobalState
                from ..state import GlobalState
            
                # Preparar datos del usuario
                user_info = {
                    'username': user_data['username'],
                    'name': user_data.get('name', ''),
                    'email': user_data['username'],
                    'role': user_data['role'],
                    'access_token': user_data['access_token']
                }
            
                # Guardar en sesión global
                state = await self.get_state(GlobalState)
                state.login_user(user_info)

                
                
                # Redirigir al dashboard
                return rx.redirect("/dashboard")
            else:
                self.error_message = error
        
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
        
        finally:
            self.loading = False
            """Manejar el login."""
            # Validar campos
            if not self.username or not self.password:
                self.error_message = "Por favor ingresa usuario y contraseña"
                return
        
        self.loading = True
        self.error_message = ""
        
        try:
            # Autenticar con Cognito
            cognito = CognitoAuth()
            success, user_data, error = cognito.authenticate(
                self.username, 
                self.password
            )
            
            if success:
                # Guardar en estado global
                from ..state import GlobalState
                
                # Preparar datos del usuario
                user_info = {
                    'username': user_data['username'],
                    'email': user_data['username'],  # En Cognito el username es el email
                    'role': user_data['role'],
                    'access_token': user_data['access_token']
                }
                
                # Guardar en sesión global
                GlobalState.login_user(user_info)
                
                # Redirigir al dashboard
                return rx.redirect("/dashboard")
            else:
                self.error_message = error
        
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
        
        finally:
            self.loading = False
            
            """Manejar el login del usuario"""
            #Validar Campos 
            if not self.username or not self.password:
                self.error_message = 'Por favor ingresar usuario y contraseña'
                return 
            
            self.loading = True
            self.error_message = ''

            try: 
                # Autenticar con Cognito
                cognito = CognitoAuth()
                success, user_data, error = cognito.authenticate(
                    self.username,
                    self.password
                )

                if success:
                    # Guardar datos en la sesion
                    self.username = user_data['username']

                    #redirigir al dashboard 
                    return rx.redirect('/dashboard')
                else:
                    self.error_message = error

            except Exception as e:
                self.error_message = f'Error: {str(e)}'

            finally:
                self.loading = False

def login_page() -> rx.Component:
    """Página de login."""
    return rx.center(
        rx.card(
            rx.vstack(
                # Logo/Título
                rx.heading(
                    "CNDD Project",
                    size="8",
                    margin_bottom="0.5rem",
                ),
                rx.text(
                    "Sistema de Gestión S3",
                    size="4",
                    color="gray",
                    margin_bottom="2rem",
                ),
                # Formulario
                rx.vstack(
                    # Usuario
                    rx.text("Usuario", size="3", weight="medium"),
                    rx.input(
                        placeholder="Ingresa tu usuario",
                        value=LoginState.username,
                        on_change=LoginState.set_username,
                        size="3",
                        width="100%",
                    ),
                    
                    # Contraseña
                    rx.text(
                        "Contraseña", 
                        size="3", 
                        weight="medium", 
                        margin_top="1rem"
                    ),
                    rx.input(
                        placeholder="Ingresa tu contraseña",
                        type=rx.cond(LoginState.show_password, "text", "password"),
                        value=LoginState.password,
                        on_change=LoginState.set_password,
                        size="3",
                        width="100%",
                    ),
                    
                    # Mostrar contraseña
                    rx.checkbox(
                        "Mostrar contraseña",
                        checked=LoginState.show_password,
                        on_change=LoginState.toggle_password,
                        size="2",
                        margin_top="0.5rem",
                    ),
                    # Mensaje de error
                    rx.cond(
                        LoginState.error_message != "",
                        rx.callout(
                            LoginState.error_message,
                            icon="triangle-alert",
                            color_scheme="red",
                            margin_top="1rem",
                        ),
                    ),
                    # Botón login
                    rx.button(
                        rx.cond(
                            LoginState.loading,
                            rx.hstack(
                                rx.spinner(size="3"),
                                rx.text("Iniciando sesión..."),
                                spacing="2",
                            ),
                            rx.text("Iniciar Sesión"),
                        ),
                        on_click=LoginState.handle_login,
                        size="3",
                        width="100%",
                        margin_top="1.5rem",
                    ),
                    
                    width="100%",
                    spacing="2",
                ),
                spacing="4",
                width="100%",
            ),
            size="4",
            max_width="400px",
        ),
        min_height="100vh",
        background="var(--gray-2)",
    )