FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Inicializar Reflex
RUN reflex init

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Puerto
EXPOSE 8000

# Comando de inicio - Frontend y Backend en el mismo puerto
CMD ["reflex", "run", "--env", "prod", "--backend-port", "8000", "--frontend-port", "8000"]