import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Monitor de Bandas Cambiarias", layout="wide")

def get_data():
    conn = sqlite3.connect("/home/marcemorelli/portfolio/Exchange_Rates.db")
    query = "SELECT Date, Wholesale_USD, Exchange_Rate_Upper_Limit, Exchange_Rate_Lower_Limit FROM Rates ORDER BY Date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['Date'] = pd.to_datetime(df['Date'])
    return df

st.title("📊 Monitor de Bandas Cambiarias - BCRA")
st.markdown("Visualización en tiempo real de las bandas de intervención y el dólar mayorista.")

try:
    df = get_data()

    # Filtro de fecha en el sidebar
    st.sidebar.header("Filtros")
    fecha_min = df['Date'].min().to_pydatetime()
    fecha_max = df['Date'].max().to_pydatetime()
    rango = st.sidebar.slider("Rango de fechas", fecha_min, fecha_max, (fecha_min, fecha_max))

    # Filtrar dataframe
    mask = (df['Date'] >= rango[0]) & (df['Date'] <= rango[1])
    df_filtered = df.loc[mask]

    # Crear el gráfico con Plotly
    fig = go.Figure()

    # Área sombreada (Canal)
    fig.add_trace(go.Scatter(
        x=df_filtered['Date'].tolist() + df_filtered['Date'].tolist()[::-1],
        y=df_filtered['Exchange_Rate_Upper_Limit'].tolist() + df_filtered['Exchange_Rate_Lower_Limit'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(0,176,246,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='Zona de Intervención'
    ))

    # Línea Techo
    fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Exchange_Rate_Upper_Limit'],
                             line=dict(color='red', width=2, dash='dash'), name='Techo'))

    # Línea Piso
    fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Exchange_Rate_Lower_Limit'],
                             line=dict(color='green', width=2, dash='dash'), name='Piso'))

    # Línea Dólar Mayorista
    fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Wholesale_USD'],
                             line=dict(color='black', width=3), name='Dólar Mayorista'))

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Precio (ARS)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Métricas clave
    col1, col2, col3 = st.columns(3)
    hoy = df.iloc[-1]
    col1.metric("Último Techo", f"${hoy['Exchange_Rate_Upper_Limit']:.2f}")
    col2.metric("Último Piso", f"${hoy['Exchange_Rate_Lower_Limit']:.2f}")
    col3.metric("Dólar Actual", f"${hoy['Wholesale_USD']:.2f}")

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")