import streamlit as st
import pandas as pd
import numpy as np
from fractions import Fraction

def format_frac(val):
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"

class MNum:
    def __init__(self, m, num):
        self.m = Fraction(m)
        self.num = Fraction(num)
        
    def __add__(self, other):
        if isinstance(other, MNum): return MNum(self.m + other.m, self.num + other.num)
        return MNum(self.m, self.num + Fraction(other))
        
    __radd__ = __add__
        
    def __sub__(self, other):
        if isinstance(other, MNum): return MNum(self.m - other.m, self.num - other.num)
        return MNum(self.m, self.num - Fraction(other))
        
    def __rsub__(self, other):
        o = other if isinstance(other, MNum) else MNum(0, Fraction(other))
        return o - self
        
    def __mul__(self, other):
        if isinstance(other, MNum): raise ValueError("Cannot multiply MNum by MNum")
        return MNum(self.m * Fraction(other), self.num * Fraction(other))
        
    __rmul__ = __mul__
    
    def __truediv__(self, other):
        return MNum(self.m / Fraction(other), self.num / Fraction(other))
        
    def __neg__(self):
        return MNum(-self.m, -self.num)
        
    def __lt__(self, other):
        o_m, o_n = (other.m, other.num) if isinstance(other, MNum) else (Fraction(0), Fraction(other))
        if self.m < o_m: return True
        elif self.m > o_m: return False
        return self.num < o_n

    def __le__(self, other):
        o_m, o_n = (other.m, other.num) if isinstance(other, MNum) else (Fraction(0), Fraction(other))
        if self.m < o_m: return True
        elif self.m > o_m: return False
        return self.num <= o_n
        
    def __gt__(self, other): return not self.__le__(other)
    def __ge__(self, other): return not self.__lt__(other)
    
    def __eq__(self, other):
        o_m, o_n = (other.m, other.num) if isinstance(other, MNum) else (Fraction(0), Fraction(other))
        return self.m == o_m and self.num == o_n
        
    def __float__(self):
        return float(self.m * 1000000 + self.num)
        
    def __str__(self):
        if self.m == 0:
            return format_frac(self.num)
        elif self.num == 0:
            if self.m == 1: return "M"
            elif self.m == -1: return "-M"
            return f"{format_frac(self.m)}M"
        else:
            m_s = "M" if self.m == 1 else ("-M" if self.m == -1 else f"{format_frac(self.m)}M")
            n_s = format_frac(abs(self.num))
            sign = "+" if self.num > 0 else "-"
            return f"{m_s} {sign} {n_s}"

class SimplexSolver:
    def __init__(self, tipo_opt, c, A, b, signs, var_names):
        self.tipo_opt = tipo_opt
        self.m_restr = len(A)
        self.c = c
        self.A = A
        self.b = b
        self.signs = signs.copy()
        
        self.var_names = list(var_names)
        self.col_names = list(var_names)
        self.C_base = []
        self.base_vars = []
        self.tables = []
        
    def solve(self):
        # Standardize b >= 0
        for i in range(self.m_restr):
            if self.b[i] < 0:
                self.b[i] = -self.b[i]
                self.A[i] = [-val for val in self.A[i]]
                if self.signs[i] == "<=": self.signs[i] = ">="
                elif self.signs[i] == ">=": self.signs[i] = "<="

        # Build C_j as MNum
        C_j = []
        for x in self.c:
            if self.tipo_opt == "Minimizar":
                C_j.append(MNum(0, -Fraction(x)))
            else:
                C_j.append(MNum(0, Fraction(x)))

        A_matrix = [[Fraction(v) for v in row] for row in self.A]
        
        for i in range(self.m_restr):
            if self.signs[i] == "<=":
                name = f"S{i+1}"
                self.col_names.append(name)
                C_j.append(MNum(0, 0))
                self.base_vars.append(name)
                self.C_base.append(MNum(0, 0))
                for j in range(self.m_restr):
                    A_matrix[j].append(Fraction(1) if j == i else Fraction(0))
            elif self.signs[i] == ">=":
                name_e = f"E{i+1}"
                self.col_names.append(name_e)
                C_j.append(MNum(0, 0))
                
                name_a = f"A{i+1}"
                self.col_names.append(name_a)
                C_j.append(MNum(-1, 0)) # -1M
                
                self.base_vars.append(name_a)
                self.C_base.append(MNum(-1, 0))
                
                for j in range(self.m_restr):
                    A_matrix[j].append(Fraction(-1) if j == i else Fraction(0))
                    A_matrix[j].append(Fraction(1) if j == i else Fraction(0))
            elif self.signs[i] == "=":
                name_a = f"A{i+1}"
                self.col_names.append(name_a)
                C_j.append(MNum(-1, 0)) # -1M
                
                self.base_vars.append(name_a)
                self.C_base.append(MNum(-1, 0))
                
                for j in range(self.m_restr):
                    A_matrix[j].append(Fraction(1) if j == i else Fraction(0))
                    
        tableau = [row + [Fraction(self.b[i])] for i, row in enumerate(A_matrix)]
        cols = len(C_j)
        
        status = "En progreso"
        ans_z = None
        
        for iteration in range(100):
            # calc Z row
            Zj_Cj = []
            for j in range(cols):
                zj = sum((self.C_base[i] * tableau[i][j] for i in range(self.m_restr)), start=MNum(0,0))
                Zj_Cj.append(zj - C_j[j])
            
            z_val = sum((self.C_base[i] * tableau[i][-1] for i in range(self.m_restr)), start=MNum(0,0))
            
            # format tableau
            str_tableau = []
            for i in range(self.m_restr):
                row_str = [format_frac(x) for x in tableau[i]]
                str_tableau.append([self.base_vars[i]] + row_str)
                
            str_z_row = ["Z"] + [str(x) for x in Zj_Cj] + [str(z_val)]
            str_tableau.append(str_z_row)
            
            df_cols = ["Base"] + self.col_names + ["RHS"]
            df = pd.DataFrame(str_tableau, columns=df_cols)
            self.tables.append(df)
            
            # Check optimal: all Zj - Cj >= 0 (since we continuously maximize)
            if all(z >= MNum(0,0) for z in Zj_Cj):
                status = "Óptimo"
                ans_z = z_val
                break
                
            # Find entering var (most negative Zj - Cj)
            enter_col = -1
            min_val = MNum(0, 0)
            for j in range(cols):
                if Zj_Cj[j] < MNum(0, 0) and Zj_Cj[j] < min_val:
                    min_val = Zj_Cj[j]
                    enter_col = j
                    
            if enter_col == -1:
                status = "Óptimo"
                ans_z = z_val
                break
                
            # Ratio test
            leave_row = -1
            min_ratio = None
            for i in range(self.m_restr):
                if tableau[i][enter_col] > 0:
                    ratio = tableau[i][-1] / tableau[i][enter_col]
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        leave_row = i
                        
            if leave_row == -1:
                status = "No acotado"
                break
                
            # Pivot
            pivot = tableau[leave_row][enter_col]
            tableau[leave_row] = [val / pivot for val in tableau[leave_row]]
            
            for i in range(self.m_restr):
                if i != leave_row:
                    factor = tableau[i][enter_col]
                    tableau[i] = [tableau[i][j] - factor * tableau[leave_row][j] for j in range(cols + 1)]
                    
            self.base_vars[leave_row] = self.col_names[enter_col]
            self.C_base[leave_row] = C_j[enter_col]
            
        if status == "Óptimo":
            # Check artificials
            for i in range(self.m_restr):
                if "A" in self.base_vars[i] and tableau[i][-1] > 0:
                    status = "Infactible"
                    
            if self.tipo_opt == "Minimizar" and ans_z is not None:
                ans_z = -ans_z
                
        # Final answer values parsing to float for metrics
        ans_vars = {name: 0.0 for name in self.var_names}
        if status == "Óptimo":
            for i in range(self.m_restr):
                if self.base_vars[i] in ans_vars:
                    ans_vars[self.base_vars[i]] = float(tableau[i][-1])
        
        return status, ans_z, self.tables, ans_vars

# Configuración de la página
st.set_page_config(page_title="Simplex Pro", page_icon="📈", layout="wide")
st.title("📈 Simplex Pro: Analizador de Decisiones con Tablas")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
tipo_opt = st.sidebar.radio("Objetivo del Problema:", ("Maximizar", "Minimizar"))
n_vars = st.sidebar.number_input("Variables de Decisión", min_value=1, max_value=10, value=2)
n_restr = st.sidebar.number_input("Total de Restricciones", min_value=1, max_value=15, value=2)

# --- NOMBRES DE VARIABLES ---
st.subheader("1. Identificación de Variables")
st.info("Asigna nombres a tus variables para que la conclusión sea más clara.")
nombres_vars = []
cols_nombres = st.columns(n_vars)
for i in range(n_vars):
    with cols_nombres[i]:
        nombre = st.text_input(f"Nombre de x{i+1}", value=f"X{i+1}", key=f"name_{i}")
        nombres_vars.append(nombre)

# --- FUNCIÓN OBJETIVO ---
st.subheader(f"2. Función Objetivo a {tipo_opt}")
c = []
cols_z = st.columns(n_vars)
for i in range(n_vars):
    with cols_z[i]:
        val = st.number_input(f"Coef. de {nombres_vars[i]}", value=0.0, key=f"c_{i}")
        c.append(val)

# --- RESTRICCIONES ---
st.subheader("3. Restricciones del Sistema")
A = []
b = []
signs = []

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
            
        A.append(fila_actual)
        signs.append(signo)
        b.append(rhs)

# --- PROCESAMIENTO ---
st.divider()
if st.button("📊 GENERAR ANÁLISIS FINAL", type="primary", use_container_width=True):
    try:
        solver = SimplexSolver(tipo_opt, c, A, b, signs, nombres_vars)
        status, z_val, tables, ans_vars = solver.solve()
        
        # Display Tables
        st.subheader("📝 Evolución de las Tablas Simplex")
        for idx, table in enumerate(tables):
            st.markdown(f"**Iteración {idx}**")
            st.dataframe(table, use_container_width=True, hide_index=True)
            
        if status == "Óptimo":
            # --- RESULTADOS MÉTRICOS ---
            st.success("✅ Análisis Completado Exitosamente")
            val_z_float = float(z_val) if isinstance(z_val, MNum) else float(z_val)
            st.metric(label=f"Resultado Óptimo de Z ({tipo_opt})", value=f"{val_z_float:,.2f}")
            
            # --- TABLA DE RESULTADOS ---
            df_res = pd.DataFrame({
                "Variable": nombres_vars,
                "Valor Óptimo": [ans_vars[v] for v in nombres_vars],
                "Impacto Unitario (Coef Objectivo)": c
            })
            st.table(df_res)
            
            # --- CONCLUSIONES AUTOMÁTICAS ---
            st.subheader("📝 Conclusiones del Modelo")
            
            max_var = max(ans_vars, key=ans_vars.get)
            max_val = ans_vars[max_var]
            ceros = [v for v, val in ans_vars.items() if val == 0]
            
            conclusion_text = f"""
            Basado en el modelo de Programación Lineal ejecutado:
            * Para lograr un **{tipo_opt.lower()}** de **{val_z_float:,.2f}** en la función objetivo, se deben asignar los valores mostrados en la tabla.
            * La variable con mayor presencia en la solución es **{max_var}** con un valor de **{max_val:,.2f}**.
            * {'Variables como ' + ', '.join(ceros) + ' no deberían ser priorizadas (valor 0)' if len(ceros) > 0 else 'Todas las variables contribuyen activamente a la solución.'}
            """
            st.info(conclusion_text)
            
            st.balloons()
        elif status == "Infactible":
            st.error("Infactible: No se encontró una región factible que cumpla con todas las restricciones.")
        elif status == "No acotado":
            st.warning("No acotado: La solución del problema puede mejorar infinitamente sin violar restricciones.")
            
    except Exception as e:
        import traceback
        st.error(f"Error en los datos o en el procesamiento: {e}")
        st.code(traceback.format_exc())
