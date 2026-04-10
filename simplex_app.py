import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import linprog

# Configuración de la página
st.set_page_config(page_title="Simplex Pro", page_icon="📈", layout="wide")
st.title("📈 Simplex Pro: Analizador de Decisiones")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
tipo_opt = st.sidebar.radio("Objetivo del Problema:", ("Maximizar", "Minimizar"))
n_vars = st.sidebar.number_input("Variables de Decisión", min_value=2, max_value=10, value=2)
n_restr = st.sidebar.number_input("Total de Restricciones", min_value=1, max_value=15, value=2)

# --- NOMBRES DE VARIABLES ---
st.subheader("1. Identificación de Variables")
st.info("Asigna nombres a tus variables para que la conclusión sea más clara.")
nombres_vars = []
cols_nombres = st.columns(n_vars)
for i in range(n_vars):
    with cols_nombres[i]:
        nombre = st.text_input(f"Nombre de x{i+1}", value=f"Variable {i+1}", key=f"name_{i}")
        nombres_vars.append(nombre)

# --- FUNCIÓN OBJETIVO ---
st.subheader(f"2. Función Objetivo a {tipo_opt}")
c = []
cols_z = st.columns(n_vars)
for i in range(n_vars):
    with cols_z[i]:
        val = st.number_input(f"Coef. de {nombres_vars[i]}", value=0.0, key=f"c_{i}")
        c.append(-val if tipo_opt == "Maximizar" else val)

# --- RESTRICCIONES ---
st.subheader("3. Restricciones del Sistema")
A_ub, b_ub, A_eq, b_eq = [], [], [], []

for i in range(n_restr):
    with st.expander(f"Configurar Restricción {i+1}", expanded=True):
        cols_r = st.columns(n_vars + 2)
        fila_actual = []
        for j in range(n_vars):
            with cols_r[j]:
                fila_actual.append(st.number_input(f"{nombres_vars[j]} (R{i+1})", value=0.0, key=f"r_{i}_{j}"))
        
        with cols_r[n_vars]:
            signo = st.selectbox("Signo", ("<=", ">=", "="), key=f"signo_{i}")
        with cols_r[n_vars + 1]:
            rhs = st.number_input("Lado Der. (RHS)", value=0.0, key=f"rhs_{i}")
        
        if signo == "<=":
            A_ub.append(fila_actual); b_ub.append(rhs)
        elif signo == ">=":
            A_ub.append([-x for x in fila_actual]); b_ub.append(-rhs)
        else:
            A_eq.append(fila_actual); b_eq.append(rhs)

# --- PROCESAMIENTO ---
st.divider()
if st.button("📊 GENERAR ANÁLISIS FINAL", type="primary", use_container_width=True):
    try:
        res = linprog(
            c, 
            A_ub=A_ub if A_ub else None, b_ub=b_ub if b_ub else None,
            A_eq=A_eq if A_eq else None, b_eq=b_eq if b_eq else None,
            bounds=(0, None), method='highs'
        )

        if res.success:
            val_z = -res.fun if tipo_opt == "Maximizar" else res.fun
            
            # --- RESULTADOS MÉTRICOS ---
            st.success("✅ Análisis Completado Exitosamente")
            st.metric(label=f"Resultado Óptimo de Z ({tipo_opt})", value=f"{val_z:,.2f}")
            
            # --- TABLA DE RESULTADOS ---
            df_res = pd.DataFrame({
                "Variable": nombres_vars,
                "Valor Óptimo": res.x,
                "Impacto Unitario": [abs(x) for x in c]
            })
            st.table(df_res)

            # --- CONCLUSIONES AUTOMÁTICAS ---
            st.subheader("📝 Conclusiones del Modelo")
            
            conclusion_text = f"""
            Basado en el modelo de Programación Lineal ejecutado:
            * Para lograr un **{tipo_opt.lower()}** de **{val_z:,.2f}** en la función objetivo, se deben asignar los valores mostrados en la tabla.
            * La variable con mayor presencia en la solución es **{nombres_vars[np.argmax(res.x)]}** con un valor de **{max(res.x):,.2f}**.
            * {'Variables como ' + ', '.join([nombres_vars[i] for i, v in enumerate(res.x) if v == 0]) + ' no deberían ser priorizadas (valor 0)' if 0 in res.x else 'Todas las variables contribuyen activamente a la solución.'}
            """
            st.info(conclusion_text)
            
            st.balloons()
        else:
            st.error(f"Infactible: {res.message}")
    except Exception as e:
        st.error(f"Error en los datos: {e}")