import warnings
warnings.filterwarnings("ignore")

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine

# ─── Configuração da página ───────────────────────────────────────────────
st.set_page_config(
    page_title="Dengue no Brasil",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilo visual ────────────────────────────────────────────────────────
st.markdown("""
<style>
  .kpi {
    background: #1a1a2e;
    border-left: 4px solid #e94560;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 6px;
  }
  .kpi-label {
    color: #a0aec0;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: .06em;
  }
  .kpi-value {
    color: #f7fafc;
    font-size: 1.8rem;
    font-weight: 800;
  }
  .kpi-sub {
    color: #68d391;
    font-size: 0.75rem;
    margin-top: 2px;
  }
  .sec {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e94560;
    border-bottom: 2px solid #e94560;
    padding-bottom: 5px;
    margin: 20px 0 12px;
  }
</style>
""", unsafe_allow_html=True)

CORES = {
    "Norte": "#3182ce",
    "Nordeste": "#dd6b20",
    "Centro-Oeste": "#38a169",
    "Sudeste": "#e53e3e",
    "Sul": "#805ad5",
}

MESES = [
    "Jan","Fev","Mar","Abr","Mai","Jun",
    "Jul","Ago","Set","Out","Nov","Dez"
]

# ─── Carga dos dados ──────────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando dados…")
def carregar():

    base = os.path.dirname(__file__)

    caminho_csv = os.path.join(
        base,
        "dados",
        "simulacao_dengue_brasil.csv"
    )

    df = pd.read_csv(caminho_csv)

    df["data"] = pd.to_datetime(df["data"])
    df["municipio"] = df["municipio"].str.strip().str.title()
    df["regiao"] = df["regiao"].str.strip().str.title()
    df["uf"] = df["uf"].str.strip().str.upper()
    df["nivel_alerta"] = df["nivel_alerta"].str.strip().str.title()

    df["nome_mes"] = df["mes"].apply(
        lambda x: MESES[x - 1]
    )

    def estacao(m):
        if m in [12, 1, 2]:
            return "Verão"

        if m in [3, 4, 5]:
            return "Outono"

        if m in [6, 7, 8]:
            return "Inverno"

        return "Primavera"

    df["estacao"] = df["mes"].apply(estacao)

    df["taxa_let"] = np.where(
        df["casos_dengue"] > 0,
        df["obitos"] / df["casos_dengue"] * 100,
        0
    ).round(4)

    # ─── Cria pasta do banco ──────────────────────────────────────────────
    db_dir = os.path.join(base, "database")

    os.makedirs(db_dir, exist_ok=True)

    # ─── Caminho SQLite ───────────────────────────────────────────────────
    db = os.path.join(db_dir, "dengue.sqlite")

    engine = create_engine(
        f"sqlite:///{db}"
    )

    # ─── Salva tabela ─────────────────────────────────────────────────────
    df.to_sql(
        "dengue",
        engine,
        if_exists="replace",
        index=False
    )

    return df

# ─── Carregar dataframe ───────────────────────────────────────────────────
df_full = carregar()

# ─── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:

    st.title("🦟 Filtros")

    anos = sorted(df_full["ano"].unique())

    ano_sel = st.select_slider(
        "Período",
        options=anos,
        value=(min(anos), max(anos))
    )

# ─── Aplicar filtros ──────────────────────────────────────────────────────
df = df_full[
    df_full["ano"].between(ano_sel[0], ano_sel[1])
]

# ─── Título ───────────────────────────────────────────────────────────────
st.title("🦟 Evolução dos Casos de Dengue no Brasil")

st.caption("Projeto G2 · Dashboard Epidemiológico")

# ─── KPIs ─────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total de Casos",
        f"{df['casos_dengue'].sum():,.0f}"
    )

with col2:
    st.metric(
        "Total de Óbitos",
        f"{df['obitos'].sum():,.0f}"
    )

with col3:
    st.metric(
        "Internações",
        f"{df['internacoes'].sum():,.0f}"
    )

# ─── Evolução temporal ────────────────────────────────────────────────────
por_ano = df.groupby("ano")["casos_dengue"].sum().reset_index()

fig = px.line(
    por_ano,
    x="ano",
    y="casos_dengue",
    markers=True,
    title="Casos de Dengue por Ano"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ─── Tabela ───────────────────────────────────────────────────────────────
st.subheader("📋 Dados")

st.dataframe(
    df.head(100),
    use_container_width=True
)