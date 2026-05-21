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
  .kpi-label { color: #a0aec0; font-size: 0.78rem;
               text-transform: uppercase; letter-spacing: .06em; }
  .kpi-value { color: #f7fafc; font-size: 1.8rem; font-weight: 800; }
  .kpi-sub   { color: #68d391; font-size: 0.75rem; margin-top: 2px; }
  .sec { font-size: 1.1rem; font-weight: 700; color: #e94560;
         border-bottom: 2px solid #e94560;
         padding-bottom: 5px; margin: 20px 0 12px; }
  .info-box  { background:#ebf8ff; border-left:4px solid #3182ce;
               border-radius:6px; padding:10px 14px;
               font-size:.88rem; color:#1a365d; margin:8px 0; }
  .alert-box { background:#fff5f5; border-left:4px solid #e53e3e;
               border-radius:6px; padding:10px 14px;
               font-size:.88rem; color:#742a2a; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

CORES = {
    "Norte": "#3182ce", "Nordeste": "#dd6b20",
    "Centro-Oeste": "#38a169", "Sudeste": "#e53e3e", "Sul": "#805ad5",
}
CORES_ALERTA = {"Baixo": "#38a169", "Medio": "#dd6b20", "Alto": "#e53e3e"}
MESES = ["Jan","Fev","Mar","Abr","Mai","Jun",
         "Jul","Ago","Set","Out","Nov","Dez"]

# ─── Carga dos dados ──────────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando dados...")
def carregar():
    base = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(base, "dados", "simulacao_dengue_brasil.csv"))

    df["data"]         = pd.to_datetime(df["data"])
    df["municipio"]    = df["municipio"].str.strip().str.title()
    df["regiao"]       = df["regiao"].str.strip().str.title()
    df["uf"]           = df["uf"].str.strip().str.upper()
    df["nivel_alerta"] = df["nivel_alerta"].str.strip().str.title()
    df["nome_mes"]     = df["mes"].apply(lambda x: MESES[x - 1])

    def estacao(m):
        if m in [12,1,2]:  return "Verao"
        if m in [3,4,5]:   return "Outono"
        if m in [6,7,8]:   return "Inverno"
        return "Primavera"
    df["estacao"] = df["mes"].apply(estacao)
    df["taxa_let"] = np.where(df["casos_dengue"] > 0,
                              df["obitos"] / df["casos_dengue"] * 100, 0).round(4)

    # SQLite em memoria (funciona no Streamlit Cloud)
    engine = create_engine("sqlite:///:memory:", echo=False)
    df.to_sql("dengue", engine, if_exists="replace", index=False)

    return df

df_full = carregar()

# ─── Sidebar filtros ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Filtros")
    st.markdown("---")

    anos = sorted(df_full["ano"].unique())
    ano_sel = st.select_slider("Periodo", options=anos,
                                value=(min(anos), max(anos)))

    regioes = sorted(df_full["regiao"].unique())
    reg_sel = st.multiselect("Regiao", regioes, default=regioes)

    ufs = sorted(df_full[df_full["regiao"].isin(reg_sel)]["uf"].unique())
    uf_sel = st.multiselect("Estado (UF)", ufs, default=ufs)

    muns = sorted(df_full[df_full["uf"].isin(uf_sel)]["municipio"].unique())
    mun_sel = st.multiselect("Municipio", muns, default=muns)

    alertas = sorted(df_full["nivel_alerta"].unique())
    alert_sel = st.multiselect("Nivel de Alerta", alertas, default=alertas)

    meses_num = list(range(1, 13))
    mes_sel = st.multiselect("Meses", meses_num, default=meses_num,
                              format_func=lambda x: MESES[x - 1])

    st.markdown("---")
    st.caption("Projeto G2 - Dengue Brasil")

# ─── Aplicar filtros ──────────────────────────────────────────────────────
df = df_full[
    df_full["ano"].between(ano_sel[0], ano_sel[1]) &
    df_full["mes"].isin(mes_sel) &
    df_full["regiao"].isin(reg_sel) &
    df_full["uf"].isin(uf_sel) &
    df_full["municipio"].isin(mun_sel) &
    df_full["nivel_alerta"].isin(alert_sel)
].copy()

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados. Ajuste os filtros.")
    st.stop()

# ─── Cabecalho ────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='text-align:center;color:#e94560;font-size:2rem;margin-bottom:2px'>
  Evolucao dos Casos de Dengue no Brasil
</h1>
<p style='text-align:center;color:#718096;margin-top:0'>
  Analise epidemiologica - 2015 a 2024 - Projeto G2
</p>
<hr style='border-color:#2d3748;margin:10px 0 20px'>
""", unsafe_allow_html=True)

# ─── KPIs ─────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">Indicadores Principais</div>',
            unsafe_allow_html=True)

total_casos  = df["casos_dengue"].sum()
total_ob     = df["obitos"].sum()
total_int    = df["internacoes"].sum()
media_men    = df.groupby(["ano","mes"])["casos_dengue"].sum().mean()
inc_media    = df["incidencia_100k"].mean()
uf_top       = df.groupby("uf")["casos_dengue"].sum().idxmax()
mun_top      = df.groupby("municipio")["incidencia_100k"].mean().idxmax()
mun_inc      = df.groupby("municipio")["incidencia_100k"].mean().max()
ano_pico     = df.groupby("ano")["casos_dengue"].sum().idxmax()
ano_pico_v   = df.groupby("ano")["casos_dengue"].sum().max()

def kpi(col, label, val, sub=""):
    col.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{val}</div>'
        f'{"<div class=kpi-sub>" + sub + "</div>" if sub else ""}</div>',
        unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
c5,c6,c7,c8 = st.columns(4)
kpi(c1, "Total de Casos",       f"{total_casos:,.0f}")
kpi(c2, "Total de Obitos",      f"{total_ob:,.0f}")
kpi(c3, "Total de Internacoes", f"{total_int:,.0f}")
kpi(c4, "Media Mensal",         f"{media_men:,.0f}", "casos/mes")
kpi(c5, "Incidencia Media",     f"{inc_media:.1f}",  "por 100k hab.")
kpi(c6, "Estado Mais Afetado",  uf_top)
kpi(c7, "Municipio Critico",    mun_top, f"{mun_inc:.1f}/100k")
kpi(c8, "Ano de Pico",          str(ano_pico), f"{ano_pico_v:,.0f} casos")

# ─── Evolucao temporal ────────────────────────────────────────────────────
st.markdown('<div class="sec">Evolucao Temporal</div>',
            unsafe_allow_html=True)

por_ano = df.groupby("ano").agg(
    casos=("casos_dengue","sum"),
    obitos=("obitos","sum"),
    internacoes=("internacoes","sum"),
    incidencia=("incidencia_100k","mean"),
).reset_index()

col_a, col_b = st.columns([3,2])
with col_a:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=por_ano["ano"], y=por_ano["casos"],
                         name="Casos", marker_color="#e53e3e", opacity=.75),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=por_ano["ano"], y=por_ano["incidencia"],
                             name="Incidencia/100k", mode="lines+markers",
                             line=dict(color="#f6e05e", width=2.5),
                             marker=dict(size=7)),
                  secondary_y=True)
    fig.update_layout(title="Casos e Incidencia por Ano",
                      hovermode="x unified",
                      plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f7fafc",
                      legend=dict(orientation="h", y=-0.22))
    fig.update_yaxes(gridcolor="#2d3748", secondary_y=False)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig2 = px.bar(por_ano, x="ano", y=["obitos","internacoes"],
                  barmode="group", title="Obitos e Internacoes por Ano",
                  color_discrete_map={"obitos":"#fc8181","internacoes":"#f6ad55"},
                  labels={"value":"Qtd","ano":"Ano","variable":""})
    fig2.update_layout(hovermode="x unified",
                       plot_bgcolor="rgba(0,0,0,0)",
                       paper_bgcolor="rgba(0,0,0,0)",
                       font_color="#f7fafc",
                       legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig2, use_container_width=True)

cresc = por_ano["casos"].pct_change().mean() * 100
st.markdown(
    f'<div class="info-box">Ano de pico: <b>{ano_pico}</b> com '
    f'<b>{ano_pico_v:,.0f} casos</b>. Crescimento medio anual: '
    f'<b>{cresc:+.1f}%</b> no periodo selecionado.</div>',
    unsafe_allow_html=True)

# ─── Comparacao regional ──────────────────────────────────────────────────
st.markdown('<div class="sec">Comparacao Regional</div>',
            unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Por Regiao", "Por Estado (UF)"])

with tab1:
    por_reg = (df.groupby("regiao")
               .agg(casos=("casos_dengue","sum"),
                    incidencia=("incidencia_100k","mean"))
               .reset_index()
               .sort_values("casos", ascending=False))

    ca, cb = st.columns(2)
    with ca:
        fig = px.bar(por_reg, x="regiao", y="casos", color="regiao",
                     color_discrete_map=CORES, text_auto=".3s",
                     title="Total de Casos por Regiao",
                     labels={"casos":"Casos","regiao":"Regiao"})
        fig.update_layout(showlegend=False,
                          plot_bgcolor="rgba(0,0,0,0)",
                          paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f7fafc")
        st.plotly_chart(fig, use_container_width=True)
    with cb:
        fig = px.pie(por_reg, names="regiao", values="casos",
                     color="regiao", color_discrete_map=CORES,
                     hole=.4, title="Distribuicao % por Regiao")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                          paper_bgcolor="rgba(0,0,0,0)",
                          font_color="#f7fafc")
        st.plotly_chart(fig, use_container_width=True)

    por_reg_ano = df.groupby(["ano","regiao"])["casos_dengue"].sum().reset_index()
    fig = px.line(por_reg_ano, x="ano", y="casos_dengue", color="regiao",
                  markers=True, color_discrete_map=CORES,
                  title="Evolucao por Regiao ao Longo do Tempo",
                  labels={"casos_dengue":"Casos","ano":"Ano","regiao":"Regiao"})
    fig.update_layout(hovermode="x unified",
                      plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f7fafc")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    por_uf = (df.groupby(["uf","regiao"])
              .agg(casos=("casos_dengue","sum"),
                   incidencia=("incidencia_100k","mean"))
              .reset_index()
              .sort_values("casos", ascending=False))
    fig = px.bar(por_uf, x="uf", y="casos", color="regiao",
                 color_discrete_map=CORES, text_auto=".3s",
                 title="Total de Casos por Estado (UF)",
                 labels={"casos":"Casos","uf":"UF","regiao":"Regiao"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f7fafc")
    st.plotly_chart(fig, use_container_width=True)

# ─── Sazonalidade ─────────────────────────────────────────────────────────
st.markdown('<div class="sec">Sazonalidade</div>',
            unsafe_allow_html=True)

pivot = (df.groupby(["ano","mes"])["casos_dengue"]
         .sum().unstack("mes").fillna(0))
pivot.columns = [MESES[c-1] for c in pivot.columns]

fig = px.imshow(pivot, color_continuous_scale="YlOrRd",
                text_auto=".3s",
                title="Heatmap - Casos por Mes e Ano",
                labels=dict(x="Mes", y="Ano", color="Casos"),
                aspect="auto")
fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                  paper_bgcolor="rgba(0,0,0,0)",
                  font_color="#f7fafc")
st.plotly_chart(fig, use_container_width=True)

sazon = df.groupby("mes")["casos_dengue"].mean().reset_index()
sazon["nome_mes"] = sazon["mes"].apply(lambda x: MESES[x-1])
mes_pico = sazon.loc[sazon["casos_dengue"].idxmax(), "nome_mes"]

fig2 = px.bar(sazon, x="nome_mes", y="casos_dengue",
              color="casos_dengue", color_continuous_scale="YlOrRd",
              title="Media Historica Mensal de Casos",
              labels={"casos_dengue":"Media de Casos","nome_mes":"Mes"},
              category_orders={"nome_mes": MESES})
fig2.update_layout(coloraxis_showscale=False,
                   plot_bgcolor="rgba(0,0,0,0)",
                   paper_bgcolor="rgba(0,0,0,0)",
                   font_color="#f7fafc")
st.plotly_chart(fig2, use_container_width=True)

st.markdown(
    f'<div class="alert-box">Mes historicamente mais critico: '
    f'<b>{mes_pico}</b>. Os primeiros meses do ano (jan-abr) concentram '
    f'maior carga de casos - periodo de verao e chuvas intensas.</div>',
    unsafe_allow_html=True)

# ─── Chuva x Dengue ───────────────────────────────────────────────────────
st.markdown('<div class="sec">Correlacao: Chuva x Dengue</div>',
            unsafe_allow_html=True)

col_c, col_d = st.columns(2)

with col_c:
    fig = px.scatter(df, x="chuva_mm", y="casos_dengue", color="regiao",
                     trendline="ols", opacity=.5,
                     color_discrete_map=CORES,
                     title="Dispersao: Chuva x Casos",
                     labels={"chuva_mm":"Chuva (mm)",
                             "casos_dengue":"Casos","regiao":"Regiao"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f7fafc")
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    med = df.groupby("mes").agg(
        chuva=("chuva_mm","mean"),
        casos=("casos_dengue","mean")).reset_index()
    med["nome_mes"] = med["mes"].apply(lambda x: MESES[x-1])

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Bar(x=med["nome_mes"], y=med["chuva"],
                          name="Chuva (mm)", marker_color="#4299e1", opacity=.7),
                   secondary_y=False)
    fig2.add_trace(go.Scatter(x=med["nome_mes"], y=med["casos"],
                              name="Casos medios", mode="lines+markers",
                              line=dict(color="#fc8181", width=2.5)),
                   secondary_y=True)
    fig2.update_layout(title="Chuva e Casos - Medias Mensais",
                       hovermode="x unified",
                       plot_bgcolor="rgba(0,0,0,0)",
                       paper_bgcolor="rgba(0,0,0,0)",
                       font_color="#f7fafc",
                       legend=dict(orientation="h", y=-0.25),
                       xaxis=dict(categoryorder="array",
                                  categoryarray=MESES))
    fig2.update_yaxes(gridcolor="#2d3748", secondary_y=False)
    st.plotly_chart(fig2, use_container_width=True)

r = df[["chuva_mm","casos_dengue"]].corr().iloc[0,1]
forca = "forte" if abs(r) > .6 else "moderada" if abs(r) > .3 else "fraca"
st.markdown(
    f'<div class="info-box">Correlacao de Pearson: <b>r = {r:.3f}</b> - '
    f'correlacao <b>{forca}</b> entre chuva e casos de dengue.</div>',
    unsafe_allow_html=True)

# ─── Ranking de municipios ────────────────────────────────────────────────
st.markdown('<div class="sec">Ranking de Municipios</div>',
            unsafe_allow_html=True)

rank = (df.groupby(["municipio","uf","regiao"])
        .agg(casos=("casos_dengue","sum"),
             incidencia=("incidencia_100k","mean"),
             obitos=("obitos","sum"))
        .reset_index()
        .sort_values("incidencia", ascending=False)
        .head(15))
rank["label"] = rank["municipio"] + " / " + rank["uf"]

fig = px.bar(rank, x="incidencia", y="label", orientation="h",
             color="regiao", color_discrete_map=CORES,
             text_auto=".1f",
             title="Top 15 Municipios - Incidencia Media por 100k hab.",
             labels={"incidencia":"Incidencia/100k","label":"Municipio","regiao":"Regiao"})
fig.update_layout(yaxis=dict(autorange="reversed"),
                  plot_bgcolor="rgba(0,0,0,0)",
                  paper_bgcolor="rgba(0,0,0,0)",
                  font_color="#f7fafc")
st.plotly_chart(fig, use_container_width=True)

# ─── Nivel de alerta ──────────────────────────────────────────────────────
st.markdown('<div class="sec">Nivel de Alerta Epidemiologico</div>',
            unsafe_allow_html=True)

ce, cf = st.columns(2)
with ce:
    al = df.groupby("nivel_alerta")["casos_dengue"].sum().reset_index()
    fig = px.pie(al, names="nivel_alerta", values="casos_dengue",
                 color="nivel_alerta", color_discrete_map=CORES_ALERTA,
                 hole=.4, title="Casos por Nivel de Alerta")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#f7fafc")
    st.plotly_chart(fig, use_container_width=True)

with cf:
    al2 = df.groupby(["regiao","nivel_alerta"])["casos_dengue"].sum().reset_index()
    fig2 = px.bar(al2, x="regiao", y="casos_dengue", color="nivel_alerta",
                  barmode="stack", color_discrete_map=CORES_ALERTA,
                  title="Alerta por Regiao",
                  labels={"casos_dengue":"Casos","regiao":"Regiao",
                          "nivel_alerta":"Alerta"})
    fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                       paper_bgcolor="rgba(0,0,0,0)",
                       font_color="#f7fafc")
    st.plotly_chart(fig2, use_container_width=True)

# ─── Tabela dinamica ──────────────────────────────────────────────────────
st.markdown('<div class="sec">Tabela Dinamica</div>',
            unsafe_allow_html=True)

c1t, c2t = st.columns(2)
with c1t:
    idx = st.selectbox("Linhas", ["uf","regiao","municipio","ano","nivel_alerta"])
with c2t:
    col = st.selectbox("Colunas", ["ano","mes","regiao","nivel_alerta"])
val = st.selectbox("Valor", ["casos_dengue","internacoes","obitos","incidencia_100k"])

try:
    piv = pd.pivot_table(df, index=idx, columns=col, values=val,
                         aggfunc="sum", fill_value=0, margins=True)
    piv.columns = [str(c) for c in piv.columns]
    st.dataframe(piv.style.format("{:,.0f}")
                 .background_gradient(cmap="Reds", axis=None),
                 use_container_width=True)
except Exception as e:
    st.warning(f"Nao foi possivel gerar: {e}")

# ─── Conclusao executiva ──────────────────────────────────────────────────
st.markdown('<div class="sec">Conclusao Executiva</div>',
            unsafe_allow_html=True)

reg_lider = df.groupby("regiao")["casos_dengue"].sum().idxmax()

st.markdown(f"""
<div style="background:#1a1a2e;border-radius:10px;padding:22px 26px;
            line-height:1.85;color:#e2e8f0">

<h4 style="color:#e94560;margin-top:0">Principais Achados</h4>

<b>Evolucao:</b> {total_casos:,.0f} casos registrados no periodo.
Crescimento medio anual de <b>{cresc:+.1f}%</b>.
Pico em <b>{ano_pico}</b> ({ano_pico_v:,.0f} casos).<br><br>

<b>Sazonalidade:</b> Meses criticos entre <b>janeiro e abril</b> (verao/outono),
coincidindo com chuvas intensas.
Mes mais critico: <b>{mes_pico}</b>.<br><br>

<b>Regional:</b> Regiao <b>{reg_lider}</b> concentrou mais casos.
Estado mais afetado: <b>{uf_top}</b>.<br><br>

<b>Chuva:</b> Correlacao r = {r:.3f} ({forca}).
Alertas climaticos podem antecipar surtos em 2-4 semanas.<br><br>

<b>Municipio critico:</b> <b>{mun_top}</b> -
{mun_inc:.1f} casos por 100 mil habitantes.<br><br>

<h4 style="color:#68d391;margin-bottom:6px">Recomendacoes</h4>
<ul>
  <li>Campanhas de eliminacao de focos em <b>outubro-dezembro</b></li>
  <li>Reforco hospitalar em <b>janeiro-abril</b></li>
  <li>Vigilancia intensiva nos municipios criticos</li>
  <li>Alertas climaticos integrados com previsao de chuvas</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Projeto G2 - Dengue Brasil - Dados simulados para fins didaticos")
