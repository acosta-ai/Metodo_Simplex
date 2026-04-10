import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import linprog

st.set_page_config(page_title="Simplex Pro", page_icon="📊", layout="wide")
st.title("📊 Simplex Pro: Analizador Dinámico")

# --- CONFIGURACIÓN ---
st.sidebar.header("Configuración")
tipo_opt = st.sidebar.radio("Objetivo del Problema:", ("Maximizar", "Minimizar"))
n_vars = st.sidebar.number_input("Número de Variables", min_value=1, value=2)
n_restr = st.sidebar.number_input("Número de Restricciones", min_value=1, value=2)

# --- ENTRADA DE DATOS ---
st.subheader("1. Coeficientes de la Función Objetivo (Z)")
c = []
cols_z = st.columns(n_vars)
for i in range(n_vars):
    val = cols_z[i].number_input(f"Coeficiente x{i+1}", value=0.0, key=f"obj_{i}")
    c.append(-float(val) if tipo_opt == "Maximizar" else float(val))

st.subheader("2. Restricciones")
A_ub, b_ub = [], []
for i in range(n_restr):
    with st.expander(f"Restricción {i+1}", expanded=True):
        cols_r = st.columns(n_vars + 1)
        fila = []
        for j in range(n_vars):
            val_r = cols_r[j].number_input(f"x{j+1} (R{i+1})", value=0.0, key=f"restr_{i}_{j}")
            fila.append(float(val_r))
        rhs = cols_r[-1].number_input(f"Lado Derecho (RHS) {i+1}", value=0.0, key=f"rhs_{i}")
        A_ub.append(fila)
        b_ub.append(float(rhs))

# --- BOTÓN DE RESOLVER ---
st.divider()
if st.button("🚀 CALCULAR SOLUCIÓN ÓPTIMA", type="primary", use_container_width=True):
    try:
        # Usamos el método 'highs' que es el más preciso actualmente
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method='highs')
        
        if res.success:
            st.balloons()
            val_z = -res.fun if tipo_opt == "Maximizar" else res.fun
            
            # --- RESULTADOS PRINCIPALES ---
            st.success(f"### 🎉 ¡Solución Final Encontrada!")
            st.metric(label=f"Valor Óptimo de Z ({tipo_opt})", value=f"{val_z:,.2f}")
            
            # --- TABLA DE VARIABLES ---
            st.write("### 📝 Valores finales en la pizarra (V.I.):")
            df_res = pd.DataFrame({
                "Variable": [f"x{i+1}" for i in range(n_vars)],
                "Valor Óptimo": [round(x, 4) for x in res.x],
                "Estado": ["En la Base" if x > 0.0001 else "Fuera de la Base" for x in res.x]
            })
            st.table(df_res)
            
            # --- COMPARATIVA DE PIZARRA ---
            st.info(f"""
            **Interpretación:**
            * Para obtener el máximo de **{val_z:,.2f}**, el sistema determinó que:
            * **x1** debe valer **{res.x[0]:,.2f}**
            * **x2** debe valer **{res.x[1]:,.2f}**
            *(Si estos números coinciden con tu segunda tabla, ¡el ejercicio está perfecto!)*
            """)
        else:
            st.error(f"❌ No se pudo optimizar: {res.message}")
    except Exception as e:
        st.error(f"⚠️ Error: Asegúrate de llenar todos los espacios. {e}")
