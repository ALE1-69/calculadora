import streamlit as st
import math

# --- FUNÇÕES DE APOIO (WILHELM, 1976) ---

def calcular_pws(t_c):
    """Pressão de saturação em kPa [cite: 35, 45-55]."""
    T = t_c + 273.15
    if t_c < 0:
        return math.exp(24.2779 - (6238.64 / T) - 0.344438 * math.log(T)) # [1a]
    return math.exp((-7511.52 / T) + 89.63121 + (0.023998970 * T) - 
                    (1.1654551e-5 * (T**2)) - (1.2810336e-8 * (T**3)) + 
                    (2.0998405e-11 * (T**4)) - (12.150799 * math.log(T))) # [1b]

def calcular_w_equacao_16(t, t_star, p):
    """Calcula W a partir de t e t_star usando a Eq. [16] [cite: 142-144]."""
    pws_star = calcular_pws(t_star)
    ws_star = 0.62198 * pws_star / (p - pws_star) # [2]
    num = (2501 - 2.411 * t_star) * ws_star - 1.006 * (t - t_star)
    den = 2501 + 1.775 * t - 4.186 * t_star
    return num / den

def calcular_tbu_secante(t_bs, w_alvo, p):
    """Encontra t* por tentativa e erro (Método da Secante) ."""
    x0 = t_bs - 10  # Estimativa inicial 1
    x1 = t_bs       # Estimativa inicial 2
    
    def f(t_teste):
        return w_alvo - calcular_w_equacao_16(t_bs, t_teste, p)

    for _ in range(20):
        f_x0, f_x1 = f(x0), f(x1)
        if abs(f_x1 - f_x0) < 1e-9: break
        x2 = x1 - f_x1 * (x1 - x0) / (f_x1 - f_x0)
        x0, x1 = x1, x2
        if abs(x1 - x0) < 0.001: return x1
    return x1

def calcular_tdp_regressao(pw):
    """Ponto de orvalho via regressão [cite: 126-136]."""
    a = math.log(pw)
    if pw <= 0.611: return 5.994 + 12.41 * a + 0.4273 * (a**2)
    elif pw <= 12.33: return 6.983 + 14.38 * a + 1.079 * (a**2)
    return 13.80 + 9.478 * a + 1.991 * (a**2)

# --- INTERFACE ---
st.set_page_config(page_title="Ambiência Wilhelm Pro", page_icon="🌡️")
st.title("📊 Ambiência Animal: Wilhelm (1976)")

# Configurações na Barra Lateral
st.sidebar.header("Configurações")
altitude = st.sidebar.number_input("Altitude (m)", value=918)
p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
especie = st.sidebar.selectbox("Espécie", ["Bovinos", "Aves", "Suínos"])

# Entrada de Dados
metodo = st.radio("Entrada:", ["TBS e UR%", "TBS e TBU", "TBS e TPO"], horizontal=True)
col1, col2 = st.columns(2)
with col1: tbs = st.number_input("TBS (°C)", value=30.0)
with col2: 
    if metodo == "TBS e UR%": dado2 = st.number_input("UR (%)", value=50.0)
    elif metodo == "TBS e TBU": dado2 = st.number_input("TBU (°C)", value=22.0)
    else: dado2 = st.number_input("TPO (°C)", value=18.0)

if st.button("CALCULAR"):
    try:
        if metodo == "TBS e UR%":
            phi = dado2 / 100.0
            pws = calcular_pws(tbs)
            pw = phi * pws
            w = 0.62198 * pw / (p_atm - pw)
            tdp = calcular_tdp_regressao(pw)
            tbu = calcular_tbu_secante(tbs, w, p_atm) # Passo 5 do artigo
        elif metodo == "TBS e TBU":
            tbu = dado2
            w = calcular_w_equacao_16(tbs, tbu, p_atm)
            pw = (p_atm * w) / (0.62198 + w)
            phi = (pw / calcular_pws(tbs)) * 100
            tdp = calcular_tdp_regressao(pw)
        else:
            tdp = dado2
            pw = calcular_pws(tdp)
            phi = (pw / calcular_pws(tbs)) * 100
            w = 0.62198 * pw / (p_atm - pw)
            tbu = calcular_tbu_secante(tbs, w, p_atm)

        h = 1.006 * tbs + w * (2501 + 1.775 * tbs)
        itu = (tbs + 273.15) + 0.36 * (tdp + 273.15) - 330.08
        
        # Exibição
        st.success(f"### ITU: {itu:.2f}")
        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("TBU (°C)", f"{tbu:.2f} °C")
        res_col2.metric("UR (%)", f"{phi:.1f}%")
        res_col3.metric("Entalpia", f"{h:.2f} kJ/kg")
        
        st.write(f"**Ponto de Orvalho:** {tdp:.2f} °C | **W:** {w:.5f} kg/kg | **P. Atmosférica:** {p_atm:.2f} kPa")

    except Exception:
        st.error("Erro nos cálculos. Verifique os valores.")
