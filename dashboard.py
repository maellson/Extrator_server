import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Classificação de Documentos",
    page_icon="📊",
    layout="wide"
)

# Título do dashboard
st.title("📊 Dashboard de Classificação de Documentos")
st.markdown("---")

# Função para conectar ao banco de dados
def conectar_banco():
    """Conecta ao banco de dados SQLite"""
    try:
        conn = sqlite3.connect("classificacoes.db")
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

# Função para criar link de download/visualização de PDF
def create_pdf_link(file_path, file_name):
    """Cria um link para visualizar o PDF"""
    if os.path.exists(file_path):
        # Ler o arquivo PDF
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        
        # Converter para base64
        b64_pdf = base64.b64encode(pdf_data).decode()
        
        # Criar link de download
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{file_name}" target="_blank">📄 Visualizar PDF</a>'
        return href
    else:
        return "❌ Arquivo não encontrado"

# Função para exibir PDF inline
def display_pdf(file_path):
    """Exibe PDF inline usando iframe"""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        
        b64_pdf = base64.b64encode(pdf_data).decode()
        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{b64_pdf}" 
                width="100%" 
                height="800" 
                type="application/pdf">
        </iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error("Arquivo PDF não encontrado")

# Função para obter estatísticas do banco de dados
def obter_estatisticas():
    """Obtém estatísticas gerais do banco de dados"""
    conn = conectar_banco()
    if conn is None:
        return None
    
    try:
        # Total de classificações
        total_classificacoes = pd.read_sql_query("SELECT COUNT(*) as total FROM classificacoes", conn).iloc[0]['total']
        
        # Classificações por tipo
        classificacoes_tipo = pd.read_sql_query("""
            SELECT tipo_classificacao, COUNT(*) as quantidade 
            FROM classificacoes 
            GROUP BY tipo_classificacao
        """, conn)
        
        # Total de tokens
        tokens = pd.read_sql_query("""
            SELECT SUM(tokens_entrada) as entrada, SUM(tokens_saida) as saida 
            FROM classificacoes
        """, conn).iloc[0]
        
        # Índices de certeza
        indices_certeza = pd.read_sql_query("""
            SELECT AVG(indice_certeza) as media, 
                   MIN(indice_certeza) as minimo, 
                   MAX(indice_certeza) as maximo
            FROM classificacoes
        """, conn).iloc[0]
        
        conn.close()
        
        return {
            "total_classificacoes": total_classificacoes,
            "classificacoes_tipo": classificacoes_tipo,
            "tokens_entrada": tokens['entrada'] if tokens['entrada'] else 0,
            "tokens_saida": tokens['saida'] if tokens['saida'] else 0,
            "media_certeza": indices_certeza['media'] if indices_certeza['media'] else 0,
            "min_certeza": indices_certeza['minimo'] if indices_certeza['minimo'] else 0,
            "max_certeza": indices_certeza['maximo'] if indices_certeza['maximo'] else 0
        }
    except Exception as e:
        if conn:
            conn.close()
        st.error(f"Erro ao obter estatísticas: {str(e)}")
        return None

# Função para obter dados detalhados
def obter_dados_detalhados():
    """Obtém todos os dados de classificações"""
    conn = conectar_banco()
    if conn is None:
        return pd.DataFrame()
    
    try:
        df = pd.read_sql_query("""
            SELECT id, nome_arquivo, caminho_arquivo, tipo_classificacao, indice_certeza,
                   tokens_entrada, tokens_saida, data_processamento
            FROM classificacoes
            ORDER BY data_processamento DESC
        """, conn)
        conn.close()
        return df
    except Exception as e:
        if conn:
            conn.close()
        st.error(f"Erro ao obter dados detalhados: {str(e)}")
        return pd.DataFrame()

# Função para obter distribuição por faixa de certeza
def obter_distribuicao_certeza():
    """Obtém distribuição por faixa de certeza"""
    conn = conectar_banco()
    if conn is None:
        return pd.DataFrame()
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                CASE 
                    WHEN indice_certeza >= 0.9 THEN 'Alta (0.9-1.0)'
                    WHEN indice_certeza >= 0.7 THEN 'Média-Alta (0.7-0.9)'
                    WHEN indice_certeza >= 0.5 THEN 'Média (0.5-0.7)'
                    WHEN indice_certeza >= 0.3 THEN 'Baixa (0.3-0.5)'
                    ELSE 'Muito Baixa (0.0-0.3)'
                END as faixa_certeza,
                COUNT(*) as quantidade
            FROM classificacoes
            GROUP BY 
                CASE 
                    WHEN indice_certeza >= 0.9 THEN 'Alta (0.9-1.0)'
                    WHEN indice_certeza >= 0.7 THEN 'Média-Alta (0.7-0.9)'
                    WHEN indice_certeza >= 0.5 THEN 'Média (0.5-0.7)'
                    WHEN indice_certeza >= 0.3 THEN 'Baixa (0.3-0.5)'
                    ELSE 'Muito Baixa (0.0-0.3)'
                END
            ORDER BY quantidade DESC
        """, conn)
        conn.close()
        return df
    except Exception as e:
        if conn:
            conn.close()
        st.error(f"Erro ao obter distribuição de certeza: {str(e)}")
        return pd.DataFrame()

# Inicializar session state para controlar qual PDF está sendo visualizado
if 'pdf_selecionado' not in st.session_state:
    st.session_state.pdf_selecionado = None

# Obter estatísticas
estatisticas = obter_estatisticas()

if estatisticas is not None:
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Documentos Processados", 
            value=estatisticas["total_classificacoes"]
        )
    
    with col2:
        st.metric(
            label="Tokens de Entrada", 
            value=f"{estatisticas['tokens_entrada']:,}"
        )
    
    with col3:
        st.metric(
            label="Tokens de Saída", 
            value=f"{estatisticas['tokens_saida']:,}"
        )
    
    with col4:
        st.metric(
            label="Média de Certeza", 
            value=f"{estatisticas['media_certeza']:.2f}"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    # Gráfico de distribuição por tipo
    with col1:
        st.subheader("Distribuição por Tipo de Documento")
        if not estatisticas["classificacoes_tipo"].empty:
            fig_tipo = px.pie(
                estatisticas["classificacoes_tipo"], 
                values='quantidade', 
                names='tipo_classificacao',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            st.plotly_chart(fig_tipo, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para exibir")
    
    # Gráfico de distribuição por faixa de certeza
    with col2:
        st.subheader("Distribuição por Faixa de Certeza")
        distribuicao_certeza = obter_distribuicao_certeza()
        if not distribuicao_certeza.empty:
            fig_certeza = px.bar(
                distribuicao_certeza, 
                x='faixa_certeza', 
                y='quantidade',
                color='faixa_certeza',
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig_certeza.update_layout(xaxis_title="Faixa de Certeza", yaxis_title="Quantidade")
            st.plotly_chart(fig_certeza, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para exibir")
    
    st.markdown("---")
    
    # Dados detalhados
    st.subheader("Dados Detalhados de Classificações")
    
    # Filtros
    df_detalhado = obter_dados_detalhados()
    
    if not df_detalhado.empty:
        # Filtros na barra lateral
        st.sidebar.header("Filtros")
        
        # Filtro por tipo de documento
        tipos_disponiveis = df_detalhado['tipo_classificacao'].unique().tolist()
        tipos_selecionados = st.sidebar.multiselect(
            "Tipo de Documento", 
            options=tipos_disponiveis,
            default=tipos_disponiveis
        )
        
        # Filtro por faixa de certeza
        faixa_certeza = st.sidebar.slider(
            "Faixa de Certeza",
            min_value=0.0,
            max_value=1.0,
            value=(0.0, 1.0),
            step=0.1
        )
        
        # Aplicar filtros
        df_filtrado = df_detalhado[
            (df_detalhado['tipo_classificacao'].isin(tipos_selecionados)) &
            (df_detalhado['indice_certeza'] >= faixa_certeza[0]) &
            (df_detalhado['indice_certeza'] <= faixa_certeza[1])
        ]
        
        # Mostrar dados filtrados com interface melhorada
        st.subheader("Dados Filtrados")
        if not df_filtrado.empty:
            
            # Criar interface tabular interativa
            for idx, row in df_filtrado.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{row['nome_arquivo']}**")
                    
                    with col2:
                        # Badge colorido para o tipo
                        tipo_colors = {
                            'voucher': '#1f77b4',
                            'boleto': '#ff7f0e', 
                            'nota_fiscal': '#2ca02c',
                            'descarte': '#d62728'
                        }
                        color = tipo_colors.get(row['tipo_classificacao'], '#7f7f7f')
                        st.markdown(f'<span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{row["tipo_classificacao"]}</span>', unsafe_allow_html=True)
                    
                    with col3:
                        st.write(f"**{row['indice_certeza']:.2f}**")
                    
                    with col4:
                        st.write(f"{row['tokens_entrada']}")
                    
                    with col5:
                        st.write(f"{row['tokens_saida']}")
                    
                    with col6:
                        # Botão para visualizar PDF
                        if st.button("👁️ Ver", key=f"view_{row['id']}", help="Visualizar PDF"):
                            st.session_state.pdf_selecionado = row['caminho_arquivo']
                    
                    st.divider()
            
            # Seção de visualização de PDF
            if st.session_state.pdf_selecionado:
                st.markdown("---")
                st.subheader("📄 Visualizador de PDF")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("❌ Fechar Visualizador"):
                        st.session_state.pdf_selecionado = None
                        st.rerun()
                
                with col2:
                    st.write(f"**Arquivo:** {os.path.basename(st.session_state.pdf_selecionado)}")
                
                # Exibir PDF
                display_pdf(st.session_state.pdf_selecionado)
        
        else:
            st.info("Nenhum dado disponível para exibir")
        
        # Estatísticas dos dados filtrados
        st.subheader("Estatísticas dos Dados Filtrados")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Documentos Filtrados", 
                value=len(df_filtrado)
            )
        
        with col2:
            if len(df_filtrado) > 0:
                st.metric(
                    label="Média de Certeza", 
                    value=f"{df_filtrado['indice_certeza'].mean():.2f}"
                )
            else:
                st.metric(label="Média de Certeza", value="0.00")
        
        with col3:
            if len(df_filtrado) > 0:
                st.metric(
                    label="Total de Tokens", 
                    value=f"{df_filtrado['tokens_entrada'].sum() + df_filtrado['tokens_saida'].sum():,}"
                )
            else:
                st.metric(label="Total de Tokens", value="0")
    else:
        st.info("Nenhum dado disponível para exibir")
else:
    st.error("Não foi possível conectar ao banco de dados. Verifique se o arquivo 'classificacoes.db' existe e contém dados.")

# Informações adicionais
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Dashboard de Classificação de Documentos - Desenvolvido com Streamlit</p>
    <p>Para atualizar os dados, execute o processo de classificação e recarregue esta página</p>
</div>
""", unsafe_allow_html=True)