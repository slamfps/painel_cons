# pages/2_📅_Comparar_Periodos.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.utils import (
    carregar_csv, extrair_equipe_nome, formatar_valor,
    calcular_variacao_percentual, obter_cor_variacao,
    formatar_periodo_nome
)
from src.metas import (
    inicializar_sistema_metas, obter_meta, calcular_progresso_meta,
    criar_nome_curto_grafico, obter_gradiente_por_tipo,
    obter_cor_progresso, criar_card_indicador
)

# ============================================================================
# CONFIGURAÇÃO INICIAL
# ============================================================================
st.set_page_config(page_title="Comparar Períodos", page_icon="📅", layout="wide")

# CSS MÍNIMO - APENAS PARA GRADIENTES DOS CARDS DE PERÍODO (único HTML permitido)
st.markdown("""
<style>
    .period-card-1 {
        background: linear-gradient(135deg, #0F172A, #1E293B);
        border-radius: 16px;
        padding: 20px;
        color: white;
        box-shadow: 0 8px 20px rgba(15,23,42,0.3);
    }
    .period-card-2 {
        background: linear-gradient(135deg, #1E40AF, #2563EB);
        border-radius: 16px;
        padding: 20px;
        color: white;
        box-shadow: 0 8px 20px rgba(37,99,235,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================
col_logo, col_title = st.columns([0.08, 0.92])
with col_logo:
    st.markdown("📅")
with col_title:
    st.title("Comparar Períodos")
    st.markdown("**Compare o desempenho entre dois períodos**")

# ============================================================================
# INICIALIZAR SISTEMA
# ============================================================================
inicializar_sistema_metas()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
def safe_float(valor, default=0.0):
    try:
        if pd.isna(valor) or valor is None:
            return default
        return float(valor)
    except:
        return default

def safe_formatar_valor(valor):
    try:
        resultado = formatar_valor(valor)
        return resultado if resultado else "0"
    except:
        return "0"

# ============================================================================
# UPLOAD DOS ARQUIVOS
# ============================================================================
with st.container(border=True):
    st.markdown("### 📁 Carregar arquivos")
    st.caption("Dois arquivos CSV com a mesma estrutura (coluna USUÁRIO)")
    
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("Primeiro período", type="csv", key="per1")
    with col2:
        file2 = st.file_uploader("Segundo período", type="csv", key="per2")

if file1 and file2:
    with st.spinner("🔄 Processando comparação..."):
        # ====================================================================
        # CARREGAR DADOS
        # ====================================================================
        df1, _ = carregar_csv(file1)
        df2, _ = carregar_csv(file2)
        
        periodo1_nome = formatar_periodo_nome(file1.name, 1) or "Período 1"
        periodo2_nome = formatar_periodo_nome(file2.name, 2) or "Período 2"
        
        # Padronizar coluna de usuário
        for df in [df1, df2]:
            for col in df.columns:
                if any(t in str(col).upper() for t in ['USUÁRIO', 'USUARIO', 'CONSULTOR']):
                    df.rename(columns={col: 'USUARIO'}, inplace=True)
                    break
        
        if 'USUARIO' in df1.columns and 'USUARIO' in df2.columns:
            # Processar nomes e equipes
            for df in [df1, df2]:
                df['USUARIO'] = df['USUARIO'].astype(str).str.strip()
                df = df[~df['USUARIO'].isin(['', 'nan', 'NaN', 'None'])]
                df[['EQUIPE', 'NOME_PURO']] = df['USUARIO'].apply(
                    lambda x: pd.Series(extrair_equipe_nome(x))
                )
            
            # ====================================================================
            # SELEÇÃO DE CONSULTOR
            # ====================================================================
            consultores1 = set(df1['USUARIO'].unique())
            consultores2 = set(df2['USUARIO'].unique())
            consultores_comuns = sorted(list(consultores1 & consultores2))
            consultores_comuns = [c for c in consultores_comuns if c and str(c).lower() not in ['nan', 'none', '']]
            
            if consultores_comuns:
                st.divider()
                
                with st.container(border=True):
                    st.markdown("### 👤 Selecionar consultor")
                    
                    col_eq, col_cons = st.columns(2)
                    
                    with col_eq:
                        equipes_df1 = df1['EQUIPE'].dropna().unique()
                        equipes_df2 = df2['EQUIPE'].dropna().unique()
                        equipes_comuns = list(set(equipes_df1) & set(equipes_df2))
                        equipes_comuns = [str(e) for e in equipes_comuns if str(e).strip()]
                        
                        if equipes_comuns:
                            equipe_opcoes = ['Todas'] + sorted(equipes_comuns)
                            equipe_filtro = st.selectbox("🏢 Equipe", equipe_opcoes, key="eq_comp")
                        else:
                            equipe_filtro = 'Todas'
                    
                    with col_eq if equipes_comuns else col_cons:
                        modo_comp = st.radio(
                            "🔄 Comparar",
                            ["Mesmo consultor", "Consultores diferentes"],
                            horizontal=True,
                            key="modo_comp"
                        )
                    
                    with col_cons:
                        if modo_comp == "Mesmo consultor":
                            if equipe_filtro != 'Todas' and equipes_comuns:
                                cons_filtrados = df1[df1['EQUIPE'] == equipe_filtro]['USUARIO'].unique()
                                cons_filtrados = [c for c in cons_filtrados if c in consultores_comuns]
                            else:
                                cons_filtrados = consultores_comuns
                            
                            if cons_filtrados:
                                consultor = st.selectbox("Consultor", sorted(cons_filtrados), key="cons_unico")
                                consultor1 = consultor2 = consultor
                            else:
                                st.warning("⚠️ Nenhum consultor encontrado")
                                st.stop()
                        else:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                consultor1 = st.selectbox("Consultor 1", sorted(consultores_comuns), key="cons_a")
                            with col_b:
                                cons2_opcoes = [c for c in consultores_comuns if c != consultor1]
                                consultor2 = st.selectbox("Consultor 2", cons2_opcoes, key="cons_b")
                
                # ====================================================================
                # CARDS DOS PERÍODOS (único HTML permitido)
                # ====================================================================
                df1_filtrado = df1[df1['USUARIO'] == consultor1].copy()
                df2_filtrado = df2[df2['USUARIO'] == consultor2].copy()
                
                if not df1_filtrado.empty and not df2_filtrado.empty:
                    st.divider()
                    
                    col_per1, col_per2 = st.columns(2)
                    
                    with col_per1:
                        equipe1 = df1_filtrado['EQUIPE'].iloc[0] if 'EQUIPE' in df1_filtrado.columns else 'Sem equipe'
                        st.markdown(f"""
                        <div class="period-card-1">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                <span style="background: rgba(255,255,255,0.15); padding: 4px 14px; border-radius: 40px; font-size: 13px;">
                                    📅 {periodo1_nome}
                                </span>
                                <span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 40px; font-size: 12px;">
                                    {equipe1}
                                </span>
                            </div>
                            <div style="font-size: 28px; font-weight: 700; margin-bottom: 4px;">{consultor1}</div>
                            <div style="color: rgba(255,255,255,0.7); font-size: 14px;">
                                {len(df1_filtrado.select_dtypes(include=['number']).columns)} indicadores
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_per2:
                        equipe2 = df2_filtrado['EQUIPE'].iloc[0] if 'EQUIPE' in df2_filtrado.columns else 'Sem equipe'
                        st.markdown(f"""
                        <div class="period-card-2">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                <span style="background: rgba(255,255,255,0.15); padding: 4px 14px; border-radius: 40px; font-size: 13px;">
                                    📅 {periodo2_nome}
                                </span>
                                <span style="background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 40px; font-size: 12px;">
                                    {equipe2}
                                </span>
                            </div>
                            <div style="font-size: 28px; font-weight: 700; margin-bottom: 4px;">{consultor2}</div>
                            <div style="color: rgba(255,255,255,0.7); font-size: 14px;">
                                {len(df2_filtrado.select_dtypes(include=['number']).columns)} indicadores
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # ====================================================================
                    # PAINEL DE INDICADORES
                    # ====================================================================
                    st.divider()
                    st.markdown("### 🎯 Indicadores para comparar")
                    
                    # Identificar indicadores
                    nums1 = df1_filtrado.select_dtypes(include=['number']).columns.tolist()
                    nums2 = df2_filtrado.select_dtypes(include=['number']).columns.tolist()
                    
                    cvs_cols = []
                    for col in df1_filtrado.columns:
                        if 'CVS' in col.upper() or 'CALLBACK' in col.upper():
                            if col not in nums1:
                                cvs_cols.append(col)
                                df1_filtrado[col] = pd.to_numeric(
                                    df1_filtrado[col].astype(str).str.replace(',', '.').str.replace('%', ''),
                                    errors='coerce'
                                )
                                df2_filtrado[col] = pd.to_numeric(
                                    df2_filtrado[col].astype(str).str.replace(',', '.').str.replace('%', ''),
                                    errors='coerce'
                                )
                    
                    indicadores_comuns = sorted(list(set(nums1 + cvs_cols) & set(nums2)))
                    excluir = ['USUARIO', 'EQUIPE', 'NOME_PURO']
                    indicadores_comuns = [i for i in indicadores_comuns if i not in excluir]
                    
                    # Session state
                    if 'indicadores_selecionados' not in st.session_state:
                        st.session_state.indicadores_selecionados = indicadores_comuns[:4] if indicadores_comuns else []
                    
                    # Layout de busca
                    col_busca, col_ativos = st.columns([1, 1])
                    
                    with col_busca:
                        st.markdown("**🔍 Buscar**")
                        busca = st.text_input("Buscar", placeholder="Digite o nome...", label_visibility="collapsed")
                        
                        if busca:
                            resultados = [i for i in indicadores_comuns if busca.upper() in i.upper()]
                            if resultados:
                                for ind in resultados[:6]:
                                    nome_curto = criar_nome_curto_grafico(ind)
                                    if st.button(f"➕ {nome_curto}", key=f"add_{ind}", use_container_width=True):
                                        if ind not in st.session_state.indicadores_selecionados:
                                            st.session_state.indicadores_selecionados.append(ind)
                                            st.rerun()
                            else:
                                st.caption("Nenhum encontrado")
                    
                    with col_ativos:
                        st.markdown("**📋 Selecionados**")
                        if st.session_state.indicadores_selecionados:
                            for ind in st.session_state.indicadores_selecionados.copy():
                                nome_curto = criar_nome_curto_grafico(ind)
                                col_tag, col_rm = st.columns([5, 1])
                                with col_tag:
                                    st.markdown(f"**{nome_curto}**  \n`{ind[:30]}...`" if len(ind) > 30 else f"**{nome_curto}**  \n`{ind}`")
                                with col_rm:
                                    if st.button("🗑️", key=f"rm_{ind}", help="Remover"):
                                        st.session_state.indicadores_selecionados.remove(ind)
                                        st.rerun()
                            
                            if st.button("🧹 Limpar todos", use_container_width=True):
                                st.session_state.indicadores_selecionados = []
                                st.rerun()
                        else:
                            st.caption("Nenhum selecionado")
                    
                    indicadores_selecionados = st.session_state.indicadores_selecionados
                    
                    if indicadores_selecionados:
                        # ====================================================================
                        # ABAS PARA CADA MODO DE VISUALIZAÇÃO (mais compacto)
                        # ====================================================================
                        st.divider()
                        
                        tab1, tab2, tab3 = st.tabs(["📅 Períodos", "🎯 vs Meta", "📊 Variação"])
                        
                        # ====================================================================
                        # PROCESSAR DADOS (uma vez só)
                        # ====================================================================
                        dados_cards = []
                        for indicador in indicadores_selecionados:
                            if indicador in df1_filtrado.columns and indicador in df2_filtrado.columns:
                                v1 = safe_float(df1_filtrado[indicador].iloc[0])
                                v2 = safe_float(df2_filtrado[indicador].iloc[0])
                                
                                variacao = calcular_variacao_percentual(v1, v2)
                                
                                # Metas
                                meta1 = None
                                if 'EQUIPE' in df1_filtrado.columns:
                                    meta1 = obter_meta(indicador, consultor1, df1_filtrado['EQUIPE'].iloc[0])
                                else:
                                    meta1 = obter_meta(indicador, consultor1)
                                
                                meta2 = None
                                if 'EQUIPE' in df2_filtrado.columns:
                                    meta2 = obter_meta(indicador, consultor2, df2_filtrado['EQUIPE'].iloc[0])
                                else:
                                    meta2 = obter_meta(indicador, consultor2)
                                
                                prog1 = calcular_progresso_meta(v1, meta1['valor']) if meta1 else None
                                prog2 = calcular_progresso_meta(v2, meta2['valor']) if meta2 else None
                                
                                dados_cards.append({
                                    'indicador': indicador,
                                    'nome_curto': criar_nome_curto_grafico(indicador),
                                    'v1': v1,
                                    'v2': v2,
                                    'v1_fmt': safe_formatar_valor(v1),
                                    'v2_fmt': safe_formatar_valor(v2),
                                    'variacao': variacao,
                                    'meta1': meta1,
                                    'meta2': meta2,
                                    'meta1_fmt': safe_formatar_valor(meta1['valor']) if meta1 else None,
                                    'meta2_fmt': safe_formatar_valor(meta2['valor']) if meta2 else None,
                                    'prog1': prog1,
                                    'prog2': prog2,
                                    'equipe1': df1_filtrado['EQUIPE'].iloc[0] if 'EQUIPE' in df1_filtrado.columns else None,
                                    'equipe2': df2_filtrado['EQUIPE'].iloc[0] if 'EQUIPE' in df2_filtrado.columns else None
                                })
                        
                        if dados_cards:
                            # Ordenar por impacto
                            dados_cards.sort(key=lambda x: abs(x['variacao']), reverse=True)
                            
                            # ========== ABA 1: PERÍODOS ==========
                            with tab1:
                                st.markdown("### 📊 Comparação direta")
                                
                                # Grid de 2 colunas para cards
                                for i in range(0, len(dados_cards), 2):
                                    cols = st.columns(2)
                                    
                                    # Primeiro card da linha
                                    with cols[0]:
                                        card = dados_cards[i]
                                        st.markdown(f"**{card['nome_curto']}**")
                                        st.caption(card['indicador'])
                                        
                                        col_p1, col_p2 = st.columns(2)
                                        with col_p1:
                                            st.markdown(f":blue[📅 {periodo1_nome}]")
                                            criar_card_indicador(
                                                card['v1'], 
                                                card['indicador'], 
                                                consultor1, 
                                                card['equipe1']
                                            )
                                        with col_p2:
                                            st.markdown(f":orange[📅 {periodo2_nome}]")
                                            criar_card_indicador(
                                                card['v2'], 
                                                card['indicador'], 
                                                consultor2, 
                                                card['equipe2']
                                            )
                                        
                                        if card['variacao'] > 5:
                                            st.success(f"📈 +{card['variacao']:.1f}%")
                                        elif card['variacao'] < -5:
                                            st.error(f"📉 {card['variacao']:.1f}%")
                                        else:
                                            st.info(f"➡️ {card['variacao']:+.1f}%")
                                    
                                    # Segundo card da linha (se existir)
                                    if i + 1 < len(dados_cards):
                                        with cols[1]:
                                            card = dados_cards[i + 1]
                                            st.markdown(f"**{card['nome_curto']}**")
                                            st.caption(card['indicador'])
                                            
                                            col_p1, col_p2 = st.columns(2)
                                            with col_p1:
                                                st.markdown(f":blue[📅 {periodo1_nome}]")
                                                criar_card_indicador(
                                                    card['v1'], 
                                                    card['indicador'], 
                                                    consultor1, 
                                                    card['equipe1']
                                                )
                                            with col_p2:
                                                st.markdown(f":orange[📅 {periodo2_nome}]")
                                                criar_card_indicador(
                                                    card['v2'], 
                                                    card['indicador'], 
                                                    consultor2, 
                                                    card['equipe2']
                                                )
                                            
                                            if card['variacao'] > 5:
                                                st.success(f"📈 +{card['variacao']:.1f}%")
                                            elif card['variacao'] < -5:
                                                st.error(f"📉 {card['variacao']:.1f}%")
                                            else:
                                                st.info(f"➡️ {card['variacao']:+.1f}%")
                                    
                                    st.divider()
                            
                            # ========== ABA 2: VS META ==========
                            with tab2:
                                st.markdown("### 🎯 Comparação com metas")
                                
                                for i in range(0, len(dados_cards), 2):
                                    cols = st.columns(2)
                                    
                                    with cols[0]:
                                        card = dados_cards[i]
                                        st.markdown(f"**{card['nome_curto']}**")
                                        st.caption(card['indicador'])
                                        
                                        col_m1, col_m2 = st.columns(2)
                                        with col_m1:
                                            st.markdown(f":blue[**{periodo1_nome}**]")
                                            st.metric("Realizado", card['v1_fmt'])
                                            if card['meta1']:
                                                st.markdown(f"🎯 Meta: {card['meta1_fmt']}")
                                                if card['prog1'] and card['prog1'] >= 100:
                                                    st.success(f"✅ {card['prog1']:.0f}%")
                                                else:
                                                    st.caption(f"{card['prog1']:.0f}%")
                                            else:
                                                st.caption("Sem meta")
                                        
                                        with col_m2:
                                            st.markdown(f":orange[**{periodo2_nome}**]")
                                            st.metric("Realizado", card['v2_fmt'])
                                            if card['meta2']:
                                                st.markdown(f"🎯 Meta: {card['meta2_fmt']}")
                                                if card['prog2'] and card['prog2'] >= 100:
                                                    st.success(f"✅ {card['prog2']:.0f}%")
                                                else:
                                                    st.caption(f"{card['prog2']:.0f}%")
                                            else:
                                                st.caption("Sem meta")
                                    
                                    if i + 1 < len(dados_cards):
                                        with cols[1]:
                                            card = dados_cards[i + 1]
                                            st.markdown(f"**{card['nome_curto']}**")
                                            st.caption(card['indicador'])
                                            
                                            col_m1, col_m2 = st.columns(2)
                                            with col_m1:
                                                st.markdown(f":blue[**{periodo1_nome}**]")
                                                st.metric("Realizado", card['v1_fmt'])
                                                if card['meta1']:
                                                    st.markdown(f"🎯 Meta: {card['meta1_fmt']}")
                                                    if card['prog1'] and card['prog1'] >= 100:
                                                        st.success(f"✅ {card['prog1']:.0f}%")
                                                    else:
                                                        st.caption(f"{card['prog1']:.0f}%")
                                                else:
                                                    st.caption("Sem meta")
                                            
                                            with col_m2:
                                                st.markdown(f":orange[**{periodo2_nome}**]")
                                                st.metric("Realizado", card['v2_fmt'])
                                                if card['meta2']:
                                                    st.markdown(f"🎯 Meta: {card['meta2_fmt']}")
                                                    if card['prog2'] and card['prog2'] >= 100:
                                                        st.success(f"✅ {card['prog2']:.0f}%")
                                                    else:
                                                        st.caption(f"{card['prog2']:.0f}%")
                                                else:
                                                    st.caption("Sem meta")
                                    
                                    st.divider()
                            
                            # ========== ABA 3: VARIAÇÃO ==========
                            with tab3:
                                st.markdown("### 📊 Diferença absoluta e percentual")
                                
                                for i in range(0, len(dados_cards), 2):
                                    cols = st.columns(2)
                                    
                                    with cols[0]:
                                        card = dados_cards[i]
                                        st.markdown(f"**{card['nome_curto']}**")
                                        st.caption(card['indicador'])
                                        
                                        col_v1, col_v2, col_var = st.columns([2, 2, 1])
                                        with col_v1:
                                            st.markdown(f":blue[**{periodo1_nome}**]")
                                            st.markdown(f"# {card['v1_fmt']}")
                                        with col_v2:
                                            st.markdown(f":orange[**{periodo2_nome}**]")
                                            st.markdown(f"# {card['v2_fmt']}")
                                        with col_var:
                                            diff_abs = card['v2'] - card['v1']
                                            diff_fmt = safe_formatar_valor(abs(diff_abs))
                                            sinal = "+" if diff_abs > 0 else "-"
                                            cor = "green" if diff_abs > 0 else "red" if diff_abs < 0 else "gray"
                                            st.markdown(f":{cor}[**{sinal}{diff_fmt}**]")
                                            st.markdown(f":{cor}[({sinal}{card['variacao']:.1f}%)]")
                                    
                                    if i + 1 < len(dados_cards):
                                        with cols[1]:
                                            card = dados_cards[i + 1]
                                            st.markdown(f"**{card['nome_curto']}**")
                                            st.caption(card['indicador'])
                                            
                                            col_v1, col_v2, col_var = st.columns([2, 2, 1])
                                            with col_v1:
                                                st.markdown(f":blue[**{periodo1_nome}**]")
                                                st.markdown(f"# {card['v1_fmt']}")
                                            with col_v2:
                                                st.markdown(f":orange[**{periodo2_nome}**]")
                                                st.markdown(f"# {card['v2_fmt']}")
                                            with col_var:
                                                diff_abs = card['v2'] - card['v1']
                                                diff_fmt = safe_formatar_valor(abs(diff_abs))
                                                sinal = "+" if diff_abs > 0 else "-"
                                                cor = "green" if diff_abs > 0 else "red" if diff_abs < 0 else "gray"
                                                st.markdown(f":{cor}[**{sinal}{diff_fmt}**]")
                                                st.markdown(f":{cor}[({sinal}{card['variacao']:.1f}%)]")
                                    
                                    st.divider()
                            
                            # ====================================================================
                            # CARDS DE DESTAQUE (mantido)
                            # ====================================================================
                            st.divider()
                            st.markdown("### ⚡ Destaques")
                            
                            variacoes = [d['variacao'] for d in dados_cards]
                            melhor = max(variacoes) if variacoes else 0
                            pior = min(variacoes) if variacoes else 0
                            melhor_idx = variacoes.index(melhor) if variacoes else 0
                            pior_idx = variacoes.index(pior) if variacoes else 0
                            metas_atingidas = sum(1 for d in dados_cards if d['prog2'] and d['prog2'] >= 100)
                            
                            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                            
                            with col_d1:
                                with st.container(border=True):
                                    st.markdown("📈 **Maior evolução**")
                                    st.markdown(f"### {dados_cards[melhor_idx]['nome_curto']}")
                                    st.markdown(f"# :green[+{melhor:.1f}%]")
                                    st.caption(f"{dados_cards[melhor_idx]['v1_fmt']} → {dados_cards[melhor_idx]['v2_fmt']}")
                            
                            with col_d2:
                                with st.container(border=True):
                                    st.markdown("📉 **Maior queda**")
                                    st.markdown(f"### {dados_cards[pior_idx]['nome_curto']}")
                                    st.markdown(f"# :red[{pior:.1f}%]")
                                    st.caption(f"{dados_cards[pior_idx]['v1_fmt']} → {dados_cards[pior_idx]['v2_fmt']}")
                            
                            with col_d3:
                                with st.container(border=True):
                                    st.markdown("✅ **Metas atingidas**")
                                    st.markdown(f"# {metas_atingidas}")
                                    st.caption(f"em {periodo2_nome}")
                            
                            with col_d4:
                                with st.container(border=True):
                                    st.markdown("📊 **Total analisado**")
                                    st.markdown(f"# {len(dados_cards)}")
                                    st.caption("indicadores comparados")
                            
                            # ====================================================================
                            # EXPORTAÇÃO
                            # ====================================================================
                            st.divider()
                            st.markdown("### 💾 Exportar")
                            
                            col_act1, col_act2 = st.columns(2)
                            
                            with col_act1:
                                if st.button("📥 Exportar Excel", use_container_width=True):
                                    from io import BytesIO
                                    
                                    output = BytesIO()
                                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                        df_export = pd.DataFrame([{
                                            'Indicador': d['indicador'],
                                            f'{periodo1_nome}': d['v1_fmt'],
                                            f'Meta {periodo1_nome}': d['meta1_fmt'] if d['meta1_fmt'] else '—',
                                            f'{periodo2_nome}': d['v2_fmt'],
                                            f'Meta {periodo2_nome}': d['meta2_fmt'] if d['meta2_fmt'] else '—',
                                            'Variação %': f"{d['variacao']:+.1f}%",
                                            'Progresso P1': f"{d['prog1']:.0f}%" if d['prog1'] else '—',
                                            'Progresso P2': f"{d['prog2']:.0f}%" if d['prog2'] else '—'
                                        } for d in dados_cards])
                                        
                                        df_export.to_excel(writer, index=False, sheet_name='Comparativo')
                                        
                                        pd.DataFrame([{
                                            'Consultor 1': consultor1,
                                            'Consultor 2': consultor2,
                                            'Período 1': periodo1_nome,
                                            'Período 2': periodo2_nome,
                                            'Data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                                            'Total Indicadores': len(dados_cards),
                                            'Metas Atingidas': metas_atingidas
                                        }]).to_excel(writer, index=False, sheet_name='Resumo')
                                    
                                    output.seek(0)
                                    st.download_button(
                                        "⬇️ Baixar relatório",
                                        data=output,
                                        file_name=f"comparativo_{consultor1}_vs_{consultor2}.xlsx",
                                        use_container_width=True
                                    )
                            
                            with col_act2:
                                if st.button("🔄 Nova comparação", use_container_width=True):
                                    if 'indicadores_selecionados' in st.session_state:
                                        del st.session_state.indicadores_selecionados
                                    st.rerun()
                    
                    else:
                        st.info("👆 Adicione indicadores para começar")
                else:
                    st.warning("⚠️ Dados não encontrados para o consultor selecionado")
            else:
                st.error("❌ Nenhum consultor em comum entre os dois períodos")
        else:
            st.error("❌ Coluna 'USUÁRIO' não encontrada em um dos arquivos")

elif file1 or file2:
    st.info("📁 Aguardando o segundo arquivo...")
else:
    with st.expander("💡 Como usar", expanded=True):
        st.markdown("""
        ### 📋 Passo a passo:
        
        1. **Carregue dois arquivos CSV** com os dados dos períodos
        2. **Selecione o consultor** (mesmo ou diferentes)
        3. **Adicione indicadores** usando a busca
        4. **Navegue pelas abas** para diferentes visualizações:
           - **📅 Períodos**: Cards lado a lado
           - **🎯 vs Meta**: Comparação com metas
           - **📊 Variação**: Diferença absoluta e percentual
        5. **Veja os destaques** automáticos
        
        ### ✨ Novidades:
        - 🎯 **Metas 100% agora em branco no verde** (legível!)
        - 📊 **Grid de 2 colunas** - 50% menos scroll
        - 🔄 **Abas** - interface mais limpa
        - ⚡ **Mais rápido e responsivo**
        """)