import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import json

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL
st.set_page_config(page_title="Costimplant USS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #003366;
        color: white;
        border: 2px solid #FFCC00;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FFCC00;
        color: #003366;
    }
    h1, h2, h3 { color: #003366; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS Y ARCHIVOS
@st.cache_data
def load_data():
    try:
        data = pd.read_csv('base_datos_costos_uss_valdivia.csv', encoding='utf-8-sig')
        data.columns = ['Categoría', 'Código', 'Descripción', 'Precio Clínica', 'Lab', 'Precio Total', 'Proveedor']
        data['Proveedor'] = data['Proveedor'].astype(str).str.strip()
        data['Categoría'] = data['Categoría'].astype(str).str.strip()
        return data
    except Exception as e:
        st.error(f"Error al cargar el archivo CSV: {e}")
        return pd.DataFrame()

df = load_data()
HISTORIAL_FILE = 'historial_pacientes.csv'
PLANTILLAS_FILE = 'plantillas.json'

def guardar_en_historial(datos):
    if not os.path.isfile(HISTORIAL_FILE):
        pd.DataFrame([datos]).to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')
    else:
        df_hist = pd.read_csv(HISTORIAL_FILE)
        pd.concat([df_hist, pd.DataFrame([datos])], ignore_index=True).to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')

def cargar_plantillas():
    if os.path.exists(PLANTILLAS_FILE):
        try:
            with open(PLANTILLAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def guardar_plantilla(nombre, carrito):
    plantillas = cargar_plantillas()
    plantillas[nombre] = carrito
    with open(PLANTILLAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=4)

# FUNCIÓN DE LIMPIEZA (CALLBACK)
def limpiar_todo():
    st.session_state.carrito = []
    st.session_state.paciente_n = ""
    st.session_state.paciente_r = ""
    st.session_state.paciente_d = ""
    st.session_state.paciente_o = ""

# 3. FUNCIÓN GENERAR PDF
def generar_pdf(resumen, t_total, paciente, rut, doctor, obs):
    pdf = FPDF()
    pdf.add_page()
    
    def limpiar_texto(texto):
        return str(texto).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(225, 225, 225)
    pdf.text(12, 140, "DOCUMENTO NO OFICIAL DE LA UNIVERSIDAD SAN SEBASTIAN")
    pdf.set_y(20)
    
    pdf.set_font("Arial", 'B', 15)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(200, 10, txt="PLANIFICACION DE COSTOS DE IMPLANTES", ln=True, align='C')
    pdf.cell(200, 8, txt="HERRAMIENTA DE APOYO CLINICO", ln=True, align='C')
    
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, txt=limpiar_texto(f"PACIENTE: {paciente.upper()}"))
    pdf.cell(90, 6, txt=f"FECHA: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.cell(100, 6, txt=limpiar_texto(f"RUT: {rut}"))
    pdf.cell(90, 6, txt=limpiar_texto(f"DOCTOR/ALUMNO: {doctor.upper()}"), ln=True, align='R')
    pdf.ln(8)

    for prov in resumen['Proveedor'].unique():
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 8, limpiar_texto(f"DETALLE: {prov.upper()}"), 1, 1, 'L', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(100, 8, "Descripcion", 1, 0, 'C')
        pdf.cell(15, 8, "Cant.", 1, 0, 'C')
        pdf.cell(35, 8, "Unitario", 1, 0, 'C')
        pdf.cell(40, 8, "Subtotal", 1, 1, 'C')
        
        pdf.set_font("Arial", size=9)
        temp_df = resumen[resumen['Proveedor'] == prov]
        subtotal_prov = 0
        
        for _, row in temp_df.iterrows():
            desc_limpia = limpiar_texto(str(row['Descripción'])[:55])
            pdf.cell(100, 8, desc_limpia, 1)
            pdf.cell(15, 8, str(row['Cantidad']), 1, 0, 'C')
            pdf.cell(35, 8, f"${row['Precio Unitario']:,.0f}", 1, 0, 'C')
            pdf.cell(40, 8, f"${row['Subtotal']:,.0f}", 1, 1, 'R')
            subtotal_prov += row['Subtotal']
            
        pdf.set_font("Arial", 'B', 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(150, 8, limpiar_texto(f"SUBTOTAL {prov.upper()}:"), 1, 0, 'R', True)
        pdf.cell(40, 8, f"${subtotal_prov:,.0f}", 1, 1, 'R', True)
        pdf.ln(5)

    if obs:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 7, txt="OBSERVACIONES:", ln=True)
        pdf.set_font("Arial", size=9)
        pdf.multi_cell(190, 5, txt=limpiar_texto(obs), border=1)
        pdf.ln(5)

    total_procedimientos = resumen[resumen['Proveedor'] == 'USS Valdivia']['Subtotal'].sum()
    total_insumos = resumen[resumen['Proveedor'] != 'USS Valdivia']['Subtotal'].sum()

    pdf.ln(2)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 8, "RESUMEN FINAL DE COSTOS", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(150, 8, "Total Procedimientos (Clinica USS):", 1, 0, 'R')
    pdf.cell(40, 8, f"${total_procedimientos:,.0f}", 1, 1, 'R')
    
    pdf.cell(150, 8, "Total Insumos y Biomateriales (Marcas):", 1, 0, 'R')
    pdf.cell(40, 8, f"${total_insumos:,.0f}", 1, 1, 'R')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(255, 220, 100)
    pdf.cell(150, 10, "GRAN TOTAL ESTIMADO:", 1, 0, 'R')
    pdf.cell(40, 10, f"${t_total:,.0f}", 1, 1, 'R', True)

    pdf.ln(8)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, "INFORMACION IMPORTANTE:", 1, 1, 'L', True)
    pdf.set_font("Arial", size=8)
    msg = (
        "- Este documento presenta los aranceles referenciales de insumos y procedimientos.\n"
        "- No es un documento oficial de la Universidad San Sebastian.\n"
        "- Valores sujetos a cambio una vez que se corroboren tanto en caja del centro de salud, como por la marca de insumos."
    )
    pdf.multi_cell(190, 5, txt=msg, border=1)

    return pdf.output(dest='S').encode('latin-1')

# 4. INTERFAZ DE USUARIO
st.title("Costimplant USS")

menu = st.sidebar.radio("Navegación", ["Crear Presupuesto", "Historial de Pacientes"])

if menu == "Crear Presupuesto":
    st.sidebar.subheader("Datos del Paciente")
    
    # Manejo del estado para limpiar los campos
    if 'paciente_n' not in st.session_state: st.session_state.paciente_n = ""
    if 'paciente_r' not in st.session_state: st.session_state.paciente_r = ""
    if 'paciente_d' not in st.session_state: st.session_state.paciente_d = ""
    if 'paciente_o' not in st.session_state: st.session_state.paciente_o = ""

    n_p = st.sidebar.text_input("Nombre", key="paciente_n")
    r_p = st.sidebar.text_input("RUT", key="paciente_r")
    d_p = st.sidebar.text_input("Doctor/Alumno", key="paciente_d")
    obs_p = st.sidebar.text_area("Observaciones", key="paciente_o")

    if 'carrito' not in st.session_state: st.session_state.carrito = []

    # PLANTILLAS RÁPIDAS
    st.header("⚡ Plantillas Rápidas")
    plantillas_guardadas = cargar_plantillas()
    
    if plantillas_guardadas:
        col_pl1, col_pl2, col_pl3 = st.columns([2, 1, 1])
        with col_pl1:
            plantilla_sel = st.selectbox("Seleccionar Plantilla:", ["-- Ninguna --"] + list(plantillas_guardadas.keys()))
        with col_pl2:
            st.write("")
            if st.button("➕ Cargar Plantilla"):
                if plantilla_sel != "-- Ninguna --":
                    st.session_state.carrito.extend(plantillas_guardadas[plantilla_sel])
                    st.success(f"Plantilla '{plantilla_sel}' agregada al carrito.")
                    st.rerun()
        with col_pl3:
            st.write("")
            if st.button("🗑️ Borrar Plantilla"):
                if plantilla_sel != "-- Ninguna --":
                    del plantillas_guardadas[plantilla_sel]
                    with open(PLANTILLAS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(plantillas_guardadas, f, ensure_ascii=False, indent=4)
                    st.warning(f"Plantilla '{plantilla_sel}' eliminada.")
                    st.rerun()
    else:
        st.info("No tienes plantillas guardadas. Arma tu presupuesto abajo y guárdalo al final de la página.")
        
    st.markdown("---")

    # PASO 1: USS VALDIVIA
    st.header("1° Seleccionar Procedimiento Clínico (USS)")
    df_uss = df[df['Proveedor'] == 'USS Valdivia']
    
    c1, c2, c3, c4 = st.columns([1.5, 2.5, 1, 1])
    with c1:
        cat_p = st.selectbox("Área:", df_uss['Categoría'].unique(), key="cat_p1")
    with c2:
        df_p_f = df_uss[df_uss['Categoría'] == cat_p]
        proc_sel = st.selectbox("Procedimiento:", df_p_f['Descripción'].tolist())
    with c3:
        cant_p = st.number_input("Cant.:", min_value=1, value=1, key="cant_p1")
    if c4.button("Añadir", key="btn_p1"):
        row = df_p_f[df_p_f['Descripción'] == proc_sel].iloc[0]
        st.session_state.carrito.append({
            'Descripción': row['Descripción'], 'Proveedor': 'USS Valdivia',
            'Precio Unitario': row['Precio Total'], 'Cantidad': cant_p, 'Subtotal': row['Precio Total'] * cant_p
        })

    # PASO 2: INSUMOS
    st.header("2° Seleccionar Insumos y Biomateriales")
    df_ins = df[df['Proveedor'] != 'USS Valdivia']
    
    i1, i2, i3, i4, i5 = st.columns([1.5, 1.5, 2, 0.8, 1])
    with i1:
        marca_sel = st.selectbox("Marca:", df_ins['Proveedor'].unique(), key="marca_i2")
    with i2:
        df_m = df_ins[df_ins['Proveedor'] == marca_sel]
        cat_i = st.selectbox("Categoría:", df_m['Categoría'].unique(), key="cat_i2")
    with i3:
        df_i_f = df_m[df_m['Categoría'] == cat_i]
        ins_sel = st.selectbox("Producto:", df_i_f['Descripción'].tolist())
    with i4:
        cant_i = st.number_input("Cant.:", min_value=1, value=1, key="cant_i2")
    if i5.button("Añadir", key="btn_i2"):
        row = df_i_f[df_i_f['Descripción'] == ins_sel].iloc[0]
        st.session_state.carrito.append({
            'Descripción': row['Descripción'], 'Proveedor': marca_sel,
            'Precio Unitario': row['Precio Total'], 'Cantidad': cant_i, 'Subtotal': row['Precio Total'] * cant_i
        })

    # RESUMEN
    if st.session_state.carrito:
        st.markdown("---")
        st.subheader("Resumen del Presupuesto")
        
        for i, item in enumerate(st.session_state.carrito):
            r1, r2, r3, r4, r5 = st.columns([3, 1, 1, 1, 1])
            r1.write(f"**{item['Descripción']}** ({item['Proveedor']})")
            r2.write(f"Cant: {item['Cantidad']}")
            
            if r3.button("✏️", key=f"ed_{i}"): st.session_state[f"edit_{i}"] = True
            if st.session_state.get(f"edit_{i}", False):
                new_v = r1.number_input("Editar Precio:", value=float(item['Precio Unitario']), key=f"val_{i}")
                if r1.button("Guardar", key=f"sav_{i}"):
                    st.session_state.carrito[i]['Precio Unitario'] = new_v
                    st.session_state.carrito[i]['Subtotal'] = new_v * item['Cantidad']
                    st.session_state[f"edit_{i}"] = False
                    st.rerun()

            r4.write(f"${item['Subtotal']:,.0f}")
            if r5.button("Eliminar", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()

        res_df = pd.DataFrame(st.session_state.carrito)
        total = res_df['Subtotal'].sum()
        
        tot_proc = res_df[res_df['Proveedor'] == 'USS Valdivia']['Subtotal'].sum()
        tot_insu = res_df[res_df['Proveedor'] != 'USS Valdivia']['Subtotal'].sum()
        
        st.write(f"**Total Procedimientos USS:** ${tot_proc:,.0f}")
        st.write(f"**Total Insumos:** ${tot_insu:,.0f}")
        st.subheader(f"GRAN TOTAL ESTIMADO: ${total:,.0f}")

        # GUARDAR COMO PLANTILLA
        st.markdown("---")
        st.subheader("💾 Guardar como Plantilla")
        col_nt, col_bt = st.columns([3, 1])
        with col_nt:
            nombre_nueva_plantilla = st.text_input("Nombre de la plantilla (ej. 'Implante Unitario'):")
        with col_bt:
            st.write("")
            if st.button("Guardar Plantilla"):
                if nombre_nueva_plantilla:
                    guardar_plantilla(nombre_nueva_plantilla, st.session_state.carrito)
                    st.success(f"Plantilla '{nombre_nueva_plantilla}' guardada con éxito.")
                    st.rerun()
                else:
                    st.warning("Por favor, ingresa un nombre para la plantilla.")
        
        st.markdown("---")

        # --- BOTÓN CON CALLBACK PARA REINICIAR Y LIMPIAR TODO ---
        st.write("¿Deseas empezar desde cero o terminaste con este paciente?")
        st.button("🔄 Ingresar Nuevo Presupuesto (Borrar Todo)", on_click=limpiar_todo)

        st.write("") # Espaciador

        # --- BOTONES DE DESCARGA Y GUARDADO ---
        col_fin1, col_fin2 = st.columns(2)
        with col_fin1:
            if st.button("💾 Guardar en Historial"):
                guardar_en_historial({"Fecha": datetime.now().strftime("%d/%m/%Y"), "Paciente": n_p, "Total": total})
                st.success("Presupuesto guardado en el historial.")
        with col_fin2:
            pdf_b = generar_pdf(res_df, total, n_p, r_p, d_p, obs_p)
            st.download_button("📥 Descargar PDF Informativo", pdf_b, f"Presupuesto_{n_p}.pdf")

else:
    st.header("Historial de Pacientes")
    if os.path.exists(HISTORIAL_FILE):
        st.dataframe(pd.read_csv(HISTORIAL_FILE), use_container_width=True)
    else:
        st.info("Sin registros.")