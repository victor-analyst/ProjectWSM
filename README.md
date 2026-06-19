<div align="center">

![SALOG Banner](imagens/salog_logo.png)

# SALOG — Control Tower

**Monitoramento WMS em tempo real para Centros de Distribuição**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Plotly](https://img.shields.io/badge/Plotly-Charts-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)

*Expedições · Recebimentos · SLA de Separação · Performance do CD*

</div>

---

## 📌 Sobre o Projeto

A **SALOG** nasceu da convicção de que logística vai além de movimentar produtos. É sobre dados precisos e visibilidade total da operação — do recebimento à expedição — com indicadores que empoderam decisões em tempo real.

> 🟢 Um único cockpit para toda a operação do Centro de Distribuição.

---

## ✨ Funcionalidades

| Recurso | Descrição |
|---|---|
| 📡 **Tempo Real** | KPIs e SLA atualizados ao vivo, sem atraso |
| 🔐 **Autenticação** | Login seguro via Streamlit Secrets |
| 📊 **Dashboards** | Gráficos interativos com Plotly para cada área |
| 🗄️ **PostgreSQL** | Banco de dados robusto com conexão via pool |
| 🎨 **UI Premium** | Tema dark com neon verde e CSS customizado |
| 📦 **Multi-módulo** | 7 módulos independentes por área da operação |

---

## 🗂️ Módulos

```
01 🏠  Visão Geral    → visaogeral.py    Cockpit com KPIs consolidados do CD
02 📥  Recebimento   → recebimento.py   Notas fiscais e volumes recebidos
03 🚚  Expedição     → expedicao.py     Pedidos expedidos e SLA de separação
04 📦  Estoque       → estoque.py       SKUs, localizações e movimentações
05 🔍  Inventário    → inventario.py    Divergências, acuracidade e contagens
06 📈  Performance   → performance.py   Produtividade, eficiência e metas
07 🏢  Sobre Nós     → sobrenos.py      Página institucional da plataforma
```

---

## 🛠️ Tech Stack

- **[Python 3.x](https://python.org)** — Linguagem principal
- **[Streamlit](https://streamlit.io)** — Framework de interface web
- **[PostgreSQL](https://postgresql.org)** — Banco de dados relacional
- **[Plotly](https://plotly.com)** — Gráficos e visualizações interativas
- **[Pandas](https://pandas.pydata.org)** — Manipulação e análise de dados
- **CSS Avançado** — UI dark premium com animações customizadas

---

## 🚀 Como Rodar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/PROJECT_PY_v22.git
cd PROJECT_PY_v22
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure os secrets

Crie o arquivo `.streamlit/secrets.toml`:

```toml
[auth]
login  = "seu_usuario"
email  = "seu@email.com"
senha  = "sua_senha_segura"

[database]
host     = "localhost"
port     = "5432"
database = "salog_db"
user     = "postgres"
password = "sua_senha_db"
```

### 4. Execute

```bash
streamlit run app.py
```

Acesse em **http://localhost:8501** 🎉

---

## 📁 Estrutura de Arquivos

```
PROJECT_PY_v22/
│
├── app.py              ← Entrada principal, auth & roteamento
├── db.py               ← Conexão com PostgreSQL (pool)
├── visaogeral.py       ← Cockpit / Painel principal
├── recebimento.py      ← Módulo de recebimento
├── expedicao.py        ← Módulo de expedição
├── estoque.py          ← Módulo de estoque
├── inventario.py       ← Módulo de inventário
├── performance.py      ← Módulo de performance
├── sobrenos.py         ← Página institucional
├── requirements.txt    ← Dependências Python
├── imagens/            ← Assets visuais do CD
└── .streamlit/
    └── secrets.toml    ← Credenciais (não versionar!)
```

---

## ⚠️ Atenção

Nunca suba o arquivo `secrets.toml` para o GitHub. Adicione ao `.gitignore`:

```
.streamlit/secrets.toml
```

---

<div align="center">

**SALOG** · Control Tower · Centro de Distribuição · WMS

*Construído com 💚 em Python*

</div>
