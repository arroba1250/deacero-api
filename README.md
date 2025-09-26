# DEACERO – Steel Rebar Price API

API REST (FastAPI) que predice el precio de cierre **de mañana** para la varilla corrugada (usando como proxy el ETF SLX).  
Incluye: pipeline de datos, modelo ML (Random Forest), empaquetado con Docker y endpoint público listo para deploy.

## 1) Requisitos
- Python 3.11+
- (Opcional) Docker Desktop

## 2) Estructura
.
├─ app.py # API FastAPI
├─ model.joblib # Modelo entrenado (joblib)
├─ steel_rebar_prices.csv # Datos históricos (proxy)
├─ requirements.txt # Dependencias
└─ Dockerfile # Contenedor


## 3) Correr local (sin Docker)
Instala dependencias y levanta el servidor:
```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080


Prueba:

Swagger UI: http://localhost:8080/docs
Salud: http://localhost:8080/health
Predicción: http://localhost:8080/predict/steel-rebar-price


4) Correr con Docker
4.1 Construir imagen
	docker build -t deacero-api .
4.2 Ejecutar contenedor
	docker run -p 8080:8080 --name deacero deacero-api
4.3 (Opcional) Usar archivos locales sin reconstruir
	docker run -p 8080:8080 --name deacero -v "%cd%:/app" deacero-api
4.4 Comandos útiles
docker ps                  # contenedores corriendo
docker stop deacero        # parar contenedor
docker rm deacero          # eliminar contenedor
docker images              # listar imágenes
docker rmi deacero-api     # eliminar imagen
5) Endpoints

GET /health
200 OK

{
  "status": "ok",
  "version": "1.0.1",
  "model_loaded": true,
  "model_features": ["lag_1","lag_7","lag_30","rolling_mean_7","rolling_mean_30","day_of_week","month"],
  "data_exists": true,
  "server_time_local": "2025-09-25T21:10:00-06:00"
}

GET /predict/steel-rebar-price
200 OK

{
  "prediction_date": "YYYY-MM-DD",
  "predicted_price_usd_per_ton": 71.9244,
  "currency": "USD",
  "unit": "metric_ton",
  "model_confidence": 0.8,
  "timestamp": "YYYY-MM-DDTHH:MM:SS-06:00"
}


6) Variables de entorno (opcionales)

MODEL_PATH (default: model.joblib)
DATA_CSV (default: steel_rebar_prices.csv)
Ejemplo:
	docker run -p 8080:8080 -e MODEL_PATH=/app/model.joblib -e DATA_CSV=/app/steel_rebar_prices.csv deacero-api

7) Notas técnicas

Zona horaria: la API usa America/Monterrey para calcular prediction_date.
model_confidence es un placeholder (0.80). En producción, reemplazar por intervalo de predicción o error reciente.
Si actualizas el modelo o el CSV y no montas volumen, debes reconstruir la imagen (docker build …).

8) Troubleshooting

docker: command not found → instala Docker Desktop y reabre la terminal.
Engine no corre → abre Docker Desktop hasta ver “Engine running”.
WSL2 en Windows:

wsl --status
wsl --install
wsl --set-default-version 2

Puerto ocupado → usa otro: -p 9090:8080 y entra a http://localhost:9090.