import requests
import sqlite3
from datetime import date

# 1. Obtener dato
url = "https://dolarapi.com/v1/dolares/oficial"
data = requests.get(url).json()

fecha = date.today().isoformat()
valor = data["venta"]

# 2. Conectar a la base
conn = sqlite3.connect("datos.db")
cur = conn.cursor()

# 3. Crear tabla si no existe
cur.execute("""
CREATE TABLE IF NOT EXISTS dolar_oficial (
    fecha TEXT PRIMARY KEY,
    valor REAL
)
""")

# 4. Insertar dato
cur.execute("""
INSERT OR IGNORE INTO dolar_oficial (fecha, valor)
VALUES (?, ?)
""", (fecha, valor))

conn.commit()
conn.close()

print(f"Guardado: {fecha} - {valor}")
