import streamlit as st
import math

# --- FUNÇÕES MATEMÁTICAS (WILHELM, 1976) ---

def calcular_pws(t_c):
    """Pressão de saturação em kPa [cite: 35, 45-55]."""
    T = t_c + 273.15
    if t_c < 0:
        return math.exp(24.2779 - (6238.64 / T) - 0.344438 * math.log(T)) # [1a] [cite: 38-42]
    return math.exp((-7511.52 / T) + 89.63121 + (0.023998970 * T) - 
                    (1.1654551e-5 * (T**2)) - (1.2810336e-8 * (T**3)) + 
                    (2.0998405e-11 * (T**4)) - (12.150799 * math.log(T))) # [1b] [cite: 46-55]

def calcular_tdp_regressao(pw):
    """Ponto de orvalho via regressão [cite: 126-136]."""
    a = math.log(pw)
    if pw <= 0.611: return 5.994 + 12.41 * a + 0.4273 * (a**2) # [11a]
    elif pw <= 12.33: return 6.983 + 14.38 * a + 1.079 * (a**2) # [11b]
    return 13.80 + 9.478 * a + 1.991 * (a**2) # [11c]

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Ambiência Wilhelm", page_icon="🌡️")
st.title("📊 Calculadora de Ambiência Animal")
st.markdown(f"**Baseado em:** Wilhelm (1976) | **Autor:** Seu Nome")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.header("Configurações Locais")
altitude = st.sidebar.number_input("Altitude (m)", value=918, help="Ex: Lavras ~ 918m")
p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
st.sidebar.write(f"Pressão estimada: **{p_atm:.2f} kPa**")

especie = st.sidebar.selectbox("Espécie Animal", ["Bovinos", "Aves", "Suínos"])

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
        elif metodo == "TBS e Bulbo Úmido (TBU)":
            pws_star = calcular_pws(dado2)
            ws_star = 0.62198 * pws_star / (p_atm - pws_star)
            w = ((2501 - 2.411 * dado2) * ws_star - 1.006 * (tbs - dado2)) / (2501 + 1.775 * tbs - 4.186 * dado2) # [cite: 142-144]
            pw = (p_atm * w) / (0.62198 + w)
            phi = (pw / calcular_pws(tbs)) * 100
            tdp = calcular_tdp_regressao(pw)
        else:
            tdp = dado2
            pw = calcular_pws(tdp)
            phi = (pw / calcular_pws(tbs)) * 100
            w = 0.62198 * pw / (p_atm - pw)

        h = 1.006 * tbs + w * (2501 + 1.775 * tbs) # [cite: 118-119]
        v = 0.28705 * (tbs + 273.15) * (1 + 1.6078 * w) / p_atm # [cite: 84-87]
        itu = (tbs + 273.15) + 0.36 * (tdp + 273.15) - 330.08 # Fórmula do Usuário

        # Lógica de Classificação
        if especie == "Bovinos":
            status = "Conforto" if itu < 72 else "Alerta" if itu < 79 else "Grave"
        else: # Aves e Suínos
            status = "Conforto" if itu < 74 else "Alerta" if itu < 79 else "Perigo"

        # --- EXIBIÇÃO ---
        st.success(f"### ITU: {itu:.2f} — {status}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("UR (%)", f"{phi if metodo != 'TBS e UR%' else dado2:.1f}%")
        c2.metric("Entalpia (h)", f"{h:.2f} kJ/kg")
        c3.metric("Ponto Orvalho", f"{tdp:.2f} °C")
        
        st.info(f"**Volume Específico:** {v:.4f} m³/kg | **Razão de Mistura:** {w:.5f} kg/kg")

    except Exception as e:
        st.error("Erro no cálculo. Verifique se os dados são fisicamente possíveis.")