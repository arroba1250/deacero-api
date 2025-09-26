# Usa imagen base ligera de Python
FROM python:3.11-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements primero para aprovechar cache
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código y archivos necesarios
COPY . .

# Exponer puerto
EXPOSE 8080

# Comando para arrancar el servidor
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
