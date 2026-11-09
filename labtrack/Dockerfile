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

# Copiar dependencias e instalarlas
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

# Copiar selectivamente los archivos del proyecto (sin copia recursiva ciega)
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser run.py .

USER appuser

EXPOSE 5000

CMD ["python", "run.py"]
