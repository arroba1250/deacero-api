# train_baseline.py
# ----------------------------------------------------------
# Este script entrena un modelo de predicción de precios
# de acero (proxy SLX) usando features rezagadas (lags),
# medias móviles y variables de calendario.
# Luego guarda el modelo entrenado en un archivo .joblib
# que será usado después por la API.
# ----------------------------------------------------------

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from joblib import dump
from datetime import timedelta

# ----------------------------------------------------------
# 1) Cargar dataset enriquecido (generado en el paso 2)
# ----------------------------------------------------------
df = pd.read_csv("steel_rebar_features.csv", parse_dates=["date"]).set_index("date")

# ----------------------------------------------------------
# 2) Definir variables (X = features, y = target)
# ----------------------------------------------------------
FEATURES = [
    "lag_1", "lag_7", "lag_30",
    "rolling_mean_7", "rolling_mean_30",
    "day_of_week", "month"
]
TARGET = "price_usd_per_ton"

# Aseguramos que no haya NaN en columnas clave
df = df.dropna(subset=FEATURES + [TARGET])

# ----------------------------------------------------------
# 3) División temporal train/test
#    - Usamos los últimos 180 días como "test set"
#    - El resto será "train set"
# ----------------------------------------------------------
test_days = 180
split_date = df.index.max() - pd.Timedelta(days=test_days)

train, test = df[df.index <= split_date], df[df.index > split_date]

X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

# ----------------------------------------------------------
# 4) Entrenar un modelo de baseline
#    - Random Forest Regressor: robusto, rápido y fácil
#    - Parámetros básicos, sin ajuste fino
# ----------------------------------------------------------
model = RandomForestRegressor(
    n_estimators=400,   # número de árboles
    max_depth=None,     # sin límite de profundidad
    random_state=42,    # reproducibilidad
    n_jobs=-1           # usar todos los núcleos disponibles
)
model.fit(X_train, y_train)

# ----------------------------------------------------------
# 5) Evaluar desempeño en el test set
#    - MAE: error absoluto medio
#    - MAPE: error porcentual medio
# ----------------------------------------------------------
pred = model.predict(X_test)
mae = mean_absolute_error(y_test, pred)
mape = (np.abs((y_test - pred) / y_test).mean()) * 100

print("📊 Resultados del modelo baseline:")
print(f"MAE  (USD/ton): {mae:,.4f}")
print(f"MAPE (%%):      {mape:,.2f}%")

# ----------------------------------------------------------
# 6) Reentrenar el modelo con TODO el histórico
#    - Así aprovechamos toda la data para la predicción final
#    - Guardar en archivo .joblib para usar en la API
# ----------------------------------------------------------
model.fit(df[FEATURES], df[TARGET])

dump({"model": model, "features": FEATURES}, "model.joblib")
print("✅ Modelo guardado en 'model.joblib'")

# ----------------------------------------------------------
# 7) Predicción para el "día siguiente" (ejemplo)
#    - Calculamos las features de mañana usando las últimas filas
#    - Solo para validar que el pipeline funciona
# ----------------------------------------------------------
last = df.iloc[-1]
tomorrow = last.name + timedelta(days=1)

x_next = pd.DataFrame([{
    "lag_1": last["price_usd_per_ton"],
    "lag_7": df["price_usd_per_ton"].iloc[-7],
    "lag_30": df["price_usd_per_ton"].iloc[-30],
    "rolling_mean_7": df["price_usd_per_ton"].iloc[-7:].mean(),
    "rolling_mean_30": df["price_usd_per_ton"].iloc[-30:].mean(),
    "day_of_week": tomorrow.dayofweek,
    "month": tomorrow.month
}])

yhat = float(model.predict(x_next)[0])
print(f"🔮 Predicción para {tomorrow.date()}: {yhat:,.2f} USD/ton")
