# prepare_data.py
import pandas as pd
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

# 1. Cargar dataset
df = pd.read_csv("steel_rebar_prices.csv", parse_dates=["date"])

# 2. Asegurar frecuencia diaria (rellena huecos)
df = df.set_index("date").asfreq("D")
df["price_usd_per_ton"] = df["price_usd_per_ton"].ffill()

# 3. Crear variables rezagadas (lags)
for lag in [1, 7, 30]:
    df[f"lag_{lag}"] = df["price_usd_per_ton"].shift(lag)

# 4. Medias móviles
df["rolling_mean_7"] = df["price_usd_per_ton"].rolling(7).mean()
df["rolling_mean_30"] = df["price_usd_per_ton"].rolling(30).mean()

# 5. Features de calendario
df["day_of_week"] = df.index.dayofweek
df["month"] = df.index.month

# 6. Limpiar NaN (primeras filas)
df = df.dropna()

# 7. Guardar dataset listo para modelar
df.to_csv("steel_rebar_features.csv")
print("Dataset enriquecido guardado en steel_rebar_features.csv")
print(df.head())
