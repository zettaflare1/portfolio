import requests
import sqlite3
from datetime import date

url = "https://dolarapi.com/v1/dolares/oficial"
data = requests.get(url).json()

fecha = date.today().isoformat()
valor = data["venta"]

conn = sqlite3.connect("datos.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS dolar_oficial (
    fecha TEXT PRIMARY KEY,
    valor REAL
)
""")

cur.execute("""
INSERT OR IGNORE INTO dolar_oficial (fecha, valor)
VALUES (?, ?)
""", (fecha, valor))

conn.commit()
conn.close()

print(f"Guardado: {fecha} - {valor}")
