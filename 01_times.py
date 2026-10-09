
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Clubes",
    page_icon="⚽",
    layout="wide"
)

# Carregamento e tratamento dos dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv("Tabela_Clubes.csv")

    # Remove coluna de índice, se existir
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Converte idade com vírgula decimal para número
    df["Idade_Media"] = pd.to_numeric(
        df["Idade_Media"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # Separa gols feitos e gols sofridos
    gols = df["GolsF/S"].astype(str).str.split(":", expand=True)
    df["Gols_Feitos"] = pd.to_numeric(gols[0], errors="coerce")
    df["Gols_Sofridos"] = pd.to_numeric(gols[1], errors="coerce")

    return df


df = carregar_dados()

# -------------------------
# CABEÇALHO
# -------------------------
st.title("⚽ Dashboard de Clubes de Futebol")
st.markdown(
    "Explore o desempenho esportivo, financeiro e histórico dos clubes."
)

# -------------------------
# FILTROS LATERAIS
# -------------------------
st.sidebar.header("Filtros")

anos = sorted(df["Ano"].unique(), reverse=True)

ano_selecionado = st.sidebar.selectbox(
    "Selecione o ano",
    anos
)

clubes = sorted(df["Clubes"].dropna().unique())

clubes_selecionados = st.sidebar.multiselect(
    "Selecione os clubes",
    clubes,
    default=[]
)

# Filtra o ano
dados_ano = df[df["Ano"] == ano_selecionado].copy()

# Filtra os clubes quando houver seleção
if clubes_selecionados:
    dados = dados_ano[
        dados_ano["Clubes"].isin(clubes_selecionados)
    ].copy()
else:
    dados = dados_ano.copy()

if dados.empty:
    st.warning("Não existem dados para os filtros selecionados.")
    st.stop()

# -------------------------
# INDICADORES PRINCIPAIS
# -------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Clubes analisados",
    dados["Clubes"].nunique()
)

col2.metric(
    "Total de vitórias",
    int(dados["Vitorias"].sum())
)

col3.metric(
    "Gols marcados",
    int(dados["Gols_Feitos"].sum())
)

col4.metric(
    "Valor dos elencos",
    f"R$ {dados['Valor_total'].sum() / 1_000_000:.1f} mi"
)

st.divider()

# -------------------------
# GRÁFICO 1: CLASSIFICAÇÃO
# -------------------------
st.subheader("🏆 Classificação dos clubes")

classificacao = dados.sort_values("Pos.", ascending=True)

fig_classificacao = px.bar(
    classificacao,
    x="Pos.",
    y="Clubes",
    orientation="h",
    color="Pos.",
    color_continuous_scale="RdYlGn_r",
    hover_data=["Vitorias", "Derrotas", "Empates", "Saldo"],
    labels={
        "Pos.": "Posição no campeonato",
        "Clubes": "Clube"
    },
    title=f"Classificação — {ano_selecionado}"
)

# A primeira posição aparece no topo
fig_classificacao.update_yaxes(
    categoryorder="array",
    categoryarray=classificacao["Clubes"].tolist(),
    autorange="reversed"
)

fig_classificacao.update_layout(
    showlegend=False,
    coloraxis_showscale=False,
    height=max(400, len(classificacao) * 24)
)

st.plotly_chart(fig_classificacao, use_container_width=True)

# -------------------------
# GRÁFICO 2: VITÓRIAS,
# EMPATES E DERROTAS
# -------------------------
st.subheader("📊 Desempenho esportivo")

desempenho = dados.melt(
    id_vars=["Clubes"],
    value_vars=["Vitorias", "Empates", "Derrotas"],
    var_name="Resultado",
    value_name="Quantidade"
)

fig_desempenho = px.bar(
    desempenho,
    x="Clubes",
    y="Quantidade",
    color="Resultado",
    barmode="group",
    color_discrete_map={
        "Vitorias": "#2ecc71",
        "Empates": "#f1c40f",
        "Derrotas": "#e74c3c"
    },
    labels={
        "Clubes": "Clube",
        "Quantidade": "Partidas",
        "Resultado": "Resultado"
    }
)

st.plotly_chart(fig_desempenho, use_container_width=True)

# -------------------------
# GRÁFICO 3: VALOR DO ELENCO
# -------------------------
st.subheader("💰 Valor de mercado dos elencos")

fig_valor = px.scatter(
    dados,
    x="Valor_total",
    y="Pos.",
    size="Qtd_Jogadores",
    color="Clubes",
    hover_name="Clubes",
    hover_data=[
        "Idade_Media",
        "Estrangeiros",
        "Media_Valor"
    ],
    labels={
        "Valor_total": "Valor total do elenco (R$)",
        "Pos.": "Posição no campeonato",
        "Qtd_Jogadores": "Quantidade de jogadores"
    },
    title="Valor do elenco versus posição"
)

# Posição 1 no topo
fig_valor.update_yaxes(autorange="reversed")

st.plotly_chart(fig_valor, use_container_width=True)

# -------------------------
# GRÁFICO 4: EVOLUÇÃO HISTÓRICA
# -------------------------
st.subheader("📈 Evolução histórica")

clube_historico = st.selectbox(
    "Escolha um clube para analisar sua evolução",
    clubes,
    index=0
)

historico = df[
    df["Clubes"] == clube_historico
].sort_values("Ano")

if not historico.empty:
    fig_historico = go.Figure()

    fig_historico.add_trace(
        go.Scatter(
            x=historico["Ano"],
            y=historico["Pos."],
            mode="lines+markers",
            name="Posição",
            line=dict(width=3),
            hovertemplate=(
                "Ano: %{x}<br>"
                "Posição: %{y}<extra></extra>"
            )
        )
    )

    fig_historico.update_layout(
        title=f"Posição de {clube_historico} por temporada",
        xaxis_title="Ano",
        yaxis_title="Posição",
        height=400
    )

    fig_historico.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_historico, use_container_width=True)

# -------------------------
# TABELA DE DADOS
# -------------------------
with st.expander("Consultar tabela de dados"):
    st.dataframe(
        dados.sort_values("Pos."),
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Fonte: Tabela_Clubes.csv | Dashboard desenvolvido com Streamlit e Plotly."
)
