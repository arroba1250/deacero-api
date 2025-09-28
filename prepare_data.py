# prepare_data.py
# Limpia la serie diaria, rellena huecos y crea features (lags, medias móviles, calendario).
import pandas as pd

# 1) Cargar CSV y forzar fecha como datetime
df = pd.read_csv("steel_rebar_prices.csv")
# fuerza conversión; si algo no parsea quedará NaT y lo filtramos
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# 2) Ordenar por fecha y dejarla como índice datetime
df = df.sort_values("date").set_index("date")

# 3) Asegurar tipo numérico en precio
df["price_usd_per_ton"] = pd.to_numeric(df["price_usd_per_ton"], errors="coerce")
df = df.dropna(subset=["price_usd_per_ton"])

# 4) Frecuencia diaria robusta (resample en lugar de asfreq)
s = df["price_usd_per_ton"].resample("D").ffill()

out = pd.DataFrame({"price_usd_per_ton": s})

# 5) Lags
for lag in [1, 7, 30]:
    out[f"lag_{lag}"] = out["price_usd_per_ton"].shift(lag)

# 6) Medias móviles
out["rolling_mean_7"]  = out["price_usd_per_ton"].rolling(7).mean()
out["rolling_mean_30"] = out["price_usd_per_ton"].rolling(30).mean()

# 7) Calendario
out["day_of_week"] = out.index.dayofweek
out["month"] = out.index.month

# 8) Quitar NaN iniciales y guardar
out = out.dropna()
out.to_csv("steel_rebar_features.csv")
print("✅ Dataset enriquecido guardado en steel_rebar_features.csv")
print(out.head())
