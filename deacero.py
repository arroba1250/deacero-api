# deacero.py
import yfinance as yf
import pandas as pd

# 1. Descargar datos de Yahoo Finance (ETF SLX como proxy del acero)
df = yf.download("SLX", start="2015-01-01", progress=False)

# 2. Usar la columna 'Close' (ya ajustada por defecto)
df = df[["Close"]].reset_index()

# 3. Renombrar columnas a formato estándar
df.columns = ["date", "price_usd_per_ton"]

# 4. Asegurar tipos correctos
df["date"] = pd.to_datetime(df["date"])
df["price_usd_per_ton"] = df["price_usd_per_ton"].astype(float)

# 5. Guardar dataset a CSV
df.to_csv("steel_rebar_prices.csv", index=False)

print("Datos guardados en steel_rebar_prices.csv")
print(df.head())
print(df.tail())
