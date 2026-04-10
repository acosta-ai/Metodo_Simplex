import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import linprog

st.set_page_config(page_title="Simplex Real", page_icon="🎯")
st.title("🎯 Simplex Pro: Solución Exacta")

# Configuración rápida en la barra lateral
st.sidebar.header("Ajustes")
tipo = st.sidebar.radio("Objetivo:", ("Maximizar", "Minimizar"))

# Datos de entrada
st.subheader("1. Función Objetivo (Z)")
c1, c2 = st.columns(2)
z1 = c1.number_input("Coeficiente x1", value=25.0)
z2 = c2.number_input("Coeficiente x2", value=40.0)

st.subheader("2. Restricciones")
r1_col = st.columns(3)
r1_x1 = r1_col[0].number_input("x1 (R1)", value=2.0)
r1_x2 = r1_col[1].number_input("x2 (R1)", value=3.0)
r1_b = r1_col[2].number_input("RHS (R1)", value=120.0)

r2_col = st.columns(3)
r2_x1 = r2_col[0].number_input("x1 (R2)", value=4.0)
r2_x2 = r2_col[1].number_input("x2 (R2)", value=2.0)
r2_b = r2_col[2].number_input("RHS (R2)", value=100.0)

if st.button("🚀 RESOLVER AHORA", type="primary", use_container_width=True):
    # Preparación matemática
    obj = [-z1, -z2] if tipo == "Maximizar" else [z1, z2]
    lhs = [[r1_x1, r1_x2], [r2_x1, r2_x2]]
    rhs = [r1_b, r2_b]
    
    # EL SECRETO: Usamos 'revised simplex' para que haga el cálculo manual
    res = linprog(c=obj, A_ub=lhs, b_ub=rhs, method='revised simplex')
    
    if res.success:
        st.balloons()
        final_z = abs(res.fun)
        
        st.success(f"### ✅ ¡Solución de la Pizarra Encontrada!")
        
        col_a, col_b = st.columns(2)
        col_a.metric("Valor de x1", f"{res.x[0]:.2f}")
        col_b.metric("Valor de x2", f"{res.x[1]:.2f}")
        st.metric("Beneficio Máximo (Z)", f"{final_z:,.2f}")
        
        st.info(f"**Resultado:** Para ganar **{final_z:,.2f}**, debes producir **{res.x[0]}** de x1 y **{res.x[1]}** de x2. ¡Igual que en tu cuaderno!")
    else:
        st.error("Revisa los datos, no se encontró solución.")
