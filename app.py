import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# 1. CONFIGURACIÓN E IDENTIDAD VISUAL USS
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

# 2. CARGA DE DATOS (VERSIÓN BLINDADA CONTRA KEYERROR)
@st.cache_data
def load_data():
    try:
        # Intentamos leer el archivo
        data = pd.read_csv('base_datos_costos_uss_valdivia.csv', encoding='utf-8')
        
        # FORZAMOS los nombres de las columnas para evitar errores de codificación o nombres distintos
        # Debe tener exactamente 7 columnas en este orden:
        data.columns = ['Categoría', 'Código', 'Descripción', 'Precio Clínica', 'Lab', 'Precio Total', 'Proveedor']
        
        # Limpieza básica
        data['Proveedor'] = data['Proveedor'].astype(str).str.strip()
        data['Categoría'] = data['Categoría'].astype(str).str.strip()
        return data
    except Exception as e:
        st.error(f"Error al cargar el archivo CSV: {e}")
        st.info("Asegúrate de que el archivo tenga 7 columnas y se llame 'base_datos_costos_uss_valdivia.csv'")
        return pd.DataFrame()

df = load_data()

HISTORIAL_FILE = 'historial_pacientes.csv'

def guardar_en_historial(datos):
    if not os.path.isfile(HISTORIAL_FILE):
        pd.DataFrame([datos]).to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')
    else:
        df_hist = pd.read_csv(HISTORIAL_FILE)
        pd.concat([df_hist, pd.DataFrame([datos])], ignore_index=True).to_csv(HISTORIAL_FILE, index=False, encoding='utf-8')

# 3. FUNCIÓN GENERAR PDF
def generar_pdf(resumen, t_total, paciente, rut, doctor, obs):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo_uss.png"):
        pdf.image("logo_uss.png", 10, 8, 40)
        pdf.ln(20)
    
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

    for prov in resumen['Proveedor'].unique():
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(0, 51, 102)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 8, f"DETALLE: {prov}", 1, 1, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(100, 8, "Descripcion", 1)
        pdf.cell(20, 8, "Cant.", 1, 0, 'C')
        pdf.cell(35, 8, "Unitario", 1, 0, 'C')
        pdf.cell(35, 8, "Subtotal", 1, 1, 'C')
        
        pdf.set_font("Arial", size=9)
        temp_df = resumen[resumen['Proveedor'] == prov]
        for _, row in temp_df.iterrows():
            pdf.cell(100, 8, str(row['Descripción'])[:50], 1)
            pdf.cell(20, 8, str(row['Cantidad']), 1, 0, 'C')
            pdf.cell(35, 8, f"${row['Precio Unitario']:,.0f}", 1, 0, 'C')
            pdf.cell(35, 8, f"${row['Subtotal']:,.0f}", 1, 1, 'R')
        pdf.ln(5)

    if obs:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(200, 8, txt="Observaciones:", ln=True)
        pdf.set_font("Arial", size=9)
        pdf.multi_cell(190, 5, txt=obs)
        pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 10, "TOTAL ESTIMADO:", 0, 0, 'R')
    pdf.cell(40, 10, f"${t_total:,.0f}", 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# 4. INTERFAZ PRINCIPAL
if df.empty:
    st.warning("Carga una base de datos válida para comenzar.")
else:
    col_l, col_t = st.columns([1, 4])
    with col_l:
        if os.path.exists("logo_uss.png"): st.image("logo_uss.png", width=120)
    with col_t:
        st.title("Costimplant USS")

    menu = st.sidebar.radio("Navegación", ["Crear Presupuesto", "Historial de Pacientes"])

    if menu == "Crear Presupuesto":
        st.sidebar.subheader("Datos del Paciente")
        n_p = st.sidebar.text_input("Nombre")
        r_p = st.sidebar.text_input("RUT")
        d_p = st.sidebar.text_input("Doctor/Alumno")
        obs_p = st.sidebar.text_area("Observaciones")

        if 'carrito' not in st.session_state: st.session_state.carrito = []

        # --- PASO 1: USS VALDIVIA ---
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

        # --- PASO 2: INSUMOS ---
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

        # --- RESUMEN ---
        if st.session_state.carrito:
            st.markdown("---")
            st.subheader("Resumen del Presupuesto")
            for i, item in enumerate(st.session_state.carrito):
                r1, r2, r3, r4, r5 = st.columns([3, 1, 1, 1, 1])
                r1.write(f"**{item['Descripción']}** ({item['Proveedor']})")
                r2.write(f"Cant: {item['Cantidad']}")
                
                if r3.button("✏️", key=f"ed_{i}"): st.session_state[f"edit_{i}"] = True
                if st.session_state.get(f"edit_{i}", False):
                    new_v = r1.number_input("Editar Precio Unitario:", value=float(item['Precio Unitario']), key=f"val_{i}")
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
            st.subheader(f"TOTAL FINAL ESTIMADO: ${total:,.0f}")

            if st.button("💾 Guardar en Historial"):
                guardar_en_historial({"Fecha": datetime.now().strftime("%d/%m/%Y"), "Paciente": n_p, "Total": total})
                st.success("Presupuesto guardado con éxito.")
            
            pdf_b = generar_pdf(res_df, total, n_p, r_p, d_p, obs_p)
            st.download_button("📥 Descargar PDF", pdf_b, f"Presupuesto_{n_p}.pdf")

    else:
        st.header("Historial de Pacientes")
        if os.path.exists(HISTORIAL_FILE):
            st.dataframe(pd.read_csv(HISTORIAL_FILE), use_container_width=True)
        else:
            st.info("Aún no hay registros en el historial.")