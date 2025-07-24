import pandas as pd
import sqlite3
import os

# === CONFIGURACIÓN ===
DB_PATH = "./data/db_red/database.db"
TABLE_NAME = "contact_info"
EXCEL_PATH = r"C:\Users\Luna Espejo\OneDrive - DROPI\Escritorio\red_coincidencias\process_red\data\raw_red\datafinal_JUL22.xlsx"
COLUMNAS_REQUERIDAS = [
    "user_id", "name", "surname", "email", "dni", "dni_invoice",
    "phone", "store_phone", "Pais_AWS", "wallet_amount", "wallet_credits",
    "Dni_Bank"
]

# === FUNCIÓN DE GUARDADO ===
def save_data(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
    conn.close()

# === FUNCIÓN FORMATEO DE MONTO ===
def formato_chileno(x):
    if pd.isna(x):
        return ""
    entero, decimal = f"{x:,.10f}".split(".")
    decimal = decimal.rstrip("0")[:2]  # Máximo dos decimales visibles
    if decimal:
        return f"{entero.replace(',', '.')}," + decimal
    else:
        return entero.replace(',', '.')

# === PROCESAMIENTO PRINCIPAL ===
def process_file():
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ No se encontró el archivo:\n{EXCEL_PATH}")
        return

    try:
        df = pd.read_excel(EXCEL_PATH, dtype=str).fillna("")
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel:\n{e}")
        return

    columnas_faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if columnas_faltantes:
        print(f"❌ El archivo no contiene las siguientes columnas necesarias:\n{columnas_faltantes}")
        return

    print("📋 Columnas validadas correctamente.")
    print(f"📂 Registros encontrados: {len(df)}")

    # === NORMALIZACIÓN ===
    df["phone"] = df["phone"].str.replace(r"\D", "", regex=True)
    df["phone_std"] = df["phone"].str[-10:]
    df["phone_match"] = df["phone"].str[-8:]

    df["wallet_amount"] = (
        df["wallet_amount"]
        .str.replace(",", "", regex=False)
        .str.replace("−", "-", regex=False)
    )
    df["wallet_amount"] = pd.to_numeric(df["wallet_amount"], errors="coerce").fillna(0)
    df["wallet_amount_str"] = df["wallet_amount"].apply(formato_chileno)

    # 🔧 CREA LA CARPETA SI NO EXISTE
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # 🔥 BORRA TABLA EXISTENTE PARA PARTIR DE CERO
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.close()

    # === CARGA EN CHUNKS ===
    chunk_size = 50000
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        save_data(chunk)
        print(f"✅ Chunk {i // chunk_size + 1} guardado en base de datos.")

    print(f"✅ Carga completada. Tabla: {TABLE_NAME} → Base de datos: {DB_PATH}")

# === EJECUCIÓN ===
if __name__ == "__main__":
    process_file()
