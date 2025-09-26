# app.py
# ----------------------------------------------------------
# API REST para predecir el PRECIO DE CIERRE DE MAÑANA
# de la varilla (proxy SLX). Carga un modelo entrenado
# (model.joblib), calcula las features de T+1 con el CSV
# "steel_rebar_prices.csv" y responde en el contrato JSON
# solicitado por el caso DEACERO.
# ----------------------------------------------------------

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
from joblib import load
import pytz  # para manejar zonas horarias

APP_VERSION = "1.0.1"

# Rutas configurables
MODEL_PATH = os.getenv("MODEL_PATH", "model.joblib")
DATA_CSV   = os.getenv("DATA_CSV", "steel_rebar_prices.csv")

# Zona horaria local (Monterrey, MX)
LOCAL_TZ = pytz.timezone("America/Monterrey")

# -----------------------------
# Esquema de respuesta (contrato)
# -----------------------------
class PredictionResponse(BaseModel):
    prediction_date: str                 # YYYY-MM-DD (mañana, hora local)
    predicted_price_usd_per_ton: float   # número (USD / metric ton)
    currency: str                        # "USD"
    unit: str                            # "metric_ton"
    model_confidence: float              # 0–1 (placeholder razonable)
    timestamp: str                       # ISO local con "Z"

# -----------------------------
# Carga de modelo
# -----------------------------
def load_model_bundle(path: str):
    if not os.path.exists(path):
        return None
    try:
        bundle = load(path)  # {"model": RandomForestRegressor, "features": [...]}
        assert "model" in bundle and "features" in bundle
        return bundle
    except Exception as e:
        print(f"[WARN] No se pudo cargar el modelo: {e}")
        return None

model_bundle = load_model_bundle(MODEL_PATH)

# -----------------------------
# Utilidades de fechas y datos
# -----------------------------
def local_now_iso() -> str:
    """Devuelve hora actual en Monterrey en ISO con Z."""
    return datetime.now(LOCAL_TZ).replace(microsecond=0).isoformat()

def tomorrow_local_date() -> datetime:
    """Devuelve la fecha de mañana según horario local (Monterrey)."""
    return (datetime.now(LOCAL_TZ) + timedelta(days=1)).date()

def load_price_series(csv_path: str) -> pd.Series:
    """Carga CSV con precios y asegura frecuencia diaria."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No existe el archivo de datos: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    if not {"date", "price_usd_per_ton"}.issubset(df.columns):
        raise ValueError("El CSV debe tener columnas: 'date', 'price_usd_per_ton'.")

    s = df.set_index("date")["price_usd_per_ton"].sort_index()
    s = s.asfreq("D").ffill()  # rellenar huecos (fines de semana/feriados)
    return s

def build_features_for_t_plus_1(price_series: pd.Series) -> pd.DataFrame:
    """Genera las features de T+1 (mañana) igual que en el entrenamiento."""
    if len(price_series) < 30:
        raise ValueError("Serie muy corta; se requieren al menos 30 días.")

    last_date = price_series.index[-1]
    tmrw_date = last_date + timedelta(days=1)

    # Lags
    lag_1  = float(price_series.iloc[-1])
    lag_7  = float(price_series.iloc[-7])
    lag_30 = float(price_series.iloc[-30])

    # Rolling means
    rolling_mean_7  = float(price_series.iloc[-7:].mean())
    rolling_mean_30 = float(price_series.iloc[-30:].mean())

    # Calendario de mañana (hora local)
    day_of_week = int(tmrw_date.dayofweek)
    month       = int(tmrw_date.month)

    x_dict = {
        "lag_1": lag_1,
        "lag_7": lag_7,
        "lag_30": lag_30,
        "rolling_mean_7": rolling_mean_7,
        "rolling_mean_30": rolling_mean_30,
        "day_of_week": day_of_week,
        "month": month
    }
    return pd.DataFrame([x_dict])

def infer_confidence_placeholder() -> float:
    """Placeholder de confianza del modelo (fijo por ahora)."""
    return 0.80

# -----------------------------
# FastAPI app & endpoints
# -----------------------------
app = FastAPI(
    title="DEACERO – Steel Rebar Price API",
    description="Predice el precio de cierre de mañana (USD/metric ton) usando un modelo entrenado.",
    version=APP_VERSION,
)

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "model_loaded": model_bundle is not None,
        "model_features": (model_bundle["features"] if model_bundle else None),
        "data_exists": os.path.exists(DATA_CSV),
        "server_time_local": local_now_iso(),
    }

@app.get("/predict/steel-rebar-price", response_model=PredictionResponse)
def predict_rebar_price():
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado. Sube 'model.joblib'.")

    try:
        series = load_price_series(DATA_CSV)
        X_next = build_features_for_t_plus_1(series)

        # Aseguramos el orden de las columnas
        FEATURES = model_bundle["features"]
        X_next = X_next[FEATURES]

        model = model_bundle["model"]
        yhat = float(model.predict(X_next)[0])

        # Respuesta
        pred_date = tomorrow_local_date().isoformat()
        ts_now = local_now_iso()

        return PredictionResponse(
            prediction_date=pred_date,
            predicted_price_usd_per_ton=round(yhat, 4),
            currency="USD",
            unit="metric_ton",
            model_confidence=float(infer_confidence_placeholder()),
            timestamp=ts_now
        )
    except FileNotFoundError as fe:
        raise HTTPException(status_code=500, detail=str(fe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al predecir: {e}")
