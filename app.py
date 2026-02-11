import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# Configuración inicial de Costimplant USS
st.set_page_config(page_title="Costimplant USS", layout="wide")

# Estilo con paleta USS: Azul (#003366) y Dorado (#FFCC00)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #003366;
        color: white;
        border: 1px solid #FFCC00;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FFCC00;
        color: #003366;
    }
    h1, h2, h3 { color: #003366; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('base_datos_costos_uss_valdivia.csv')

df = load_data()
HISTORIAL_FILE = 'historial_pacientes.csv'

# Función de guardado en Historial
def guardar_en_historial(datos):
    if not os.path.isfile(HISTORIAL_FILE):
        pd.DataFrame([datos]).to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')
    else:
        df_hist = pd.read_csv(HISTORIAL_FILE)
        pd.concat([df_hist, pd.DataFrame([datos])], ignore_index=True).to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')

# --- FUNCIÓN GENERAR PDF CON TABLAS SEPARADAS ---
def generar_pdf(resumen, t_clinico, t_insumos, t_total, paciente, rut, doctor, obs):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Logotipo USS
    if os.path.exists("logo_uss.png"):
        pdf.image("logo_uss.png", 10, 8, 33)
        pdf.ln(20)
    
    # 2. Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(200, 10, txt="COSTIMPLANT USS - SEDE VALDIVIA", ln=True, align='C')
    
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.cell(100, 6, txt=f"Paciente: {paciente}")
    pdf.cell(90, 6, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.cell(100, 6, txt=f"RUT: {rut}", ln=True)
    pdf.cell(100, 6, txt=f"Doctor(a): {doctor}", ln=True)
    pdf.ln(10)

    # 3. Tabla de Procedimientos Clínicos (USS)
    proc_df = resumen[resumen['Proveedor'] == 'USS Valdivia']
    if not proc_df.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(200, 10, txt="1. PROCEDIMIENTOS CLINICOS (ARANCEL USS)", ln=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(85, 10, "Descripcion", 1, 0, 'C', True)
        pdf.cell(20, 10, "Cant.", 1, 0, 'C', True)
        pdf.cell(35, 10, "Unitario", 1, 0, 'C', True)
        pdf.cell(35, 10, "Subtotal", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)
        for _, row in proc_df.iterrows():
            pdf.cell(85, 10, str(row['Descripción'])[:45], 1)
            pdf.cell(20, 10, str(row['Cantidad']), 1, 0, 'C')
            pdf.cell(35, 10, f"${row['Precio Unitario']:,.0f}", 1, 0, 'C')
            pdf.cell(35, 10, f"${row['Subtotal']:,.0f}", 1, 1, 'R')
        pdf.ln(5)

    # 4. Tabla de Insumos y Biomateriales
    ins_df = resumen[resumen['Proveedor'] != 'USS Valdivia']
    if not ins_df.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(200, 10, txt="2. INSUMOS Y BIOMATERIALES", ln=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(85, 10, "Descripcion (Marca)", 1, 0, 'C', True)
        pdf.cell(20, 10, "Cant.", 1, 0, 'C', True)
        pdf.cell(35, 10, "Unitario", 1, 0, 'C', True)
        pdf.cell(35, 10, "Subtotal", 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", size=9)
        for _, row in ins_df.iterrows():
            desc_marca = f"{row['Descripción']} ({row['Proveedor']})"
            pdf.cell(85, 10, desc_marca[:45], 1)
            pdf.cell(20, 10, str(row['Cantidad']), 1, 0, 'C')
            pdf.cell(35, 10, f"${row['Precio Unitario']:,.0f}", 1, 0, 'C')
            pdf.cell(35, 10, f"${row['Subtotal']:,.0f}", 1, 1, 'R')
        pdf.ln(10)

    # 5. Diagnóstico / Observaciones
    if obs:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(200, 8, txt="Diagnostico / Observaciones:", ln=True)
        pdf.set_font("Arial", size=9)
        pdf.multi_cell(190, 5, txt=obs)
        pdf.ln(5)

    # 6. Resumen de Totales
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(140, 8, "Total Procedimientos (Pago USS):", 0, 0, 'R')
    pdf.cell(35, 8, f"${t_clinico:,.0f}", 1, 1, 'R')
    pdf.cell(140, 8, "Total Insumos (Pago Casa Comercial):", 0, 0, 'R')
    pdf.cell(35, 8, f"${t_insumos:,.0f}", 1, 1, 'R')
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(140, 12, "TOTAL PRESUPUESTO:", 0, 0, 'R')
    pdf.cell(35, 12, f"${t_total:,.0f}", 1, 1, 'R')
    
    # 7. Firmas
    pdf.ln(20)
    pdf.line(30, pdf.get_y(), 80, pdf.get_y())
    pdf.line(130, pdf.get_y(), 180, pdf.get_y())
    pdf.set_font("Arial", size=8)
    pdf.cell(90, 10, "Firma Paciente", 0, 0, 'C')
    pdf.cell(90, 10, "Firma Profesional", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ DE USUARIO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo_uss.png"):
        st.image("logo_uss.png", width=150)
with col_titulo:
    st.title("Costimplant USS")
    st.subheader("Postgrado de Implantología - Sede Valdivia")

menu = st.sidebar.radio("Navegación", ["Crear Presupuesto", "Historial de Pacientes"])

if menu == "Crear Presupuesto":
    st.sidebar.subheader("Datos del Paciente")
    nombre_p = st.sidebar.text_input("Nombre Completo")
    rut_p = st.sidebar.text_input("RUT")
    doc_p = st.sidebar.text_input("Alumno/Doctor")
    diagnostico = st.sidebar.text_area("Diagnóstico / Observaciones")

    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    # PASO 1: PROCEDIMIENTOS
    st.header("1° Seleccionar el procedimiento clínico")
    items_uss = df[df['Proveedor'] == 'USS Valdivia']
    c1, c2, c3 = st.columns([2, 1, 1])
    sel_proc = c1.selectbox("Procedimiento:", items_uss['Descripción'].tolist())
    cant_proc = c2.number_input("Cantidad:", min_value=1, value=1, key="cant_p")
    if c3.button("Añadir Procedimiento"):
        row = items_uss[items_uss['Descripción'] == sel_proc].iloc[0]
        st.session_state.carrito.append({
            'Descripción': row['Descripción'], 'Proveedor': 'USS Valdivia', 
            'Precio Unitario': row['Precio Total'], 'Cantidad': cant_proc, 'Subtotal': row['Precio Total'] * cant_proc
        })

    # PASO 2: INSUMOS
    st.header("2° Seleccionar los insumos")
    items_ins = df[df['Proveedor'] != 'USS Valdivia']
    ci1, ci2, ci3 = st.columns([2, 1, 1])
    marca_sel = ci1.selectbox("Marca/Proveedor:", items_ins['Proveedor'].unique())
    ins_filt = items_ins[items_ins['Proveedor'] == marca_sel]
    insumo_sel = ci1.selectbox("Insumo:", ins_filt['Descripción'].tolist())
    cant_ins = ci2.number_input("Cantidad:", min_value=1, value=1, key="cant_i")
    if ci3.button("Añadir Insumo"):
        row = ins_filt[ins_filt['Descripción'] == insumo_sel].iloc[0]
        st.session_state.carrito.append({
            'Descripción': row['Descripción'], 'Proveedor': marca_sel, 
            'Precio Unitario': row['Precio Total'], 'Cantidad': cant_ins, 'Subtotal': row['Precio Total'] * cant_ins
        })

    # RESUMEN ACTUAL
    if st.session_state.carrito:
        st.header("Resumen del Presupuesto Actual")
        for index, item in enumerate(st.session_state.carrito):
            col_d, col_c, col_s, col_del = st.columns([3, 1, 1, 1])
            col_d.write(f"**{item['Descripción']}** ({item['Proveedor']})")
            col_c.write(f"Cant: {item['Cantidad']}")
            col_s.write(f"${item['Subtotal']:,.0f}")
            if col_del.button("Eliminar", key=f"del_{index}"):
                st.session_state.carrito.pop(index)
                st.rerun()

        res_df = pd.DataFrame(st.session_state.carrito)
        t_uss = res_df[res_df['Proveedor'] == 'USS Valdivia']['Subtotal'].sum()
        t_ins = res_df[res_df['Proveedor'] != 'USS Valdivia']['Subtotal'].sum()
        t_total = t_uss + t_ins
        
        st.markdown("---")
        st.write(f"**Clínica USS:** ${t_uss:,.0f} | **Insumos:** ${t_ins:,.0f}")
        st.subheader(f"TOTAL: ${t_total:,.0f}")

        if st.button("💾 Guardar e Historial"):
            datos_h = {"Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Paciente": nombre_p, "RUT": rut_p, "Total": t_total}
            guardar_en_historial(datos_h)
            st.success("Guardado.")
        
        pdf_b = generar_pdf(res_df, t_uss, t_ins, t_total, nombre_p, rut_p, doc_p, diagnostico)
        st.download_button("📥 Descargar PDF", pdf_b, f"Presupuesto_{nombre_p}.pdf")

else:
    st.header("Historial de Pacientes")
    if os.path.exists(HISTORIAL_FILE):
        st.dataframe(pd.read_csv(HISTORIAL_FILE), use_container_width=True)
    else: st.info("No hay registros.")