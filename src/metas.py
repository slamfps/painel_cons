import streamlit as st
from datetime import datetime
from .utils import formatar_valor
import pandas as pd
import hashlib

# ============================================================================
# FUNÇÕES DO SISTEMA DE METAS
# ============================================================================

def inicializar_sistema_metas():
    """Inicializa o sistema de metas no session_state"""
    if 'metas' not in st.session_state:
        st.session_state.metas = {}
    if 'mostrar_metas' not in st.session_state:
        st.session_state.mostrar_metas = True
    if 'modal_aberto' in st.session_state:
        del st.session_state.modal_aberto

def criar_chave_meta(indicador, consultor, equipe=None):
    """Cria uma chave única para armazenar metas"""
    if equipe:
        return f"meta_{indicador}_{consultor}_{equipe}".replace(" ", "_").upper()
    else:
        return f"meta_{indicador}_{consultor}".replace(" ", "_").upper()

def salvar_meta(indicador, meta_valor, consultor, equipe=None):
    """Salva uma meta no session_state"""
    chave = criar_chave_meta(indicador, consultor, equipe)
    
    try:
        valor_numerico = float(str(meta_valor).replace(',', '.'))
    except:
        st.error("❌ Valor da meta deve ser numérico")
        return False
    
    st.session_state.metas[chave] = {
        'valor': valor_numerico,
        'indicador': indicador,
        'consultor': consultor,
        'equipe': equipe,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return True

def remover_meta(indicador, consultor, equipe=None):
    """Remove uma meta do session_state"""
    chave = criar_chave_meta(indicador, consultor, equipe)
    if chave in st.session_state.metas:
        del st.session_state.metas[chave]
        return True
    return False

def obter_meta(indicador, consultor, equipe=None):
    """Recupera uma meta do session_state"""
    chave = criar_chave_meta(indicador, consultor, equipe)
    return st.session_state.metas.get(chave)

def calcular_progresso_meta(valor_atual, meta_valor):
    """Calcula o progresso em relação à meta (0-150%)"""
    if meta_valor is None or meta_valor == 0:
        return 0
    
    try:
        valor_numerico = float(str(valor_atual).replace(',', '.').replace('%', ''))
        meta_numerica = float(meta_valor)
        
        if meta_numerica == 0:
            return 100.0
        
        progresso = (valor_numerico / meta_numerica) * 100
        return min(progresso, 150)
    except:
        return 0

def obter_cor_progresso(progresso):
    """Retorna cor baseada no progresso da meta"""
    if progresso >= 100:
        return "#10B981"
    elif progresso >= 80:
        return "#F59E0B"
    else:
        return "#EF4444"

def formatar_progresso_texto(progresso):
    """Formata texto do progresso"""
    if progresso >= 100:
        return f"✓ {progresso:.0f}%"
    elif progresso > 0:
        return f"{progresso:.0f}%"
    else:
        return "0%"

def obter_gradiente_por_tipo(indicador):
    """Retorna gradiente CSS baseado no tipo de indicador"""
    indicador_upper = indicador.upper()
    
    if any(term in indicador_upper for term in ['VENDAS', 'VENDA', 'VDS']):
        return "linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)"
    elif any(term in indicador_upper for term in ['PONTOS', 'PTS', 'SCORE']):
        return "linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)"
    elif any(term in indicador_upper for term in ['CHIP', 'SIM', 'CARD']):
        return "linear-gradient(135deg, #059669 0%, #10B981 100%)"
    elif any(term in indicador_upper for term in ['QUALIDADE', 'QUALITY', 'CALLBACK']):
        return "linear-gradient(135deg, #EC4899 0%, #F472B6 100%)"
    elif any(term in indicador_upper for term in ['ATENDIMENTO', 'ATD', 'SERVICE']):
        return "linear-gradient(135deg, #D97706 0%, #F59E0B 100%)"
    elif any(term in indicador_upper for term in ['CVS', 'CALLBACK']):
        return "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)"
    else:
        return "linear-gradient(135deg, #6B7280 0%, #9CA3AF 100%)"

# ============================================================================
# FUNÇÃO PRINCIPAL DO CARD - VERSÃO 6.2 (CORRIGIDA E OTIMIZADA)
# ============================================================================

def criar_card_indicador(valor, indicador, consultor, equipe=None):
    """
    Cria um card de indicador compacto com metas integradas
    CORREÇÃO: Removeu columns aninhados e melhorou contraste do 100%
    """
    # Formata valor
    valor_formatado = formatar_valor(valor)
    gradiente = obter_gradiente_por_tipo(indicador)
    
    # Verifica meta existente
    meta = None
    progresso = 0
    cor_progresso = ""
    texto_progresso = ""
    meta_valor_formatado = ""
    
    if st.session_state.mostrar_metas:
        meta = obter_meta(indicador, consultor, equipe)
        if meta:
            progresso = calcular_progresso_meta(valor, meta['valor'])
            cor_progresso = obter_cor_progresso(progresso)
            texto_progresso = formatar_progresso_texto(progresso)
            meta_valor_formatado = formatar_valor(meta['valor'])
    
    # ========== CHAVE ESTÁVEL ==========
    chave_base = f"{indicador}_{consultor}_{equipe if equipe else 'sem_equipe'}"
    hash_id = hashlib.md5(chave_base.encode()).hexdigest()[:8]
    
    # ========== METAS PREDEFINIDAS ==========
    METAS_CHIP = {
        "🥉 Prata": {"chip": 23, "hab": 351, "fin": 491},
        "🥈 Ouro": {"chip": 29, "hab": 491, "fin": 614},
        "📊 Step 1": {"chip": 39, "hab": 585, "fin": 724},
        "🏆 Step 2": {"chip": 44, "hab": 685, "fin": 851}
    }
    
    # ========== CARD PRINCIPAL (SEM COLUMNS ANINHADOS) ==========
    # CABEÇALHO
    st.markdown(f"""
    <div style='
        background: {gradiente};
        padding: 10px 14px;
        color: white;
        border-radius: 8px 8px 0 0;
        margin: 0;
    '>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 12px; font-weight: 600;">
                {indicador[:18]}{'...' if len(indicador) > 18 else ''}
            </span>
            <span style="font-size: 9px; background: rgba(255,255,255,0.2); 
                        padding: 2px 6px; border-radius: 10px;">
                {valor_formatado}
            </span>
        </div>
        <div style="margin: 4px 0 0 0; font-size: 22px; font-weight: 700;">
            {valor_formatado}
        </div>
    """, unsafe_allow_html=True)
    
    # BARRA DE PROGRESSO
    if meta:
        # Define o estilo do texto do progresso baseado no percentual
        if progresso >= 100:
            estilo_progresso = 'background: #059669; color: white; font-weight: 700; padding: 2px 8px; border-radius: 12px;'
        else:
            estilo_progresso = f'font-weight: 600; color: {cor_progresso};'
        
        st.markdown(f"""
        <div style='
            background: {gradiente};
            padding: 0 14px 10px 14px;
            color: white;
            margin: 0;
        '>
            <div style="display: flex; justify-content: space-between; font-size: 10px; margin-bottom: 2px;">
                <span>Meta: {meta_valor_formatado}</span>
                <span style="{estilo_progresso}">{texto_progresso}</span>
            </div>
            <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.3); border-radius: 2px;">
                <div style="width: {min(progresso, 100)}%; height: 100%; 
                            background: {cor_progresso}; border-radius: 2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("</div>", unsafe_allow_html=True)
    
    # CORPO DO CARD
    if meta:
        st.markdown(f"""
        <div style='
            background: #F9FAFB;
            padding: 10px;
            color: #111827;
            border-radius: 0 0 8px 8px;
            border: 1px solid #E5E7EB;
            border-top: none;
        '>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #6B7280;">🎯 Meta</span>
                <span style="font-size: 13px; font-weight: 700; color: #059669;">
                    {meta_valor_formatado}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='
            background: #F9FAFB;
            padding: 10px;
            border-radius: 0 0 8px 8px;
            border: 1px dashed #9CA3AF;
            border-top: none;
            text-align: center;
        '>
            <span style="font-size: 11px; color: #6B7280;">
                ⚡ Sem meta
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # ========== POPOVER (AGORA SEM COLUMNS ANINHADOS) ==========
    texto_botao = "✏️" if meta else "🎯"
    
    with st.popover(texto_botao, use_container_width=True):
        st.markdown(f"**{indicador[:30]}**")
        st.metric("Atual", valor_formatado, delta=None)
        
        # ----- CHIP HABILITADO -----
        if "CHIP" in indicador.upper() and "HABILITADO" in indicador.upper():
            meta_atual = meta['valor'] if meta else None
            
            st.markdown("**Níveis:**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if meta_atual == 23:
                    st.success("🥉")
                    if st.button("Remover", key=f"rm_p_{hash_id}", use_container_width=True):
                        remover_meta(indicador, consultor, equipe)
                        remover_meta('PONTOS HAB TOTAL', consultor, equipe)
                        remover_meta('PONTOS FIN TOTAL', consultor, equipe)
                        st.rerun()
                else:
                    if st.button("🥉", key=f"p_{hash_id}", use_container_width=True):
                        metas = METAS_CHIP["🥉 Prata"]
                        salvar_meta(indicador, metas["chip"], consultor, equipe)
                        if 'PONTOS HAB TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS HAB TOTAL', metas["hab"], consultor, equipe)
                        if 'PONTOS FIN TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS FIN TOTAL', metas["fin"], consultor, equipe)
                        st.rerun()
            
            with col2:
                if meta_atual == 29:
                    st.success("🥈")
                    if st.button("Remover", key=f"rm_o_{hash_id}", use_container_width=True):
                        remover_meta(indicador, consultor, equipe)
                        remover_meta('PONTOS HAB TOTAL', consultor, equipe)
                        remover_meta('PONTOS FIN TOTAL', consultor, equipe)
                        st.rerun()
                else:
                    if st.button("🥈", key=f"o_{hash_id}", use_container_width=True):
                        metas = METAS_CHIP["🥈 Ouro"]
                        salvar_meta(indicador, metas["chip"], consultor, equipe)
                        if 'PONTOS HAB TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS HAB TOTAL', metas["hab"], consultor, equipe)
                        if 'PONTOS FIN TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS FIN TOTAL', metas["fin"], consultor, equipe)
                        st.rerun()
            
            with col3:
                if meta_atual == 39:
                    st.success("📊")
                    if st.button("Remover", key=f"rm_s1_{hash_id}", use_container_width=True):
                        remover_meta(indicador, consultor, equipe)
                        remover_meta('PONTOS HAB TOTAL', consultor, equipe)
                        remover_meta('PONTOS FIN TOTAL', consultor, equipe)
                        st.rerun()
                else:
                    if st.button("📊1", key=f"s1_{hash_id}", use_container_width=True):
                        metas = METAS_CHIP["📊 Step 1"]
                        salvar_meta(indicador, metas["chip"], consultor, equipe)
                        if 'PONTOS HAB TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS HAB TOTAL', metas["hab"], consultor, equipe)
                        if 'PONTOS FIN TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS FIN TOTAL', metas["fin"], consultor, equipe)
                        st.rerun()
            
            with col4:
                if meta_atual == 44:
                    st.success("🏆")
                    if st.button("Remover", key=f"rm_s2_{hash_id}", use_container_width=True):
                        remover_meta(indicador, consultor, equipe)
                        remover_meta('PONTOS HAB TOTAL', consultor, equipe)
                        remover_meta('PONTOS FIN TOTAL', consultor, equipe)
                        st.rerun()
                else:
                    if st.button("🏆2", key=f"s2_{hash_id}", use_container_width=True):
                        metas = METAS_CHIP["🏆 Step 2"]
                        salvar_meta(indicador, metas["chip"], consultor, equipe)
                        if 'PONTOS HAB TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS HAB TOTAL', metas["hab"], consultor, equipe)
                        if 'PONTOS FIN TOTAL' in st.session_state.get('todos_indicadores', []):
                            salvar_meta('PONTOS FIN TOTAL', metas["fin"], consultor, equipe)
                        st.rerun()
        
        # ----- CVS -----
        elif "CVS" in indicador.upper() and "CALLBACK" in indicador.upper():
            if meta:
                valor_sugerido = float(meta['valor'])
            else:
                try:
                    valor_sugerido = float(str(valor).replace(',', '.').replace('%', '')) * 1.1
                except:
                    valor_sugerido = 0.0
            
            nova_meta = st.number_input(
                "Meta:",
                value=float(valor_sugerido) if valor_sugerido > 0 else 0.0,
                min_value=0.0,
                step=1.0,
                format="%.1f",
                key=f"cvs_{hash_id}",
                label_visibility="collapsed",
                placeholder="Valor da meta"
            )
            
            col_s, col_r = st.columns(2)
            with col_s:
                if st.button("💾", key=f"save_cvs_{hash_id}", use_container_width=True):
                    if salvar_meta(indicador, nova_meta, consultor, equipe):
                        st.rerun()
            with col_r:
                if meta:
                    if st.button("🗑️", key=f"rm_cvs_{hash_id}", use_container_width=True):
                        if remover_meta(indicador, consultor, equipe):
                            st.rerun()
        
        # ----- OUTROS -----
        else:
            if "PONTOS" in indicador.upper():
                st.caption("Controlado pelo CHIP")
            else:
                st.caption("Meta apenas para CHIP/CVS")
    
    return meta

# ============================================================================
# FUNÇÕES AUXILIARES PARA GRÁFICOS
# ============================================================================

def obter_cor_progresso_grafico(progresso):
    """Cores otimizadas para gráficos"""
    if progresso >= 100: return '#059669'
    elif progresso >= 80: return '#10B981'
    elif progresso >= 50: return '#D97706'
    elif progresso >= 30: return '#F59E0B'
    else: return '#DC2626'

def formatar_valor_grafico(valor):
    """Formata valores para gráficos"""
    try:
        if pd.isna(valor): return "0"
        valor_str = str(valor).replace('%', '').replace(',', '.').strip()
        num_valor = float(valor_str)
        if num_valor >= 1000000: return f"{num_valor/1000000:.1f}M"
        elif num_valor >= 1000: return f"{num_valor/1000:.0f}K"
        elif num_valor.is_integer(): return f"{int(num_valor):,}".replace(",", ".")
        else: return f"{num_valor:.1f}"
    except:
        return str(valor)

def criar_nome_curto_grafico(indicador):
    """Cria versão abreviada para gráficos"""
    mapeamento = {
        'PONTOS': 'PTS', 'HABILITADO': 'HAB', 'FINALIZADO': 'FIN',
        'TOTAL': 'TOT', 'VENDAS': 'VDS', 'CHIP': 'CHP',
        'CALLBACK': 'CB', 'CVS': 'CV', 'FIN': 'FN',
        'TELEVISAO': 'TV', 'TELEVISÃO': 'TV', 'PRODUTO': 'PDT'
    }
    
    resultado = indicador.upper()
    for palavra, abrev in mapeamento.items():
        resultado = resultado.replace(palavra, abrev)
    
    resultado = ' '.join(resultado.split())
    if len(resultado) > 20:
        partes = resultado.split()
        if len(partes) > 2:
            resultado = ' '.join(partes[:2]) + '...'
        else:
            resultado = resultado[:18] + "..."
    
    return resultado