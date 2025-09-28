# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código de la app y los scripts de datos/modelo
COPY . .

# Durante el build: descarga datos, prepara features y entrena el modelo
RUN python deacero.py && \
    python prepare_data.py && \
    python train_baseline.py

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
