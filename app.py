import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Cálculo de Vigas NBR 6118", page_icon="🏗️", layout="wide")

st.title("🏗️ Cálculo Rápido de Vigas (NBR 6118)")
st.markdown("Aplicativo para pré-dimensionamento de armaduras longitudinais e transversais de vigas retangulares.")

def dimensionar_viga(bw, h, L, q_extra, fck):
    # Parâmetros Iniciais
    fyk = 500.0   
    fywk = 500.0  
    gamma_c = 1.4
    gamma_s = 1.15
    gamma_f = 1.4
    cobrimento = 3.0 
    
    fcd = (fck / gamma_c) / 10.0      
    fyd = (fyk / gamma_s) / 10.0      
    fywd = (fywk / gamma_s) / 10.0    
    d = h - cobrimento - 0.5 - (1.25 / 2.0) 

    # Esforços
    g_proprio = (bw / 100.0) * (h / 100.0) * 25.0 
    q_total = g_proprio + q_extra 
    Mk = (q_total * (L ** 2)) / 8.0 
    Md_kNcm = gamma_f * Mk * 100.0              
    Vk = (q_total * L) / 2.0        
    Vd = gamma_f * Vk                 

    # ==================== ARMADURA LONGITUDINAL ====================
    mu = Md_kNcm / (bw * (d ** 2) * 0.85 * fcd)
    
    if mu > 0.295:
        st.warning("⚠ **ATENÇÃO:** A seção atingiu o limite de dutilidade (x/d > 0.45). Recomenda-se aumentar a seção de concreto ou prever armadura dupla.")

    xi = (1.0 - math.sqrt(max(0, 1.0 - 2.0 * mu))) / 0.8
    z = d * (1.0 - 0.4 * xi) 
    As_calc = Md_kNcm / (z * fyd) 

    fctm = 0.3 * (fck ** (2.0 / 3.0)) 
    rho_min = max(0.0015, 0.078 * (fck ** (2.0 / 3.0)) / fyk)
    As_min = rho_min * bw * h
    As_adotada = max(As_calc, As_min)

    bitolas_posso = [10.0, 12.5, 16.0, 20.0] 
    escolha_long = None

    for phi in bitolas_posso:
        area_bar = (math.pi * ((phi / 10.0) ** 2)) / 4.0
        n_barras = max(2, math.ceil(As_adotada / area_bar))
        largura_util = bw - (2 * cobrimento) - (2 * 0.5)
        espacamento = (largura_util - n_barras * (phi / 10.0)) / (n_barras - 1) if n_barras > 1 else 999
        
        if espacamento >= max(2.0, phi / 10.0):
            escolha_long = (n_barras, phi, n_barras * area_bar)
            break

    if not escolha_long:
        phi = 16.0
        area_bar = (math.pi * ((phi / 10.0) ** 2)) / 4.0
        n_barras = max(2, math.ceil(As_adotada / area_bar))
        escolha_long = (n_barras, phi, n_barras * area_bar)

    # ==================== ARMADURA TRANSVERSAL ====================
    v1 = 1.0 - (fck / 250.0)
    VRd2 = 0.27 * v1 * fcd * bw * d 
    
    if Vd > VRd2:
        st.error("❌ **ERRO CRÍTICO:** Risco de esmagamento da biela de concreto (Vd > VRd2). Aumente a largura (bw) ou altura (h) da viga.")

    fctd = (0.7 * fctm / gamma_c) / 10.0 
    Vc0 = 0.6 * fctd * bw * d 
    Vsw = max(0.0, Vd - Vc0)
    Asw_s_cm2_cm = Vsw / (0.9 * d * fywd)
    Asw_s_cm2_m = Asw_s_cm2_cm * 100.0

    Asw_s_min_cm2_m = 0.2 * (fctm / fywk) * bw * 10.0 
    Asw_s_final = max(Asw_s_cm2_m, Asw_s_min_cm2_m)

    bitolas_estribo = [5.0, 6.3, 8.0] 
    escolha_transv = None

    for phi_e in bitolas_estribo:
        area_ramos = 2.0 * ((math.pi * ((phi_e / 10.0) ** 2)) / 4.0)
        passo = (area_ramos / Asw_s_final) * 100.0
        s_max = min(0.6 * d, 30.0) if Vd <= 0.67 * VRd2 else min(0.3 * d, 20.0)
        passo = math.floor(min(passo, s_max))
        
        if passo >= 7:
            escolha_transv = (phi_e, passo)
            break

    if not escolha_transv:
        escolha_transv = (5.0, 10)

    # ==================== DESENHO (MATPLOTLIB) ====================
    fig, ax = plt.subplots(figsize=(5, 6))
    concreto = patches.Rectangle((0, 0), bw, h, linewidth=2, edgecolor='#333333', facecolor='#e6e6e6')
    ax.add_patch(concreto)

    phi_e_cm = escolha_transv[0] / 10.0
    estribo = patches.Rectangle(
        (cobrimento, cobrimento), bw - 2 * cobrimento, h - 2 * cobrimento, 
        linewidth=2, edgecolor='red', facecolor='none', linestyle='--'
    )
    ax.add_patch(estribo)

    n_long, phi_l_mm, _ = escolha_long
    r_l = (phi_l_mm / 10.0) / 2.0
    y_inf = cobrimento + phi_e_cm + r_l
    x_min = cobrimento + phi_e_cm + r_l
    x_max = bw - (cobrimento + phi_e_cm + r_l)
    x_coords = [x_min + i * ((x_max - x_min) / (n_long - 1)) for i in range(n_long)] if n_long > 1 else [(x_min + x_max) / 2]

    for x in x_coords:
        barra = patches.Circle((x, y_inf), r_l, color='blue')
        ax.add_patch(barra)

    r_top = 0.8 / 2.0
    y_sup = h - (cobrimento + phi_e_cm + r_top)
    ax.add_patch(patches.Circle((x_min, y_sup), r_top, color='black'))
    ax.add_patch(patches.Circle((x_max, y_sup), r_top, color='black'))

    ax.set_aspect('equal')
    margin = 4
    ax.set_xlim(-margin, bw + margin)
    ax.set_ylim(-margin, h + margin)
    ax.set_title(f"Seção Detalhada ({bw}x{h} cm)", fontsize=10, fontweight='bold')
    ax.set_xlabel("Largura (cm)")
    ax.set_ylabel("Altura (cm)")
    ax.grid(True, linestyle=':', alpha=0.5)

    return g_proprio, q_total, Mk, Vd, As_adotada, escolha_long, Asw_s_final, escolha_transv, fig


# ==========================================
# INTERFACE DO USUÁRIO (SIDEBAR E MAIN)
# ==========================================
with st.sidebar:
    st.header("Entrada de Dados")
    bw = st.number_input("Largura da viga (cm)", min_value=12, max_value=100, value=20, step=1)
    h = st.number_input("Altura da viga (cm)", min_value=20, max_value=200, value=50, step=5)
    L = st.number_input("Vão livre (m)", min_value=1.0, max_value=20.0, value=5.0, step=0.5)
    q_extra = st.number_input("Carga adicional (kN/m)", min_value=0.0, max_value=100.0, value=15.0, step=1.0)
    fck = st.number_input("fck do concreto (MPa)", min_value=20, max_value=90, value=25, step=5)
    
    calcular = st.button("Calcular Viga", type="primary", use_container_width=True)

if calcular:
    g_proprio, q_total, Mk, Vd, As_adotada, e_long, Asw_final, e_transv, fig = dimensionar_viga(bw, h, L, q_extra, fck)
    
    # Exibição dos Resultados em Colunas
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.subheader("📊 Esforços e Cargas")
        st.write(f"- **Peso Próprio Estimado:** {g_proprio:.2f} kN/m")
        st.write(f"- **Carga Total (Serviço):** {q_total:.2f} kN/m")
        st.write(f"- **Momento Máximo de Serviço (Mk):** {Mk:.2f} kN.m")
        st.write(f"- **Cortante de Cálculo Máximo (Vd):** {Vd:.2f} kN")
        
        st.subheader("🔩 Detalhamento das Armaduras")
        st.success(f"**Armadura Longitudinal (Tração)**\n\n"
                   f"Cálculo/Mínimo: {As_adotada:.2f} cm²\n\n"
                   f"**Adotado:** {e_long[0]} barras de ø{e_long[1]} mm (Área efetiva: {e_long[2]:.2f} cm²)")
                   
        st.info(f"**Armadura Transversal (Estribos)**\n\n"
                f"Cálculo/Mínimo: {Asw_final:.2f} cm²/m\n\n"
                f"**Adotado:** Estribos de ø{e_transv[0]} mm a cada {e_transv[1]} cm")
                
    with col2:
        st.pyplot(fig)
else:
    st.info("Insira os parâmetros na barra lateral e clique em **Calcular Viga** para gerar o dimensionamento.")
