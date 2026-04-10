import numpy as np
import pandas as pd
import fractions

def to_fraction_str(val):
    if pd.isna(val):
        return ""
    frac = fractions.Fraction(val).limit_denominator(1000)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"

class SimplexModel:
    def __init__(self, obj_type, c, A, signs, b, var_names):
        self.obj_type = obj_type # 'max' or 'min'
        self.c = list(c)
        self.A = [list(row) for row in A]
        self.signs = list(signs)
        self.b = list(b)
        self.var_names = list(var_names)
        self.big_m = 1000000.0 # representing Big M
        self.tables = []
        
    def solve(self):
        # 1. Setup initial tableau
        # Variables: X..., S..., E..., A..., RHS
        n_vars = len(self.c)
        m_constraints = len(self.A)
        
        # Ensure RHS >= 0
        for i in range(m_constraints):
            if self.b[i] < 0:
                self.b[i] = -self.b[i]
                self.A[i] = [-v for v in self.A[i]]
                if self.signs[i] == '<=':
                    self.signs[i] = '>='
                elif self.signs[i] == '>=':
                    self.signs[i] = '<='
        
        slacks = []
        surplus = []
        artificials = []
        
        col_names = list(self.var_names)
        
        # Add variables based on signs
        for i, sign in enumerate(self.signs):
            if sign == '<=':
                col_names.append(f"S{i+1}")
                slacks.append(i)
            elif sign == '>=':
                col_names.append(f"E{i+1}")
                col_names.append(f"A{i+1}")
                surplus.append(i)
                artificials.append(i)
            elif sign == '=':
                col_names.append(f"A{i+1}")
                artificials.append(i)
        
        col_names.append("RHS")
        n_cols = len(col_names)
        
        tableau = np.zeros((m_constraints + 1, n_cols), dtype=float)
        
        # Fill A part
        for i in range(m_constraints):
            tableau[i, :n_vars] = self.A[i]
            tableau[i, -1] = self.b[i]
            
        basis_vars = []
        
        # Position mapping
        current_col = n_vars
        for i, sign in enumerate(self.signs):
            if sign == '<=':
                tableau[i, current_col] = 1.0
                basis_vars.append(col_names[current_col])
                current_col += 1
            elif sign == '>=':
                tableau[i, current_col] = -1.0 # E
                current_col += 1
                tableau[i, current_col] = 1.0 # A
                basis_vars.append(col_names[current_col])
                current_col += 1
            elif sign == '=':
                tableau[i, current_col] = 1.0 # A
                basis_vars.append(col_names[current_col])
                current_col += 1

        # Z row definition initially
        # Z - C = 0
        
        if self.obj_type == 'Maximizar':
            # Maximize: Z row = -C
            tableau[-1, :n_vars] = [-v for v in self.c]
            # Artificials cost -M in obj, so in Z-row it's +M
            for i, sign in enumerate(self.signs):
                if sign in ['>=', '=']:
                    # Find A column
                    idx = basis_vars[i]
                    col_idx = col_names.index(idx)
                    tableau[-1, col_idx] = self.big_m
        else: # Minimizar
            # Minimize: Z row = C
            tableau[-1, :n_vars] = [v for v in self.c]
            # Artificials cost M in obj, so in Z-row it's -M
            for i, sign in enumerate(self.signs):
                if sign in ['>=', '=']:
                    idx = basis_vars[i]
                    col_idx = col_names.index(idx)
                    tableau[-1, col_idx] = -self.big_m

        # Normalize Z-row to clear Big M columns
        for i, b_var in enumerate(basis_vars):
            if b_var.startswith('A'):
                col_idx = col_names.index(b_var)
                m_coef = tableau[-1, col_idx]
                # subtract m_coef * row from Z-row
                tableau[-1, :] -= m_coef * tableau[i, :]
                
        def save_table():
            df = pd.DataFrame(tableau, columns=col_names, index=basis_vars + ['Z'])
            self.tables.append(df.copy())

        save_table()
        
        iteration = 0
        while iteration < 100: # prevent infinite loops
            # Find entering variable
            if self.obj_type == 'Maximizar':
                # Most negative in Z row (excluding RHS)
                z_row = tableau[-1, :-1]
                if np.all(z_row >= -1e-7):
                    break # Optimal
                enter_idx = np.argmin(z_row)
            else:
                # Most positive in Z row (excluding RHS)
                z_row = tableau[-1, :-1]
                if np.all(z_row <= 1e-7):
                    break # Optimal
                enter_idx = np.argmax(z_row)
                
            # Find leaving variable using ratio test
            enter_col = tableau[:-1, enter_idx]
            rhs_col = tableau[:-1, -1]
            
            ratios = []
            for i in range(m_constraints):
                if enter_col[i] > 1e-7:
                    ratios.append(rhs_col[i] / enter_col[i])
                else:
                    ratios.append(float('inf'))
            
            if all(r == float('inf') for r in ratios):
                return "Infactible/Unbounded" # Unbounded
                
            leave_idx = np.argmin(ratios)
            
            # Pivot
            pivot = tableau[leave_idx, enter_idx]
            tableau[leave_idx, :] /= pivot
            
            for i in range(m_constraints + 1):
                if i != leave_idx:
                    factor = tableau[i, enter_idx]
                    tableau[i, :] -= factor * tableau[leave_idx, :]
                    
            basis_vars[leave_idx] = col_names[enter_idx]
            save_table()
            iteration += 1

        return "Optimal"

if __name__ == "__main__":
    A = [[2/3, 1], [8/3, 0]]
    c = [5/2, 40]
    signs = ['<=', '<=']
    b = [40, 20]
    model = SimplexModel('Maximizar', c, A, signs, b, ['X1', 'X2'])
    model.solve()
    for t in model.tables:
        print(t)
