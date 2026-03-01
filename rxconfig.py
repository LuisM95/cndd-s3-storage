import reflex as rx 

config = rx.Config(
    app_name="CNDD_Project",
    # IMPORTANTE: En producción, frontend y backend deben estar en el mismo puerto
    backend_port=8000,
    frontend_port=8000,  # ← Mismo puerto que backend
    deploy_url="https://cndd-project1.onrender.com",
)