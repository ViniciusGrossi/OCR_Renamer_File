import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Dashboard Kubota",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar a aparência
st.markdown("""
<style>
    /* Estilo geral */
    .main {
        padding-top: 1rem;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: #e8f4f8;
        text-align: center;
        font-size: 1.2rem;
        margin: 0;
    }
    
    /* Métricas cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3c72;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #6c757d;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Filtros header */
    .filter-header {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: 600;
    }
    
    /* Seções */
    .section-header {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2a5298;
        margin: 2rem 0 1rem 0;
    }
    
    .section-header h2 {
        color: #1e3c72;
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    /* Tabela */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* Remover padding do container principal */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def load_data(path):
    df = pd.read_excel(path)
    # Normalize column names: strip, uppercase, remove accents
    df.columns = (
        df.columns
          .str.strip()
          .str.upper()
          .str.normalize('NFKD')
          .str.encode('ascii', errors='ignore')
          .str.decode('ascii')
    )
    # Ensure proper types
    if 'PRECO' in df.columns:
        df['PRECO'] = pd.to_numeric(df['PRECO'], errors='coerce')
    return df

# Load dataset
data = load_data('Pecas_kubota_atualizado.xlsx')
df = data.copy()

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🔧 Dashboard de Peças Kubota</h1>
    <p>Sistema de Análise e Gestão de Estoque - Visualização Profissional</p>
</div>
""", unsafe_allow_html=True)

# Sidebar com estilo aprimorado
st.sidebar.markdown("""
<div class="filter-header">
    <h3>🎛️ Painel de Filtros</h3>
</div>
""", unsafe_allow_html=True)

# Search bar for Codigo, Descricao, or Referencia
search = st.sidebar.text_input('🔍 Pesquisar por Código, Descrição ou Referência', placeholder="Digite aqui...")
if search:
    mask_code = df['CODIGO'].astype(str).str.contains(search, case=False, na=False)
    mask_desc = df['DESCRICAO'].astype(str).str.contains(search, case=False, na=False) if 'DESCRICAO' in df.columns else False
    mask_ref  = df['REFERENCIA'].astype(str).str.contains(search, case=False, na=False) if 'REFERENCIA' in df.columns else False
    df = df[mask_code | mask_desc | mask_ref]

# Caixa filter
if 'CAIXA' in df.columns:
    with st.sidebar.expander("📦 Filtrar por Caixa", expanded=False):
        caixas = data['CAIXA'].unique()
        selecionados_caixa = st.multiselect("Selecione as Caixas", caixas, default=list(caixas), key='caixa')
    df = df[df['CAIXA'].isin(selecionados_caixa)]

# Subgrupo filter
if 'SUBGRUPO' in df.columns:
    with st.sidebar.expander("📊 Filtrar por Subgrupo", expanded=False):
        subgrupos = data['SUBGRUPO'].unique()
        selecionados_sub = st.multiselect("Selecione os Subgrupos", subgrupos, default=list(subgrupos), key='subgrupo')
    df = df[df['SUBGRUPO'].isin(selecionados_sub)]

# Preco filter
if 'PRECO' in df.columns:
    preco_min, preco_max = float(data['PRECO'].min() or 0), float(data['PRECO'].max() or 0)
    faixa = st.sidebar.slider('💰 Faixa de Preço', preco_min, preco_max, (preco_min, preco_max), format="R$ %.2f")
    df = df[df['PRECO'].between(faixa[0], faixa[1])]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(df):,}</div>
        <div class="metric-label">Total de Peças</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if 'PRECO' in df.columns:
        valor_total = df['PRECO_TOTAL'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">R$ {valor_total:,.2f}</div>
            <div class="metric-label">Valor Total</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    if 'PRECO' in df.columns:
        preco_medio = df['PRECO'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">R$ {preco_medio:.2f}</div>
            <div class="metric-label">Preço Médio</div>
        </div>
        """, unsafe_allow_html=True)

with col4:
    if 'SUBGRUPO' in df.columns:
        num_subgrupos = df['SUBGRUPO'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{num_subgrupos}</div>
            <div class="metric-label">Subgrupos</div>
        </div>
        """, unsafe_allow_html=True)

# Tabela de dados
st.markdown("""
<div class="section-header">
    <h2>📋 Dados Filtrados</h2>
</div>
""", unsafe_allow_html=True)

st.dataframe(df, use_container_width=True, height=400)

# Gráficos principais
st.markdown("""
<div class="section-header">
    <h2>📊 Análise Visual</h2>
</div>
""", unsafe_allow_html=True)

# Layout em duas colunas para os gráficos
col1, col2 = st.columns(2)

with col1:
    # Histograma de Preço
    if 'PRECO' in df.columns:
        fig_hist = px.histogram(
            df, x='PRECO', nbins=30, 
            title='Distribuição de Preços',
            color_discrete_sequence=['#2a5298']
        )
        fig_hist.update_layout(
            title_font_size=16,
            title_font_color='#1e3c72',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2c3e50'),
            showlegend=False
        )
        fig_hist.update_xaxes(title_text="Preço (R$)", title_font_color='#1e3c72')
        fig_hist.update_yaxes(title_text="Frequência", title_font_color='#1e3c72')
        st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    # Contagem de itens por Subgrupo
    if 'SUBGRUPO' in df.columns:
        df_count = df['SUBGRUPO'].value_counts().reset_index()
        df_count.columns = ['Subgrupo', 'Quantidade']
        fig_bar = px.bar(
            df_count, x='Subgrupo', y='Quantidade', 
            title='Quantidade por Subgrupo',
            color='Quantidade',
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(
            title_font_size=16,
            title_font_color='#1e3c72',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2c3e50'),
            showlegend=False
        )
        fig_bar.update_xaxes(title_text="Subgrupo", title_font_color='#1e3c72')
        fig_bar.update_yaxes(title_text="Quantidade", title_font_color='#1e3c72')
        st.plotly_chart(fig_bar, use_container_width=True)

# Segunda linha de gráficos
col3, col4 = st.columns(2)

with col3:
    # Box plot de preços por Subgrupo
    if 'SUBGRUPO' in df.columns and 'PRECO' in df.columns:
        fig_box = px.box(
            df, x='SUBGRUPO', y='PRECO', 
            title='Distribuição de Preços por Subgrupo',
            color='SUBGRUPO'
        )
        fig_box.update_layout(
            title_font_size=16,
            title_font_color='#1e3c72',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2c3e50'),
            showlegend=False
        )
        fig_box.update_xaxes(title_text="Subgrupo", title_font_color='#1e3c72')
        fig_box.update_yaxes(title_text="Preço (R$)", title_font_color='#1e3c72')
        st.plotly_chart(fig_box, use_container_width=True)

with col4:
    # Participação de valor total por Subgrupo (pizza)
    if 'SUBGRUPO' in df.columns and 'PRECO' in df.columns:
        df_val = data.groupby('SUBGRUPO')['PRECO'].sum().reset_index()
        df_val.columns = ['Subgrupo', 'ValorTotal']
        fig_pie = px.pie(
            df_val, names='Subgrupo', values='ValorTotal',
            title='Participação no Valor Total', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_layout(
            title_font_size=16,
            title_font_color='#1e3c72',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2c3e50')
        )
        fig_pie.update_traces(textinfo='percent+label', textfont_size=12)
        st.plotly_chart(fig_pie, use_container_width=True)

# Análises Adicionais
st.markdown("""
<div class="section-header">
    <h2>📈 Análises Detalhadas</h2>
</div>
""", unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    # Tabela de estatísticas descritivas de Preco
    if 'PRECO' in df.columns:
        st.subheader("📊 Estatísticas de Preço")
        stats = df['PRECO'].describe().reset_index()
        stats.columns = ['Estatística', 'Valor (R$)']
        stats['Valor (R$)'] = stats['Valor (R$)'].apply(lambda x: f"R$ {x:,.2f}")
        
        # Criar tabela estilizada
        stats_html = stats.to_html(index=False, escape=False, classes='table table-striped')
        st.markdown(stats_html, unsafe_allow_html=True)

with col6:
    # Preço Médio por Caixa
    if 'CAIXA' in df.columns and 'PRECO' in df.columns:
        st.subheader("📦 Preço Médio por Caixa")
        df_caixa = df.groupby('CAIXA')['PRECO'].mean().reset_index()
        df_caixa.columns = ['Caixa', 'PrecoMedio']
        fig_caixa = px.bar(
            df_caixa, x='Caixa', y='PrecoMedio', 
            title='Preço Médio por Caixa',
            color='PrecoMedio',
            color_continuous_scale='Viridis'
        )
        fig_caixa.update_layout(
            title_font_size=14,
            title_font_color='#1e3c72',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#2c3e50'),
            showlegend=False,
            height=400
        )
        fig_hist.update_xaxes(title_text="Preço (R$)", title_font_color='#1e3c72')
        fig_hist.update_yaxes(title_text="Frequência", title_font_color='#1e3c72')
        st.plotly_chart(fig_caixa, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 2rem 0;">
    <p>© 2024 Dashboard Kubota - Sistema de Gestão de Peças | Desenvolvido para Análise Profissional</p>
</div>
""", unsafe_allow_html=True)