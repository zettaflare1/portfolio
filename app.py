import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

def get_data():
    conn = sqlite3.connect("Exchange_Rates.db")
    query = "SELECT Date, Wholesale_USD, Exchange_Rate_Upper_Limit, Exchange_Rate_Lower_Limit FROM Rates ORDER BY Date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = get_data()

# --- LÓGICA DE SEPARACIÓN ---
# Asumimos que el REM empieza donde el 'Wholesale_USD' (TC Real) deja de tener datos (es NaN)
# O puedes definirlo por fecha si prefieres.
df_real = df[df['Wholesale_USD'].notna()]
df_rem = df[df['Wholesale_USD'].isna()]

# Para que no haya un hueco en el gráfico, el último punto de 'real' debe ser el primero de 'rem'
if not df_rem.empty:
    last_real_row = df_real.tail(1)
    df_rem = pd.concat([last_real_row, df_rem])

fig = go.Figure()

# 1. Línea del Tipo de Cambio Mayorista (Sólida)
fig.add_trace(go.Scatter(
    x=df_real['Date'], y=df_real['Wholesale_USD'],
    name="TC Mayorista (Real)",
    line=dict(color='blue', width=3)
))

# 2. Bandas Sólidas (Basadas en Inflación Real)
fig.add_trace(go.Scatter(
    x=df_real['Date'], y=df_real['Exchange_Rate_Upper_Limit'],
    name="Techo (Inflación)",
    line=dict(color='rgba(255, 0, 0, 0.5)', width=2)
))
fig.add_trace(go.Scatter(
    x=df_real['Date'], y=df_real['Exchange_Rate_Lower_Limit'],
    name="Piso (Inflación)",
    line=dict(color='rgba(0, 128, 0, 0.5)', width=2)
))

# 3. Bandas Entrecortadas (Basadas en REM)
if not df_rem.empty:
    fig.add_trace(go.Scatter(
        x=df_rem['Date'], y=df_rem['Exchange_Rate_Upper_Limit'],
        name="Techo (Proyección REM)",
        line=dict(color='red', width=2, dash='dash') # <--- Aquí el estilo entrecortado
    ))
    fig.add_trace(go.Scatter(
        x=df_rem['Date'], y=df_rem['Exchange_Rate_Lower_Limit'],
        name="Piso (Proyección REM)",
        line=dict(color='green', width=2, dash='dash') # <--- Aquí el estilo entrecortado
    ))

# Configuración estética
fig.update_layout(
    title="Monitoreo de Bandas de Tipo de Cambio (Real vs REM)",
    xaxis_title="Fecha",
    yaxis_title="ARS / USD",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)
