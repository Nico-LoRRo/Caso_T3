# Imagen base oficial ligera de Python 3.12
FROM python:3.12-slim

# Evitar generación de archivos .pyc y buffer de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV HOST=0.0.0.0

# Crear usuario sin privilegios root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copiar dependencias con versiones completamente congeladas y verificadas por hash
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Copiar archivos del proyecto protegidos contra modificación por appuser
COPY app/ ./app/
COPY run.py .

# Ejecutar proceso como appuser sin privilegios de superusuario
USER appuser

EXPOSE 5000

CMD ["python", "run.py"]
