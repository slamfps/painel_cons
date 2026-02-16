import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

# Importar funções dos módulos
from src.utils import (
    corrigir_colunas, extrair_equipe_nome, formatar_valor, 
    carregar_csv, formatar_periodo_nome
)
from src.metas import (
    inicializar_sistema_metas, obter_meta, salvar_meta,
    calcular_progresso_meta, obter_cor_progresso, formatar_progresso_texto,
    criar_card_indicador
)

# ============================================================================
# FUNÇÕES AUXILIARES PARA MELHOR VISUALIZAÇÃO
# ============================================================================
def criar_nome_curto_grafico(indicador):
    """
    Cria versão abreviada dos nomes dos indicadores para o gráfico
    """
    # Mapeamento de abreviações
    mapeamento = {
        'PONTOS': 'PTS',
        'HABILITADO': 'HAB',
        'FINALIZADO': 'FIN', 
        'TOTAL': 'TOT',
        'VENDAS': 'VDS',
        'CHIP': 'CHP',
        'TELEVISAO': 'TV',
        'TELEVISÃO': 'TV',
        'TELEVISION': 'TV',
        'PRODUTO': 'PDT',
        'QUALIDADE': 'QLD',
        'ATENDIMENTO': 'ATD',
        'CALLBACK': 'CB',
        'RECEITA': 'REC',
        'MEDIA': 'MED',
        'MÉDIA': 'MED',
        'MAXIMO': 'MAX',
        'MÁXIMO': 'MAX',
        'MINIMO': 'MIN',
        'MÍNIMO': 'MIN',
        'FINAL': 'FIN',
        'HABILITACAO': 'HAB',
        'HABILITAÇÃO': 'HAB',
        'NOVO': 'NV',
        'PME': 'PM',
        'CPF': 'CP',
        'CNPJ': 'CN',
        'GERAL': 'GER',
        'FIXA': 'FX',
        'MOVEL': 'MV',
        'MÓVEL': 'MV',
        'CVS': 'CV',
        'C/': ''
    }
    
    indicador_upper = indicador.upper()
    resultado = indicador_upper
    
    # Aplica abreviações (do maior para o menor)
    for palavra, abrev in sorted(mapeamento.items(), key=lambda x: -len(x[0])):
        if palavra in resultado:
            resultado = resultado.replace(palavra, abrev)
    
    # Remove espaços duplos e ajusta
    resultado = ' '.join(resultado.split())
    resultado = resultado.replace('  ', ' ').strip()
    
    # Se ainda for muito longo, corta inteligentemente
    if len(resultado) > 20:
        partes = resultado.split()
        if len(partes) > 2:
            resultado = ' '.join(partes[:2]) + '...'
        else:
            resultado = resultado[:18] + "..."
    
    return resultado

def obter_cor_progresso_grafico(progresso):
    """
    Cores otimizadas para o gráfico - melhor contraste
    """
    if progresso >= 100:
        return '#059669'  # Verde escuro vibrante
    elif progresso >= 80:
        return '#10B981'  # Verde médio
    elif progresso >= 50:
        return '#D97706'  # Laranja escuro
    elif progresso >= 30:
        return '#F59E0B'  # Laranja médio
    else:
        return '#DC2626'  # Vermelho escuro vibrante

def formatar_valor_grafico(valor):
    """
    Formata valores para exibição no gráfico
    """
    try:
        if pd.isna(valor):
            return "0"
        
        # Converte para número
        valor_str = str(valor).replace('%', '').replace(',', '.').strip()
        num_valor = float(valor_str)
        
        # Formata baseado no tamanho
        if num_valor >= 1000000:
            return f"{num_valor/1000000:.1f}M"
        elif num_valor >= 1000:
            return f"{num_valor/1000:.0f}K"
        elif num_valor.is_integer():
            return f"{int(num_valor):,}".replace(",", ".")
        else:
            return f"{num_valor:.1f}"
    except:
        return str(valor)

# ============================================================================
# PÁGINA: VISÃO INDIVIDUAL
# ============================================================================
st.title("👤 Análise Individual por Consultor")

# Inicializar sistema de metas
inicializar_sistema_metas()

# Upload do arquivo
with st.container():
    st.markdown("### 📁 Carregar Arquivo do Mês")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV com os dados:",
        type="csv",
        help="Arquivo deve conter coluna 'USUÁRIO' ou similar",
        key="upload_individual"
    )
    
    if uploaded_file:
        st.success("✅ Arquivo carregado com sucesso!")

if uploaded_file is not None:
    # Carregar dados
    with st.spinner("📊 Processando dados..."):
        df, sep_used = carregar_csv(uploaded_file)
    
    # Encontrar coluna do consultor
    for col in df.columns:
        col_upper = str(col).upper()
        if any(term in col_upper for term in ['USUÁRIO', 'USUARIO', 'CONSULTOR', 'VENDEDOR']):
            df = df.rename(columns={col: 'USUARIO'})
            break
    
    if 'USUARIO' in df.columns:
        # Processar dados
        df['USUARIO'] = df['USUARIO'].astype(str).str.strip()
        df = df[~df['USUARIO'].isin(['', 'nan', 'NaN', 'None', 'none'])]
        df[['EQUIPE', 'NOME_PURO']] = df['USUARIO'].apply(
            lambda x: pd.Series(extrair_equipe_nome(x))
        )
        
        consultores = sorted(df['USUARIO'].unique().tolist())
        st.session_state.todos_indicadores = df.columns.tolist()
        
        if consultores:
            # ============================================================
            # SEÇÃO 1: FILTROS
            # ============================================================
            st.markdown("---")
            st.markdown("### 🔍 Selecionar Consultor")
            
            col_equipe, col_consultor = st.columns(2)
            
            with col_equipe:
                if 'EQUIPE' in df.columns and df['EQUIPE'].nunique() > 1:
                    equipes = ['Todas as Equipes'] + sorted(df['EQUIPE'].unique().tolist())
                    equipe_selecionada = st.selectbox(
                        "Filtrar por equipe:",
                        equipes,
                        key="equipe_filter"
                    )
                    
                    if equipe_selecionada != 'Todas as Equipes':
                        consultores_filtrados = df[df['EQUIPE'] == equipe_selecionada]['USUARIO'].unique().tolist()
                    else:
                        consultores_filtrados = consultores
                else:
                    consultores_filtrados = consultores
                    equipe_selecionada = None
            
            with col_consultor:
                consultor_selecionado = st.selectbox(
                    "Selecionar consultor:",
                    sorted(consultores_filtrados),
                    key="consultor_select_main"
                )
            
            # Dados do consultor selecionado
            df_filtrado = df[df['USUARIO'] == consultor_selecionado]
            
            if not df_filtrado.empty:
                # ============================================================
                # SEÇÃO 2: CABEÇALHO INFORMATIVO
                # ============================================================
                st.markdown("---")
                
                col_header1, col_header2, col_header3, col_header4 = st.columns(4)
                
                with col_header1:
                    st.markdown("**👤 Consultor**")
                    st.markdown(f"### {consultor_selecionado}")
                
                with col_header2:
                    if 'EQUIPE' in df_filtrado.columns and df_filtrado['EQUIPE'].iloc[0]:
                        st.markdown("**🏢 Equipe**")
                        st.markdown(f"### {df_filtrado['EQUIPE'].iloc[0]}")
                
                with col_header3:
                    metas_consultor = 0
                    for chave in st.session_state.metas:
                        if consultor_selecionado in chave:
                            metas_consultor += 1
                    
                    st.markdown("**🎯 Metas Definidas**")
                    st.markdown(f"### {metas_consultor}")
                
                with col_header4:
                    st.markdown("**📅 Data da Análise**")
                    st.markdown(f"### {datetime.now().strftime('%d/%m')}")
                
                # ============================================================
                # SEÇÃO 3: SELEÇÃO PERSONALIZADA DE INDICADORES - VERSÃO COMPACTA
                # ============================================================
                st.markdown("---")
                
                with st.container():
                    st.markdown("### 🎯 Indicadores em Destaque")
                    
                    colunas_excluir = ['USUARIO', 'EQUIPE', 'NOME_PURO', 'USUÁRIO', 'CONSULTOR', 'VENDEDOR']
                    
                    # Converte colunas problemáticas
                    for col in df_filtrado.columns:
                        if col not in colunas_excluir and df_filtrado[col].dtype == 'object':
                            try:
                                df_filtrado[col] = df_filtrado[col].astype(str).str.replace(',', '.').str.replace('%', '')
                                df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')
                            except:
                                pass
                    
                    # Lista indicadores disponíveis
                    todos_indicadores = []
                    for col in df_filtrado.columns:
                        if col not in colunas_excluir:
                            if pd.api.types.is_numeric_dtype(df_filtrado[col]):
                                todos_indicadores.append(col)
                            elif any(term in col.upper() for term in ['CHIP', 'PONTOS', 'VENDAS', 'CVS', 'CALLBACK']):
                                todos_indicadores.append(col)
                    
                    if not todos_indicadores:
                        todos_indicadores = [col for col in df_filtrado.columns if col not in colunas_excluir]
                    
                    # Select sem label e compacto
                    col_sel1, col_sel2 = st.columns([4, 1])
                    
                    with col_sel1:
                        indicadores_selecionados = st.multiselect(
                            "##",  # Label invisível
                            options=todos_indicadores,
                            default=st.session_state.get('indicadores_favoritos', todos_indicadores[:4]),
                            key="multiselect_indicadores",
                            label_visibility="collapsed",  # ESSENCIAL!
                            placeholder="Selecione os indicadores..."
                        )
                    
                    with col_sel2:
                        st.write("")  # Alinhamento
                        if st.button("💾 Salvar", use_container_width=True, type="secondary"):
                            if indicadores_selecionados:
                                st.session_state.indicadores_favoritos = indicadores_selecionados
                                st.rerun()
                    
                    if indicadores_selecionados:
                        st.session_state.indicadores_favoritos = indicadores_selecionados
                
                # ============================================================
                # SEÇÃO 4: CARDS DOS INDICADORES - GRADE COMPACTA
                # ============================================================
                st.markdown("---")
                
                # CSS para compactar o layout
                st.markdown("""
                <style>
                    /* Remove espaçamento entre colunas */
                    div[data-testid="column"] {
                        padding: 0 4px !important;
                    }
                    /* Remove margens extras */
                    div.stContainer {
                        padding: 0 !important;
                        margin-bottom: 0 !important;
                    }
                    /* Compacta grid */
                    .st-emotion-cache-16ids5p {
                        gap: 0.5rem !important;
                    }
                    /* Reduz espaçamento dos cards */
                    .element-container {
                        margin-bottom: 0 !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                if st.session_state.indicadores_favoritos:
                    st.caption(f"📊 {len(st.session_state.indicadores_favoritos)} indicadores selecionados")
                    
                    indicadores_para_mostrar = st.session_state.indicadores_favoritos
                    
                    for i in range(0, len(indicadores_para_mostrar), 3):
                        cols = st.columns(3, gap="small")
                        indicadores_linha = indicadores_para_mostrar[i:i+3]
                        
                        for idx, (col, indicador) in enumerate(zip(cols, indicadores_linha)):
                            with col:
                                valor = df_filtrado[indicador].iloc[0]
                                equipe = df_filtrado['EQUIPE'].iloc[0] if 'EQUIPE' in df_filtrado.columns else None
                                
                                criar_card_indicador(
                                    valor, 
                                    indicador, 
                                    consultor_selecionado, 
                                    equipe
                                )
                else:
                    st.info("👆 Selecione os indicadores acima")
                
                # ============================================================
                # SEÇÃO 6: GRÁFICO INTERATIVO
                # ============================================================
                if st.session_state.indicadores_favoritos:
                    st.markdown("---")
                    st.markdown("### 📈 Visualização dos Indicadores")
                    
                    # Prepara dados para o gráfico
                    dados_grafico = []
                    valores_grafico = []
                    valores_formatados = []
                    cores_grafico = []
                    textos_hover = []
                    metas_valores = []
                    
                    for indicador in st.session_state.indicadores_favoritos:
                        valor = df_filtrado[indicador].iloc[0]
                        try:
                            if pd.isna(valor):
                                num_valor = 0
                            else:
                                valor_str = str(valor).replace('%', '').replace(',', '.').strip()
                                num_valor = float(valor_str)
                        except:
                            num_valor = 0
                        
                        nome_curto = criar_nome_curto_grafico(indicador)
                        dados_grafico.append(nome_curto)
                        valores_grafico.append(num_valor)
                        valores_formatados.append(formatar_valor_grafico(num_valor))
                        
                        equipe_atual = df_filtrado['EQUIPE'].iloc[0] if 'EQUIPE' in df_filtrado.columns else None
                        meta = obter_meta(indicador, consultor_selecionado, equipe_atual)
                        
                        if meta:
                            progresso = calcular_progresso_meta(valor, meta['valor'])
                            cores_grafico.append(obter_cor_progresso_grafico(progresso))
                            textos_hover.append(
                                f"<b>{indicador}</b><br>" +
                                f"<span style='color:#3B82F6; font-weight:bold'>Valor: {formatar_valor(valor)}</span><br>" +
                                f"<span style='color:#059669; font-weight:bold'>Meta: {formatar_valor(meta['valor'])}</span><br>" +
                                f"<span style='color:#6B7280'>Progresso: {progresso:.1f}%</span><br>" +
                                f"<span style='color:{obter_cor_progresso_grafico(progresso)}; font-weight:bold'>" +
                                f"{'✅ Meta atingida' if progresso >= 100 else '🟡 Em progresso' if progresso >= 50 else '🔴 Abaixo da meta'}</span>"
                            )
                            metas_valores.append(meta['valor'])
                        else:
                            cores_grafico.append('#3B82F6')
                            textos_hover.append(
                                f"<b>{indicador}</b><br>" +
                                f"<span style='color:#3B82F6; font-weight:bold'>Valor: {formatar_valor(valor)}</span><br>" +
                                f"<span style='color:#6B7280'>Meta: Não definida</span>"
                            )
                            metas_valores.append(None)
                    
                    # Ordena por valor
                    dados_ordenados = sorted(zip(valores_grafico, dados_grafico, cores_grafico, 
                                               textos_hover, metas_valores, valores_formatados), 
                                           reverse=True)
                    
                    if dados_ordenados:
                        valores_grafico, dados_grafico, cores_grafico, textos_hover, metas_valores, valores_formatados = zip(*dados_ordenados)
                    
                    # Cria gráfico
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        y=list(dados_grafico),
                        x=list(valores_grafico),
                        orientation='h',
                        marker=dict(
                            color=list(cores_grafico),
                            line=dict(color='rgba(0,0,0,0.3)', width=1.5),
                            opacity=0.9
                        ),
                        text=list(valores_formatados),
                        textposition='outside',
                        textfont=dict(size=11, color='black'),
                        hovertemplate='%{customdata}<extra></extra>',
                        customdata=list(textos_hover)
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text=f'Indicadores - {consultor_selecionado}',
                            font=dict(size=16, color="#1E3A8A"),
                            x=0.5
                        ),
                        height=max(350, len(dados_grafico) * 40),
                        margin=dict(l=5, r=5, t=50, b=30),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                    })
                    
                    # Legenda compacta
                    with st.expander("🎯 Legenda do Gráfico", expanded=False):
                        legenda_cols = st.columns(5)
                        with legenda_cols[0]: st.markdown("🔵 Sem meta")
                        with legenda_cols[1]: st.markdown("🟢 Meta ≥100%")
                        with legenda_cols[2]: st.markdown("🟩 Meta ≥80%")
                        with legenda_cols[3]: st.markdown("🟠 Meta ≥50%")
                        with legenda_cols[4]: st.markdown("🔴 Meta <50%")
                
                # ============================================================
                # SEÇÃO 7: TABELA COMPLETA
                # ============================================================
                st.markdown("---")
                st.markdown("### 📋 Todos os Indicadores")
                
                busca_indicador = st.text_input(
                    "🔍",
                    placeholder="Buscar indicador...",
                    key="busca_indicador",
                    label_visibility="collapsed"
                )
                
                if busca_indicador:
                    colunas_filtradas = [col for col in df_filtrado.columns 
                                       if busca_indicador.upper() in col.upper()]
                    df_mostrar = df_filtrado[colunas_filtradas]
                else:
                    df_mostrar = df_filtrado
                
                colunas_remover = ['USUARIO', 'EQUIPE', 'NOME_PURO']
                df_mostrar = df_mostrar.drop(columns=[c for c in colunas_remover if c in df_mostrar.columns])
                
                if not df_mostrar.empty:
                    df_formatado = df_mostrar.copy()
                    for col in df_formatado.columns:
                        if pd.api.types.is_numeric_dtype(df_formatado[col]):
                            df_formatado[col] = df_formatado[col].apply(lambda x: formatar_valor(x))
                    
                    st.dataframe(df_formatado, use_container_width=True, height=250)
                else:
                    st.warning("Nenhum indicador encontrado")
                
                # ============================================================
                # SEÇÃO 8: AÇÕES
                # ============================================================
                st.markdown("---")
                st.markdown("### ⚙️ Ações")
                
                col_acao1, col_acao2, col_acao3 = st.columns(3)
                
                with col_acao1:
                    if st.button("📥 Exportar Excel", use_container_width=True):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_filtrado.to_excel(writer, index=False, sheet_name='Dados')
                            
                            metas_consultor = []
                            for chave, meta in st.session_state.metas.items():
                                if consultor_selecionado in chave:
                                    progresso = calcular_progresso_meta(
                                        df_filtrado[meta['indicador']].iloc[0] if meta['indicador'] in df_filtrado.columns else 0,
                                        meta['valor']
                                    )
                                    metas_consultor.append({
                                        'Indicador': meta['indicador'],
                                        'Meta': meta['valor'],
                                        'Valor Atual': df_filtrado[meta['indicador']].iloc[0] if meta['indicador'] in df_filtrado.columns else 'N/A',
                                        'Progresso': f"{progresso:.1f}%"
                                    })
                            
                            if metas_consultor:
                                pd.DataFrame(metas_consultor).to_excel(writer, index=False, sheet_name='Metas')
                        
                        output.seek(0)
                        st.download_button("⬇️ Baixar", data=output, 
                                         file_name=f"relatorio_{consultor_selecionado}.xlsx")
                
                with col_acao2:
                    if st.button("🖨️ Imprimir", use_container_width=True):
                        st.info("Ctrl+P para imprimir")
                
                with col_acao3:
                    if st.button("🔄 Nova", use_container_width=True):
                        st.rerun()
            
            else:
                st.warning("⚠️ Nenhum dado encontrado")
        else:
            st.error("❌ Nenhum consultor encontrado")
    else:
        st.error("❌ Coluna de consultor não encontrada")
        with st.expander("Ver colunas"):
            st.write(df.columns.tolist())