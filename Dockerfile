FROM python:3.11-slim

# Evita que Python escriba archivos .pyc y fuerza salida de logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para Pillow, WeasyPrint y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Recolectar archivos estáticos para WhiteNoise
RUN python manage.py collectstatic --noinput

# Exponer el puerto interno del contenedor
EXPOSE 8000

# Comando para arrancar con Gunicorn apuntando al WSGI real del proyecto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "lubricantesLuisMora.wsgi:application"]

