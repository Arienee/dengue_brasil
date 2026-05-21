# 🦟 Dengue no Brasil — Projeto G2

> Dashboard interativo de análise epidemiológica da dengue no Brasil (2015–2024).

---

## 📁 Estrutura do projeto

```
dengue-brasil/
├── app.py                          ← Dashboard (Streamlit)
├── requirements.txt                ← Lista de bibliotecas
├── README.md                       ← Este arquivo
├── dados/
│   └── simulacao_dengue_brasil.csv ← Base de dados
├── database/
│   └── dengue.sqlite               ← Criado automaticamente
├── notebooks/
│   └── analise_dengue.ipynb        ← Notebook (Google Colab)
├── imagens/                        ← Pasta para prints
└── .streamlit/
    └── config.toml                 ← Tema visual
```

---

## 🚀 Como rodar o dashboard localmente (Windows)

**Pré-requisito:** ter Python instalado.  
Baixe em: https://www.python.org/downloads/ (marque "Add Python to PATH")

### Passo 1 — Instalar dependências
Abra o **Prompt de Comando** (`Win + R` → digite `cmd` → Enter) e cole:
```
pip install streamlit pandas numpy plotly sqlalchemy statsmodels
```

### Passo 2 — Entrar na pasta do projeto
```
cd C:\caminho\para\dengue-brasil
```

### Passo 3 — Rodar o dashboard
```
streamlit run app.py
```
O navegador abrirá automaticamente em `http://localhost:8501`

---

## 📓 Como usar o notebook no Google Colab

1. Acesse https://colab.research.google.com
2. Clique em **Arquivo → Fazer upload de notebook**
3. Selecione o arquivo `notebooks/analise_dengue.ipynb`
4. Execute a primeira célula — ela pedirá para fazer upload do CSV
5. Selecione `dados/simulacao_dengue_brasil.csv`
6. Execute todas as células com **Ctrl + F9**

---

## ☁️ Como publicar no GitHub e Streamlit Cloud

Veja o guia completo de publicação na documentação do projeto.

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| Python | Linguagem principal |
| Pandas | Análise de dados |
| Plotly | Gráficos interativos |
| Streamlit | Dashboard web |
| SQLAlchemy + SQLite | Banco de dados |
| NumPy | Cálculos numéricos |

---

> *Dados simulados para fins didáticos.*
