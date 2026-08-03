import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Cálculo de Vigas NBR 6118", page_icon="🏗️", layout="wide")

st.title("🏗️ Cálculo Rápido de Vigas (NBR 6118)")
st.markdown("Aplicativo interativo para pré-dimensionamento e detalhamento de vigas de concreto armado.")

def dimensionar_viga(bw, h, L, q_extra, fck, cobrimento, phi_long_mm):
    # Parâmetros Iniciais
    fyk = 500.0   
    fywk = 500.0  
    gamma_c = 1.4
    gamma_s = 1.15
    gamma_f = 1.4
    
    fcd = (fck / gamma_c) / 10.0      
    fyd = (fyk / gamma_s) / 10.0      
    fywd = (fywk / gamma_s) / 10.0    
    d = h - cobrimento - 0.5 - (phi_long_mm / 10.0 / 2.0) 

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
        st.warning("⚠ **ATENÇÃO:** A seção atingiu o limite de dutilidade (x/d > 0.45). Recomenda-se aumentar a seção de concreto (altura ou largura) ou prever armadura dupla.")

    xi = (1.0 - math.sqrt(max(0, 1.0 - 2.0 * mu))) / 0.8
    z = d * (1.0 - 0.4 * xi) 
    As_calc = Md_kNcm / (z * fyd) 

    fctm = 0.3 * (fck ** (2.0 / 3.0)) 
    rho_min = max(0.0015, 0.078 * (fck ** (2.0 / 3.0)) / fyk)
    As_min = rho_min * bw * h
    As_adotada = max(As_calc, As_min)

    # Cálculo da quantidade de barras baseada na ESCOLHA do usuário
    area_bar = (math.pi * ((phi_long_mm / 10.0) ** 2)) / 4.0
    n_barras = max(2, math.ceil(As_adotada / area_bar))
    As_efetiva = n_barras * area_bar
    escolha_long = (n_barras, phi_long_mm, As_efetiva)

    # Verificação de espaçamento horizontal livre mínimo
    largura_util = bw - (2 * cobrimento) - (2 * 0.5) # Considerando estribo inicial de 5mm
    espacamento_livre = (largura_util - n_barras * (phi_long_mm / 10.0)) / (n_barras - 1) if n_barras > 1 else 999
    espacamento_minimo_norma = max(2.0, phi_long_mm / 10.0, 1.2 * 1.9) # 1.9cm é um brita 1 padrão
    
    aviso_espacamento = False
    if espacamento_livre < espacamento_minimo_norma:
        aviso_espacamento = True
        st.error(f"❌ **ESPAÇAMENTO INSUFICIENTE:** A bitola de {phi_long_mm}mm exige {n_barras} barras. Elas não cabem lado a lado numa única camada (espaçamento de {espacamento_livre:.1f}cm < mínimo de {espacamento_minimo_norma:.1f}cm). Escolha uma bitola **MAIOR** ou aumente a largura da viga.")

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
        escolha_transv = (8.0, max(5, math.floor(min(passo, s_max)))) # Força estribo maior se precisar

    # ==================== DESENHOS (MATPLOTLIB) ====================
    # Gráfico 1: Seção Transversal
    fig1, ax1 = plt.subplots(figsize=(5, 6))
    concreto = patches.Rectangle((0, 0), bw, h, linewidth=2, edgecolor='#333333', facecolor='#e6e6e6')
    ax1.add_patch(concreto)

    phi_e_cm = escolha_transv[0] / 10.0
    estribo = patches.Rectangle(
        (cobrimento, cobrimento), bw - 2 * cobrimento, h - 2 * cobrimento, 
        linewidth=2, edgecolor='red', facecolor='none', linestyle='--'
    )
    ax1.add_patch(estribo)

    n_long, phi_l_mm, _ = escolha_long
    r_l = (phi_l_mm / 10.0) / 2.0
    y_inf = cobrimento + phi_e_cm + r_l
    x_min = cobrimento + phi_e_cm + r_l
    x_max = bw - (cobrimento + phi_e_cm + r_l)
    
    # Se espacamento der negativo, desenha apertado mesmo assim para mostrar o erro visualmente
    x_coords = [x_min + i * ((x_max - x_min) / (n_long - 1)) for i in range(n_long)] if n_long > 1 else [(x_min + x_max) / 2]

    for x in x_coords:
        barra = patches.Circle((x, y_inf), r_l, color='blue')
        ax1.add_patch(barra)

    r_top = 0.8 / 2.0
    y_sup = h - (cobrimento + phi_e_cm + r_top)
    ax1.add_patch(patches.Circle((x_min, y_sup), r_top, color='black'))
    ax1.add_patch(patches.Circle((x_max, y_sup), r_top, color='black'))

    ax1.set_aspect('equal')
    margin = 4
    ax1.set_xlim(-margin, bw + margin)
    ax1.set_ylim(-margin, h + margin)
    ax1.set_title(f"Seção Transversal ({bw}x{h} cm)", fontsize=10, fontweight='bold')
    ax1.set_xlabel("Largura (cm)")
    ax1.set_ylabel("Altura (cm)")
    ax1.grid(True, linestyle=':', alpha=0.5)

    # Gráfico 2: Vista Longitudinal
    fig2, ax2 = plt.subplots(figsize=(10, 3))
    L_cm = L * 100
    viga_long = patches.Rectangle((0, 0), L_cm, h, linewidth=2, edgecolor='#333333', facecolor='#e6e6e6')
    ax2.add_patch(viga_long)
    
    # Desenho dos estribos na vista longitudinal
    passo_cm = escolha_transv[1]
    x_estribo = cobrimento
    while x_estribo < (L_cm - cobrimento):
        linha_estribo = plt.Line2D([x_estribo, x_estribo], [cobrimento, h - cobrimento], color='red', linewidth=1.5, alpha=0.7)
        ax2.add_line(linha_estribo)
        x_estribo += passo_cm

    # Desenho da armadura longitudinal (linhas azuis)
    linha_inferior = plt.Line2D([cobrimento, L_cm - cobrimento], [y_inf, y_inf], color='blue', linewidth=3)
    linha_superior = plt.Line2D([cobrimento, L_cm - cobrimento], [y_sup, y_sup], color='black', linewidth=1.5)
    ax2.add_line(linha_inferior)
    ax2.add_line(linha_superior)

    # Pilares de apoio (representação)
    apoio_esq = patches.Polygon([(-10, -15), (10, -15), (0, 0)], closed=True, color='gray')
    apoio_dir = patches.Polygon([(L_cm-10, -15), (L_cm+10, -15), (L_cm, 0)], closed=True, color='gray')
    ax2.add_patch(apoio_esq)
    ax2.add_patch(apoio_dir)

    ax2.set_aspect('equal')
    ax2.set_xlim(-20, L_cm + 20)
    ax2.set_ylim(-20, h + 10)
    ax2.set_title(f"Vista Longitudinal - Vão de {L}m", fontsize=10, fontweight='bold')
    ax2.set_xlabel("Comprimento (cm)")
    ax2.set_ylabel("Altura (cm)")
    ax2.grid(True, linestyle=':', alpha=0.5)

    return g_proprio, q_total, Mk, Vd, As_adotada, escolha_long, Asw_s_final, escolha_transv, fig1, fig2, aviso_espacamento


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
    cobrimento = st.number_input("Cobrimento Nominal (cm)", min_value=2.0, max_value=5.0, value=3.0, step=0.5)
    
    st.markdown("---")
    st.header("Escolha das Armaduras")
    # NOVO: Dropdown para escolher a bitola longitudinal
    phi_long_mm = st.selectbox(
        "Bitola Longitudinal (Tração)", 
        options=[8.0, 10.0, 12.5, 16.0, 20.0, 25.0], 
        index=2, # index 2 corresponde a 12.5mm por padrão
        format_func=lambda x: f"ø {x} mm"
    )
    
    st.markdown("---")
    calcular = st.button("Calcular e Gerar Detalhamento", type="primary", use_container_width=True)

if calcular:
    g_proprio, q_total, Mk, Vd, As_adotada, e_long, Asw_final, e_transv, fig1, fig2, aviso_espacamento = dimensionar_viga(
        bw, h, L, q_extra, fck, cobrimento, phi_long_mm
    )
    
    # Exibição dos Resultados
    st.subheader("📊 Resumo de Esforços")
    colA, colB, colC, colD = st.columns(4)
    colA.metric("Peso Próprio", f"{g_proprio:.2f} kN/m")
    colB.metric("Carga Total", f"{q_total:.2f} kN/m")
    colC.metric("Momento Máx (Mk)", f"{Mk:.2f} kN.m")
    colD.metric("Cortante (Vd)", f"{Vd:.2f} kN")
    
    st.markdown("---")
    
    col_text, col_img = st.columns([1, 1.2])
    
    with col_text:
        st.subheader("🔩 Armaduras Detalhadas")
        st.write(f"**Área de Aço Long. Calculada (As):** {As_adotada:.2f} cm²")
        if aviso_espacamento:
            st.warning(f"**Armadura Adotada:** {e_long[0]} barras de ø{e_long[1]} mm (As,ef = {e_long[2]:.2f} cm²)")
        else:
            st.success(f"**Armadura Adotada:** {e_long[0]} barras de ø{e_long[1]} mm (As,ef = {e_long[2]:.2f} cm²)")
                   
        st.write(f"**Área de Aço Transversal (Asw/s):** {Asw_final:.2f} cm²/m")
        st.info(f"**Estribos Adotados:** ø{e_transv[0]} mm a cada {e_transv[1]} cm")
                
    with col_img:
        tab1, tab2 = st.tabs(["Seção Transversal", "Vista Longitudinal"])
        with tab1:
            st.pyplot(fig1)
        with tab2:
            st.pyplot(fig2)
else:
    st.info("👈 Preencha os dados e escolha a bitola na barra lateral, depois clique em **Calcular e Gerar Detalhamento**.")
