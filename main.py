import sqlite3
import requests
from datetime import datetime, timedelta

# CONFIGURACIÓN
DB_PATH = "/home/marcemorelli/portfolio/Exchange_Rates.db"
API_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/mayorista"

def obtener_datos_bcra():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            datos = response.json()
            ultimo_dato = datos[-1]
            return ultimo_dato['fecha'], ultimo_dato['compra']
    except Exception as e:
        print(f"Error consultando API: {e}")
    return None, None

def calcular_y_proyectar():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. BUSCAR LA SEMILLA (El último dato de Diciembre que forzamos)
    cursor.execute("""
        SELECT Date, Exchange_Rate_Upper_Limit, Exchange_Rate_Lower_Limit, Wholesale_USD
        FROM Rates
        WHERE Date <= '2025-12-31'
        ORDER BY Date DESC LIMIT 1
    """)
    ultimo = cursor.fetchone()

    if not ultimo:
        print("❌ No se encontró la semilla de Diciembre.")
        return

    fecha_ult_str, techo_seed, piso_seed, usd_seed = ultimo
    fecha_cursor = datetime.strptime(fecha_ult_str, '%Y-%m-%d')

    # 2. ACTUALIZAR DÓLAR DE HOY
    api_fecha, usd_hoy = obtener_datos_bcra()
    fecha_hoy_str = datetime.now().strftime('%Y-%m-%d')
    usd_actual = usd_hoy if (usd_hoy and api_fecha == fecha_hoy_str) else usd_seed

    # 3. LIMPIAR PROYECCIONES DESDE EL 1 DE ENERO
    # Esto asegura que no haya basura de cálculos anteriores en 2026
    cursor.execute("DELETE FROM Rates WHERE Date > '2025-12-31'")

    # 4. PROYECCIÓN DESDE LA SEMILLA
    print(f"Proyectando desde semilla: {fecha_ult_str} (Techo: {techo_seed})")

    techo_loop = techo_seed
    piso_loop = piso_seed

    # Proyectamos 150 días hacia adelante
    for _ in range(150):
        fecha_cursor += timedelta(days=1)
        f_str = fecha_cursor.strftime('%Y-%m-%d')

        # Lógica de Tasa Mensual
        if fecha_cursor.year == 2025:
            # Seguimos en diciembre: usamos 1% fijo
            tasa_mensual = 0.01
        else:
            # Es 2026: usamos Inflación t-2
            mes_t2_dt = (fecha_cursor.replace(day=1) - timedelta(days=45)).replace(day=1)
            mes_t2_str = mes_t2_dt.strftime('%Y-%m')

            cursor.execute("SELECT Real_Inflation, REM_Inflation FROM Inflation WHERE Month = ?", (mes_t2_str,))
            inf_row = cursor.fetchone()

            if not inf_row:
                break # Frenar si no hay más datos de REM cargados

            tasa_mensual = (inf_row[0] if inf_row[0] is not None else inf_row[1]) / 100

        # Aplicar fórmula de interés compuesto diario
        techo_loop *= ((1 + tasa_mensual)**(1/31))
        piso_loop *= ((1 - tasa_mensual)**(1/31))

        # El valor de USD solo se guarda si la fecha es <= hoy (Real)
        # o se deja el último USD para la proyección (Visual)
        cursor.execute("""
            INSERT OR REPLACE INTO Rates (Date, Wholesale_USD, Exchange_Rate_Upper_Limit, Exchange_Rate_Lower_Limit)
            VALUES (?, ?, ?, ?)
        """, (f_str, usd_actual, techo_loop, piso_loop))

    conn.commit()
    conn.close()
    print("✅ Proyección 2026 completada con éxito.")

if __name__ == "__main__":
    calcular_y_proyectar()