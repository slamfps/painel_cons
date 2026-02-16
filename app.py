import streamlit as st

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Performance PRO",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONALIZADO
# ============================================================================
st.markdown("""
<style>
    /* Cores principais */
    :root {
        --primary-color: #1E3A8A;
        --secondary-color: #3B82F6;
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --danger-color: #EF4444;
        --light-bg: #F8FAFC;
        --dark-text: #1E293B;
    }
    
    /* Estilo geral */
    .main {
        background-color: #ffffff;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: var(--primary-color) !important;
        font-weight: 600 !important;
    }
    
    /* Badges de variação */
    .variation-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin-top: 5px;
        text-align: center;
    }
    
    .variation-positive {
        background-color: #10B981;
        color: white;
    }
    
    .variation-negative {
        background-color: #EF4444;
        color: white;
    }
    
    .variation-neutral {
        background-color: #6B7280;
        color: white;
    }
    
    /* Cards de período */
    .period-card {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #3B82F6;
        margin-bottom: 10px;
    }
    
    /* Botões */
    .stButton > button {
        background-color: var(--secondary-color);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Separadores */
    .separator {
        height: 1px;
        background: linear-gradient(to right, transparent, var(--secondary-color), transparent);
        margin: 25px 0;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-color: var(--secondary-color) !important;
    }
    
    /* Cards com gradiente */
    .card-vendas {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .card-qualidade {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%) !important;
    }
    
    .card-produtividade {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    }
    
    .card-default {
        background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - MENU PRINCIPAL
# ============================================================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>📊</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Performance PRO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Menu de navegação
    st.markdown("### 📍 Navegação")
    st.markdown("""
    - **[👤 Visão Individual](/1_👤_Visao_Individual)**
    - **[📅 Comparar Períodos](/2_📅_Comparar_Periodos)**
    - **[🏢 Dashboard da Equipe](/3_🏢_Dashboard_Equipe)**
    """)
    
    st.markdown("---")
    
    # Inicializar sistema de metas (importando do módulo)
    from src.metas import inicializar_sistema_metas
    inicializar_sistema_metas()
    
    # Controle de exibição de metas
    st.markdown("### ⚙️ Configurações")
    mostrar_metas = st.checkbox(
        "Mostrar metas nos cards",
        value=st.session_state.mostrar_metas,
        help="Exibe/oculta o sistema de metas nos cards de indicadores"
    )
    st.session_state.mostrar_metas = mostrar_metas
    
    # Gerenciar metas salvas
    from src.metas import obter_meta, formatar_valor
    with st.expander("📋 Gerenciar Metas Salvas"):
        if st.session_state.metas:
            for chave, meta in st.session_state.metas.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{meta['indicador'][:25]}**")
                    st.caption(f"Valor: {formatar_valor(meta['valor'])} • {meta['consultor']}")
                with col2:
                    if st.button("🗑️", key=f"del_{chave}"):
                        del st.session_state.metas[chave]
                        st.rerun()
        else:
            st.info("Nenhuma meta salva ainda.")
    
    st.markdown("---")
    
    # Informações do sistema
    from datetime import datetime
    st.markdown("### ℹ️ Sobre")
    st.markdown(f"""
    **Versão:** 2.1  
    **Última atualização:** {datetime.now().strftime("%d/%m/%Y")}  
    
    *Sistema de metas implementado*
    """)
    
    st.markdown("---")
    
    # Dicas rápidas
    with st.expander("💡 Dicas Rápidas"):
        st.markdown("""
        1. **Variação em %**: Agora mostra desempenho relativo
        2. **Cores automáticas**: Verde (+5%), Vermelho (-5%), Cinza (±5%)
        3. **Sistema de Metas**: Clique em "+ Meta" para definir objetivos
        4. **Progresso visual**: Barras coloridas mostram % da meta
        5. **Filtre indicadores**: Compare apenas o que importa
        6. **Exportação**: Dados filtrados e formatados
        """)

# ============================================================================
# PÁGINA INICIAL (quando acessar app.py diretamente)
# ============================================================================
st.title("📊 Performance PRO v2.1")
st.markdown("---")
st.markdown("### Bem-vindo ao Sistema de Gestão de Performance")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 👤 Visão Individual")
    st.markdown("""
    - Análise por consultor
    - Sistema de metas
    - Indicadores personalizados
    - Exportação para Excel
    """)

with col2:
    st.markdown("#### 📅 Comparar Períodos")
    st.markdown("""
    - Variação percentual
    - Cores automáticas
    - Gráficos interativos
    - Comparação entre consultores
    """)

with col3:
    st.markdown("#### 🏢 Dashboard da Equipe")
    st.markdown("""
    - Visão geral da equipe
    - Ranking de performance
    - Médias e tendências
    - *Em breve...*
    """)

st.markdown("---")
st.info("💡 **Use o menu à esquerda para navegar entre as análises.**")