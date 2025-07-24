import streamlit as st
import pandas as pd
import sqlite3
import base64
import time
import os  # Para manejar rutas dinámicas
import gdown

# 📥 Verificar si existe la base de datos localmente, si no, descargarla
DB_PATH = "./data/db_red/database.db"
DRIVE_FILE_ID = "1DW15Nmf4Ox7sa2hcEq9ysTkCUfUZDtNP"
DOWNLOAD_URL = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}&export=download"

# Crear carpeta si no existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if not os.path.exists(DB_PATH):
    with st.spinner("📥 Descargando base de datos desde Google Drive..."):
        gdown.download(DOWNLOAD_URL, DB_PATH, quiet=False)

# Configuración inicial de la app
st.set_page_config(page_title="ADMIN_PRO", layout="wide")

# 📌 FUNCIÓN PARA PONER EL FONDO DIFUMINADO
def set_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <style>
        /* Fondo general de la app */
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}

        /* Fondo blanco translúcido sobre los elementos */
        .stApp > div {{
            background-color: rgba(255, 255, 255, 0.75);
            padding: 1rem;
            border-radius: 10px;
        }}

        /* Eliminar barra naranja superior */
        header, .css-18e3th9 {{
            background-color: transparent !important;
            box-shadow: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 📌 APLICA EL FONDO desde ruta absoluta dinámica
current_dir = os.path.dirname(__file__)
background_path = os.path.join(current_dir, "assets", "background_dropi.png")
set_background(background_path)

# 📌 LOGO CENTRADO
logo_path = os.path.join(current_dir, "assets", "lg_dropi.png")
with open(logo_path, "rb") as f:
    logo_encoded = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style='text-align: center; margin-top: -30px;'>
        <img src='data:image/png;base64,{logo_encoded}' width='300'/>
    </div>
    """,
    unsafe_allow_html=True
)

# Título y descripción
st.title("🔍 ADMIN_PRO – Red de Coincidencias Exactas")
st.markdown("---")
st.markdown("Ingresa un dato clave para buscar toda la red de coincidencias exactas entre usuarios.")

# ⚙️ Variables base
TABLE_NAME = "contact_info"
CAMPOS_CLAVE = ["email", "dni", "dni_invoice", "phone", "store_phone", "Dni_Bank"]

# 🔍 Función para buscar red de coincidencias
def buscar_red_coincidencias(valor_inicial, campos_clave, DB_PATH, TABLE_NAME):
    conn = sqlite3.connect(DB_PATH)
    df_db = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()

    valores_vistos = set()
    por_buscar = set([valor_inicial])
    coincidencias = set()
    filas_encontradas_idx = set()

    with st.status("🔍 Buscando coincidencias...", expanded=True) as status:
        progreso_texto = st.empty()
        iteracion = 0

        while por_buscar:
            valor = por_buscar.pop()
            if valor in valores_vistos:
                continue
            valores_vistos.add(valor)
            iteracion += 1

            # Mostrar progreso en cada iteración
            progreso_texto.write(f"🔁 Iteración {iteracion} | Coincidencias actuales: {len(filas_encontradas_idx)}")

            mask = pd.Series([False] * len(df_db))
            for col in campos_clave:
                mask |= (df_db[col].astype(str).str.strip() == str(valor).strip())

            nuevos_df = df_db[mask]

            for idx, fila in nuevos_df.iterrows():
                if idx not in filas_encontradas_idx:
                    filas_encontradas_idx.add(idx)
                    for col in campos_clave:
                        nuevo_valor = str(fila[col]).strip()
                        if nuevo_valor and nuevo_valor not in valores_vistos:
                            por_buscar.add(nuevo_valor)
                        if nuevo_valor:
                            coincidencias.add((nuevo_valor, col))

        status.update(label=f"✅ Coincidencias encontradas: {len(filas_encontradas_idx)}", state="complete")

    df_final = df_db.loc[list(filas_encontradas_idx)].copy()
    return df_final, coincidencias

# 🎨 Estilo visual del dataframe
def resaltar_celdas(df):
    valor_a_columnas = {}

    for col in df.columns:
        if col != "wallet_amount_str":
            for val in df[col].astype(str).str.strip():
                if val:
                    if val not in valor_a_columnas:
                        valor_a_columnas[val] = 1
                    else:
                        valor_a_columnas[val] += 1

    valores_duplicados = {val for val, count in valor_a_columnas.items() if count > 1}

    def estilo(row):
        estilos = []
        for col in df.columns:
            val = str(row[col]).strip()
            if col == "wallet_amount_str":
                try:
                    monto = float(val.replace(".", "").replace(",", "."))
                    if monto < 0:
                        estilos.append("background-color: lightcoral")
                    elif monto > 0:
                        estilos.append("background-color: lightgreen")
                    else:
                        estilos.append("")
                    continue
                except:
                    estilos.append("")
                    continue
            if val in valores_duplicados:
                estilos.append("background-color: #ffe0b2")  # naranja pastel
            else:
                estilos.append("")
        return estilos

    return df.style.apply(estilo, axis=1)

# 🧠 Entrada y resultado
valor = st.text_input("🔎 Valor a buscar (email, DNI, teléfono, etc.):")

if st.button("Buscar Red") and valor:
    resultado, coincidencias = buscar_red_coincidencias(valor.strip(), CAMPOS_CLAVE, DB_PATH, TABLE_NAME)
    if not resultado.empty:
        st.success(f"🔗 Se encontraron {len(resultado)} usuarios conectados por coincidencias exactas.")
        columnas_mostrar = [
            "user_id", "name", "surname", "email", "dni", "dni_invoice",
            "phone", "store_phone", "Pais_AWS", "wallet_amount_str", "wallet_credits", "Dni_Bank"
        ]
        columnas_existentes = [col for col in columnas_mostrar if col in resultado.columns]
        st.dataframe(resaltar_celdas(resultado[columnas_existentes]), use_container_width=True)

        csv = resultado[columnas_existentes].to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar CSV", data=csv, file_name="usuarios_conectados.csv", mime="text/csv")
    else:
        st.warning("No se encontraron coincidencias exactas relacionadas.")
