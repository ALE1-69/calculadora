import streamlit as st
import math

# --- FUNÇÕES MATEMÁTICAS (WILHELM, 1976) ---

def calcular_pws(t_c):
    """Pressão de saturação em kPa [cite: 35, 45-55]."""
    T = t_c + 273.15
    if t_c < 0:
        # Equação [1a] para -40 a 0 °C [cite: 38-42]
        return math.exp(24.2779 - (6238.64 / T) - 0.344438 * math.log(T)) 
    # Equação [1b] para 0 a 120 °C [cite: 46-55]
    return math.exp((-7511.52 / T) + 89.63121 + (0.023998970 * T) - 
                    (1.1654551e-5 * (T**2)) - (1.2810336e-8 * (T**3)) + 
                    (2.0998405e-11 * (T**4)) - (12.150799 * math.log(T))) 

def calcular_tdp_regressao(pw):
    """Ponto de orvalho via regressão [cite: 126-136]."""
    a = math.log(pw)
    if pw <= 0.611: return 5.994 + 12.41 * a + 0.4273 * (a**2) # [11a]
    elif pw <= 12.33: return 6.983 + 14.38 * a + 1.079 * (a**2) # [11b]
    return 13.80 + 9.478 * a + 1.991 * (a**2) # [11c]

# --- FUNÇÕES PARA CÁLCULO ITERATIVO DA TBU (t*) ---

def calcular_w_equacao_16(t, t_star, p):
    """Calcula a razão de mistura a partir da TBU usando a Eq. [16] ."""
    pws_star = calcular_pws(t_star)
    ws_star = 0.62198 * pws_star / (p - pws_star) # [2] [cite: 62-63]
    num = (2501 - 2.411 * t_star) * ws_star - 1.006 * (t - t_star)
    den = 2501 + 1.775 * t - 4.186 * t_star
    return num / den

def encontrar_tbu_secante(t_bs, w_alvo, p, tdp_inicial):
    """Resolve t* por tentativa e erro usando o Método da Secante ."""
    # Estimativas iniciais: o bulbo úmido está entre o ponto de orvalho e o bulbo seco
    x0 = tdp_inicial
    x1 = t_bs
    
    def f(t_teste):
        return w_alvo - calcular_w_equacao_16(t_bs, t_teste, p)

    for _ in range(20): # Limite de iterações para convergência
        f_x0 = f(x0)
        f_x1 = f(x1)
        if abs(f_x1 - f_x0) < 1e-9: break
        x2 = x1 - f_x1 * (x1 - x0) / (f_x1 - f_x0)
        x0, x1 = x1, x2
        if abs(x1 - x0) < 0.001: return x1 # Precisão de 0.001°C
    return x1

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Calculadora Ambiência Wilhelm", page_icon="🌡️")
st.title("|GEA117 - Construções e Ambiência| Calculadora de Ambiência Animal")
st.markdown(f"**Baseado em:** Numerical Calculation of Psychrometric Properties in SI Units, ASAE, Wilhelm (1976) | **Feito por:** Alexandre Klein, Graduando Eng. Agrícola pela Universidade Federal de Lavras")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.header("Configurações Locais")
altitude = st.sidebar.number_input("Altitude (m)", value=0, help="Ex: Padrão 0m")
p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
st.sidebar.write(f"Pressão estimada: **{p_atm:.2f} kPa**")

especie = st.sidebar.selectbox("Espécie Animal", ["Bovino Leiteiro", "Aves", "Suínos"])

# --- ENTRADA DE DADOS ---
st.header("Dados do Ambiente")
metodo = st.radio("Escolha o método de entrada:", 
                  ["TBS e UR%", "TBS e Bulbo Úmido (TBU)", "TBS e Ponto de Orvalho (TPO)"])

col1, col2 = st.columns(2)
with col1:
    tbs = st.number_input("Temp. Bulbo Seco (°C)", value=25.0)

with col2:
    if metodo == "TBS e UR%":
        dado2 = st.number_input("Umidade Relativa (%)", value=60.0, min_value=0.0, max_value=100.0)
    elif metodo == "TBS e Bulbo Úmido (TBU)":
        dado2 = st.number_input("Temp. Bulbo Úmido (°C)", value=20.0)
    else:
        dado2 = st.number_input("Temp. Ponto de Orvalho (°C)", value=15.0)

# --- PROCESSAMENTO ---
if st.button("CALCULAR PROPRIEDADES"):
    try:
        if metodo == "TBS e UR%":
            phi = dado2 / 100.0
            pws = calcular_pws(tbs)
            pw = phi * pws
            w = 0.62198 * pw / (p_atm - pw) # [cite: 62-64]
            tdp = calcular_tdp_regressao(pw)
            # Cálculo da TBU (t*) via Secante
            tbu = encontrar_tbu_secante(tbs, w, p_atm, tdp)
            
        elif metodo == "TBS e Bulbo Úmido (TBU)":
            tbu = dado2
            w = calcular_w_equacao_16(tbs, tbu, p_atm) # 
            pw = (p_atm * w) / (0.62198 + w) # [cite: 66]
            phi = (pw / calcular_pws(tbs)) * 100
            tdp = calcular_tdp_regressao(pw)
            
        else: # TPO
            tdp = dado2
            pw = calcular_pws(tdp)
            phi = (pw / calcular_pws(tbs)) * 100
            w = 0.62198 * pw / (p_atm - pw)
            # Cálculo da TBU (t*) via Secante
            tbu = encontrar_tbu_secante(tbs, w, p_atm, tdp)

        # Propriedades finais
        h = 1.006 * tbs + w * (2501 + 1.775 * tbs) # [cite: 118-119]
        v = 0.28705 * (tbs + 273.15) * (1 + 1.6078 * w) / p_atm # [cite: 84-87]
        itu = (tbs + 273.15) + 0.36 * (tdp + 273.15) - 330.08 # Fórmula do Usuário (em Kelvin)

        # Lógica de Classificação
        if especie == "Bovino Leiteiro":
            status = "Conforto" if itu < 72 else "Alerta" if itu < 79 else "Grave"
        else: # Aves e Suínos
            status = "Conforto" if itu < 74 else "Alerta" if itu < 79 else "Perigo"

        # --- EXIBIÇÃO ---
        st.success(f"### ITU: {itu:.2f} — {status}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("TBU (°C)", f"{tbu:.2f}")
        c2.metric("UR (%)", f"{phi if metodo != 'TBS e UR%' else dado2:.1f}%")
        c3.metric("Entalpia (h)", f"{h:.2f} kJ/kg")
        c4.metric("Ponto Orvalho", f"{tdp:.2f} °C")
        
        st.info(f"**Volume Específico:** {v:.4f} m³/kg | **Razão de Mistura:** {w:.5f} kg/kg | **Pressão:** {p_atm:.2f} kPa")

    except Exception as e:
        st.error(f"Erro no cálculo: {e}. Verifique se os dados são fisicamente possíveis.")
