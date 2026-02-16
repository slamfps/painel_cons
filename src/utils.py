import pandas as pd
import numpy as np
from datetime import datetime
import re

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================
def corrigir_colunas(df):
    """Corrige encoding e padroniza nomes de colunas."""
    df.columns = df.columns.str.encode('latin-1').str.decode('utf-8', errors='ignore')
    
    # Correções específicas
    df.columns = df.columns.str.replace('Ã¡', 'á', regex=False)
    df.columns = df.columns.str.replace('Ã£', 'ã', regex=False)
    df.columns = df.columns.str.replace('Ã§', 'ç', regex=False)
    df.columns = df.columns.str.replace('Ã©', 'é', regex=False)
    df.columns = df.columns.str.replace('Ã³', 'ó', regex=False)
    df.columns = df.columns.str.replace('Ãª', 'ê', regex=False)
    df.columns = df.columns.str.replace('Ãµ', 'õ', regex=False)
    df.columns = df.columns.str.replace('Ãº', 'ú', regex=False)
    df.columns = df.columns.str.replace('pÃs', 'pós', regex=False)
    
    df.columns = df.columns.str.upper().str.strip()
    df.columns = df.columns.str.replace('\s+', ' ', regex=True)
    
    return df

def extrair_equipe_nome(usuario):
    """Extrai equipe e nome puro do formato 'COD.EQUIPE.Nome'."""
    if isinstance(usuario, str):
        if '.' in usuario:
            parts = usuario.split('.')
            if len(parts) >= 2:
                equipe = parts[0]
                nome = '.'.join(parts[1:])
                return equipe, nome
    return "", str(usuario)

def formatar_valor(valor, formato='auto'):
    """Formata valores para exibição."""
    try:
        if pd.isna(valor):
            return "N/A"
        
        valor_str = str(valor).strip()
        
        # Verifica se é percentual
        if '%' in valor_str:
            num = float(valor_str.replace('%', '').replace(',', '.'))
            return f"{num:.1f}%"
        
        # Tenta converter para número
        num = float(valor_str.replace(',', '.'))
        
        # Formata baseado no formato solicitado
        if formato == 'porcentagem':
            return f"{num:.1f}%"
        elif formato == 'inteiro':
            return f"{num:,.0f}"
        elif formato == 'decimal':
            if abs(num) >= 1000:
                return f"{num:,.0f}"
            elif abs(num) >= 1:
                return f"{num:,.1f}"
            else:
                return f"{num:.3f}"
        else:  # auto
            if num == 0:
                return "0"
            elif abs(num) >= 1000:
                return f"{num:,.0f}"
            elif abs(num) >= 1:
                return f"{num:,.1f}"
            else:
                return f"{num:.3f}"
            
    except (ValueError, AttributeError):
        return str(valor)

def carregar_csv(file_uploader):
    """Carrega CSV detectando separador automaticamente."""
    conteudo = file_uploader.read().decode('latin-1')
    file_uploader.seek(0)
    
    sep = ';' if ';' in conteudo.split('\n')[0] else ','
    df = pd.read_csv(file_uploader, sep=sep, encoding='latin-1')
    df = corrigir_colunas(df)
    
    return df, sep

def calcular_variacao_percentual(valor1, valor2):
    """Calcula variação percentual entre dois valores."""
    try:
        v1 = float(str(valor1).replace(',', '.').replace('%', '')) if not pd.isna(valor1) else 0
        v2 = float(str(valor2).replace(',', '.').replace('%', '')) if not pd.isna(valor2) else 0
        
        if v1 == 0:
            return 100.0 if v2 > 0 else (0.0 if v2 == 0 else -100.0)
        
        variacao = ((v2 - v1) / abs(v1)) * 100
        return round(variacao, 1)
    except:
        return 0.0

def obter_cor_variacao(variacao_percentual):
    """Retorna a classe CSS baseada na variação percentual."""
    if variacao_percentual > 5.0:
        return "variation-positive"
    elif variacao_percentual < -5.0:
        return "variation-negative"
    else:
        return "variation-neutral"

def formatar_periodo_nome(arquivo_nome, periodo_num):
    """Formata nome do período baseado no nome do arquivo."""
    if not arquivo_nome:
        return f"Período {periodo_num}"
    
    # Remove extensão
    nome = arquivo_nome.lower().replace('.csv', '')
    
    # Tenta extrair mês/ano
    meses = {
        'jan': 'Jan', 'fev': 'Fev', 'mar': 'Mar', 'abr': 'Abr', 'mai': 'Mai', 'jun': 'Jun',
        'jul': 'Jul', 'ago': 'Ago', 'set': 'Set', 'out': 'Out', 'nov': 'Nov', 'dez': 'Dez'
    }
    
    for key, value in meses.items():
        if key in nome:
            # Tenta encontrar ano
            ano_match = re.search(r'20\d{2}', nome)
            ano = f"/{ano_match.group()}" if ano_match else ""
            return f"{value}{ano}"
    
    # Se não encontrar, usa nome do arquivo (limitado)
    return nome[:20]