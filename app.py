import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.title("Dashboard de Indicadores Econômicos do Brasil")
st.write("Bem-vindo ao dashboard!")



def buscar_dados_bacen(codigo, data_inicio, data_fim):
    """Busca dados de uma série temporal do Banco Central"""
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
    params = {
        "formato": "json",
        "dataInicial": data_inicio,
        "dataFinal": data_fim
    }
    
    resposta = requests.get(url, params=params)
    
    if resposta.status_code == 200:
        dados = resposta.json()
        df = pd.DataFrame(dados)
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        return df
    else:
        st.error(f"Erro ao buscar dados da série {codigo}")
        return None
  # Dicionário com os indicadores disponíveis
indicadores = {
    "Taxa SELIC (% a.m.)": 432,
    "IPCA - Inflação (% a.m.)": 433,
    "PIB (% acumulado 4 trimestres)": 4389,
    "Taxa de Desocupação (%)": 24369
}

# Dicionário com os indicadores disponíveis
indicadores = {
    "Taxa SELIC (% a.m.)": 432,
    "IPCA - Inflação (% a.m.)": 433,
    "PIB (% acumulado 4 trimestres)": 4389,
    "Taxa de Desocupação (%)": 24369
}

# Interface interativa
st.sidebar.header("Configurações")

# Modo de visualização
modo = st.sidebar.radio(
    "Modo de visualização:",
    options=["Indicador único", "Comparar indicadores"]
)

col1, col2 = st.sidebar.columns(2)
with col1:
    data_inicio = st.sidebar.date_input("Data inicial", value=pd.to_datetime("2020-01-01"))
with col2:
    data_fim = st.sidebar.date_input("Data final", value=pd.to_datetime("2026-10-01"))

# Converter datas para formato da API
data_inicio_str = data_inicio.strftime("%d/%m/%Y")
data_fim_str = data_fim.strftime("%d/%m/%Y")

if modo == "Indicador único":
    indicador_escolhido = st.sidebar.selectbox(
        "Selecione o indicador:",
        options=list(indicadores.keys())
    )
    indicadores_selecionados = [indicador_escolhido]
else:
    indicadores_selecionados = st.sidebar.multiselect(
        "Selecione os indicadores para comparar:",
        options=list(indicadores.keys()),
        default=["Taxa SELIC (% a.m.)", "IPCA - Inflação (% a.m.)"]
    )

# Buscar dados de todos os indicadores selecionados
todos_dados = {}
for indicador in indicadores_selecionados:
    codigo = indicadores[indicador]
    dados = buscar_dados_bacen(codigo, data_inicio_str, data_fim_str)
    if dados is not None:
        todos_dados[indicador] = dados

# Criar gráfico comparativo
if todos_dados:
    st.subheader("Comparação de Indicadores")
    st.write(f"Período: {data_inicio_str} até {data_fim_str}")
    
    fig = px.line(title="Evolução dos Indicadores")
    
    for indicador, dados in todos_dados.items():
        fig.add_scatter(
            x=dados['data'],
            y=dados['valor'],
            name=indicador,
            mode='lines'
        )
    
    fig.update_xaxes(tickformat="%b %Y")
    fig.update_yaxes(title_text="Valor")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar tabela com dados
    with st.expander("Ver dados brutos"):
        for indicador, dados in todos_dados.items():
            st.write(f"**{indicador}:**")
            st.write(dados)

        # Análise de correlação (apenas quando há múltiplos indicadores)
            if len(todos_dados) >= 2:
              st.subheader("Análise de Correlação")
    st.write("Coeficiente de correlação entre os indicadores selecionados:")
    
    # Preparar dados para correlação
    dados_correlacao = {}
    for indicador, dados in todos_dados.items():
        df_temp = dados.set_index('data')['valor']
        df_temp.name = indicador
        dados_correlacao[indicador] = df_temp
    
    # Combinar todos os dados em um único DataFrame
    df_correlacao = pd.concat(dados_correlacao.values(), axis=1).dropna()
    
    if len(df_correlacao) > 1:
        # Calcular matriz de correlação
        correlacao = df_correlacao.corr()
        
        # Criar heatmap de correlação
        fig_corr = px.imshow(
            correlacao,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Matriz de Correlação",
            labels=dict(color="Correlação")
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Interpretar correlações
        st.write("**Interpretação:**")
        for i in range(len(correlacao.columns)):
            for j in range(i+1, len(correlacao.columns)):
                ind1 = correlacao.columns[i]
                ind2 = correlacao.columns[j]
                valor_corr = correlacao.iloc[i, j]
                
                if abs(valor_corr) >= 0.7:
                    intensidade = "forte"
                elif abs(valor_corr) >= 0.4:
                    intensidade = "moderada"
                else:
                    intensidade = "fraca"
                
                direcao = "positiva" if valor_corr > 0 else "negativa"
                
                st.write(f"- **{ind1}** e **{ind2}**: correlação {intensidade} {direcao} ({valor_corr:.2f})")