import streamlit as st
import datetime
import re
import base64
from pathlib import Path

@st.cache_resource(show_spinner=False)
def _logo_b64():
    p = Path(__file__).parent / "imagens" / "salog_logo.png"
    return base64.b64encode(p.read_bytes()).decode()

LOGO_B64 = _logo_b64()

# =========================
# ESTADO (precisa vir antes do set_page_config para decidir o sidebar)
# =========================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Visão Geral"
if "pwd_buffer" not in st.session_state:
    st.session_state.pwd_buffer = ""

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="SALOG — Control Tower",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.autenticado else "collapsed",
)

# Credenciais carregadas dos secrets
try:
    AUTH_LOGIN = st.secrets["auth"]["login"]
    AUTH_EMAIL = st.secrets["auth"]["email"]
    AUTH_SENHA = st.secrets["auth"]["senha"]
except Exception:
    AUTH_LOGIN = AUTH_EMAIL = AUTH_SENHA = None

# =========================
# ROTEAMENTO PÓS-LOGIN
# (executado ANTES do CSS pesado do login, para preservar o layout
#  original das páginas internas e o sidebar nativo do Streamlit)
# =========================
if st.session_state.autenticado:
    import visaogeral, recebimento, expedicao, performance, sobrenos, estoque, inventario

    # CSS para manter o tema verde/escuro nas páginas internas e no sidebar
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    :root {
        --neon: #00C22D;
        --neon-soft: #00E84D;
        --bg-1: #05070A;
        --bg-2: #0D1117;
        --border: rgba(0, 194, 45, 0.18);
        --text: #E6F0EA;
        --muted: #6B7A8F;
    }
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        color: var(--text);
    }
    /* Fundo com gradientes verdes */
    .stApp {
        background:
            radial-gradient(ellipse at top, rgba(0,194,45,0.18), transparent 55%),
            radial-gradient(circle at 20% 80%, rgba(0,194,45,0.10), transparent 40%),
            linear-gradient(180deg, #05070A 0%, #0D1117 100%) !important;
        background-attachment: fixed !important;
    }
    /* Sidebar verde/escuro */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(5,7,10,0.95), rgba(13,17,23,0.95)) !important;
        border-right: 1px solid var(--border) !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    [data-testid="stSidebar"] h3 {
        color: #fff !important;
        font-weight: 800 !important;
        letter-spacing: 0.25em !important;
    }
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--neon) !important;
        letter-spacing: 0.3em !important;
        font-size: 10px !important;
    }
    /* Radio de navegação */
    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: rgba(13,24,37,0.5);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        border-color: rgba(0,194,45,0.5);
        background: rgba(0,194,45,0.06);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"],
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: rgba(0,194,45,0.12) !important;
        border-color: var(--neon) !important;
        box-shadow: 0 0 20px rgba(0,194,45,0.25);
    }
    /* Botão Sair no sidebar */
    [data-testid="stSidebar"] .stButton > button {
        background: var(--neon) !important;
        color: #05070A !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(0,194,45,0.3);
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        filter: brightness(1.05);
        box-shadow: 0 0 40px rgba(0,194,45,0.5);
    }
    /* Esconder header padrão */
    [data-testid="stHeader"] { background: transparent !important; }
    /* ===== Loader temático ao trocar de página ===== */
    .salog-loader-overlay {
        position: fixed;
        inset: 0;
        background: radial-gradient(ellipse at center, rgba(5,7,10,0.92), rgba(5,7,10,0.98));
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(8px);
        animation: salog-fade-in 0.25s ease-out;
    }
    @keyframes salog-fade-in {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    .salog-loader-ring {
        width: 84px; height: 84px;
        border-radius: 50%;
        border: 3px solid rgba(0,194,45,0.15);
        border-top-color: #00C22D;
        border-right-color: #00E84D;
        animation: salog-spin 0.9s linear infinite;
        box-shadow: 0 0 40px rgba(0,194,45,0.45), inset 0 0 20px rgba(0,194,45,0.15);
    }
    @keyframes salog-spin {
        to { transform: rotate(360deg); }
    }
    .salog-loader-text {
        margin-top: 22px;
        font-family: 'JetBrains Mono', monospace;
        color: #00E84D;
        letter-spacing: 0.35em;
        font-size: 12px;
        text-transform: uppercase;
        animation: salog-pulse 1.2s ease-in-out infinite;
    }
    .salog-loader-sub {
        margin-top: 8px;
        font-family: 'Inter', sans-serif;
        color: #6B7A8F;
        font-size: 11px;
        letter-spacing: 0.15em;
    }
    @keyframes salog-pulse {
        0%, 100% { opacity: 0.55; }
        50%      { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

    PAGINAS = {
        "Visão Geral": visaogeral.show,
        "Recebimento": recebimento.show,
        "Expedição":   expedicao.show,
        "Performance": performance.show,
        "Sobre Nós":   sobrenos.show,
        "Estoque": estoque.show,
        "Inventário": inventario.show
    }

    def _on_nav_change():
        st.session_state.pagina_atual = st.session_state._nav_radio

    with st.sidebar:
        st.markdown(
            f'<img src="data:image/png;base64,{LOGO_B64}" style="width:130px; margin-bottom:8px; display:block;">',
            unsafe_allow_html=True,
        )
        st.caption("CONTROL TOWER")
        paginas_lista = list(PAGINAS.keys())
        idx_atual = paginas_lista.index(st.session_state.pagina_atual) \
            if st.session_state.pagina_atual in paginas_lista else 0
        st.radio(
            "Navegação",
            paginas_lista,
            index=idx_atual,
            key="_nav_radio",
            on_change=_on_nav_change,
            label_visibility="collapsed",
        )
        escolha = st.session_state.pagina_atual
        st.markdown("---")
        st.caption(f"Usuário: **{AUTH_LOGIN}**")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()

    # Placeholder do loader: aparece imediatamente, some quando a página termina de renderizar
    loader_slot = st.empty()
    loader_slot.markdown(
        f"""
        <div class="salog-loader-overlay" id="salog-loader">
            <div class="salog-loader-ring"></div>
            <div class="salog-loader-text">Carregando {escolha}</div>
            <div class="salog-loader-sub">Sincronizando dados em tempo real…</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        PAGINAS[escolha]()
    except Exception as _err:
        loader_slot.empty()
        _tipo = type(_err).__name__
        _is_db = any(k in str(_err).lower() for k in ["sql", "odbc", "connect", "driver", "08s01", "operationalerror", "pyodbc"])
        _icone  = "📡" if _is_db else "⚠️"
        _titulo = "Falha na conexão com o banco de dados" if _is_db else "Algo deu errado"
        _msg    = (
            "Não foi possível estabelecer conexão com o servidor. "
            "Verifique sua rede e tente novamente em alguns instantes."
            if _is_db else
            "Ocorreu um erro inesperado ao carregar esta página. "
            "Tente novamente ou entre em contato com o suporte."
        )
        st.markdown(f"""
        <style>
        .salog-error-wrap {{
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; min-height: 60vh;
            animation: fade-up 0.5s ease-out both;
        }}
        .salog-error-card {{
            background: rgba(13,24,37,0.80);
            border: 1px solid rgba(239,68,68,0.25);
            border-radius: 20px;
            padding: 48px 52px;
            max-width: 520px; width: 100%;
            text-align: center;
            box-shadow: 0 0 60px rgba(239,68,68,0.10);
            backdrop-filter: blur(16px);
            position: relative; overflow: hidden;
        }}
        .salog-error-card::before {{
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(239,68,68,0.6), transparent);
        }}
        .salog-error-icon {{
            font-size: 52px; margin-bottom: 20px;
            filter: drop-shadow(0 0 16px rgba(239,68,68,0.5));
        }}
        .salog-error-title {{
            font-family: 'Inter', sans-serif;
            font-size: 1.35rem; font-weight: 700;
            color: #FFFFFF; margin-bottom: 14px;
            letter-spacing: -0.01em;
        }}
        .salog-error-msg {{
            font-family: 'Inter', sans-serif;
            font-size: 0.90rem; line-height: 1.65;
            color: #6B7A8F; margin-bottom: 30px;
        }}
        .salog-error-code {{
            display: inline-flex; align-items: center; gap: 8px;
            background: rgba(239,68,68,0.07);
            border: 1px solid rgba(239,68,68,0.18);
            border-radius: 8px; padding: 8px 16px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.70rem; letter-spacing: 0.12em;
            color: rgba(239,68,68,0.75); text-transform: uppercase;
        }}
        .salog-error-hint {{
            margin-top: 24px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem; letter-spacing: 0.18em;
            color: rgba(107,122,143,0.5); text-transform: uppercase;
        }}
        </style>
        <div class="salog-error-wrap">
          <div class="salog-error-card">
            <div class="salog-error-icon">{_icone}</div>
            <div class="salog-error-title">{_titulo}</div>
            <div class="salog-error-msg">{_msg}</div>
            <div class="salog-error-code">
              <span style="width:6px;height:6px;border-radius:50%;background:rgba(239,68,68,0.7);display:inline-block;"></span>
              {_tipo}
            </div>
            <div class="salog-error-hint">use o menu lateral para tentar novamente</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        loader_slot.empty()
    st.stop()

# =========================
# CSS GLOBAL
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --neon: #00C22D;
    --neon-soft: #00E84D;
    --bg-1: #05070A;
    --bg-2: #0D1117;
    --card: rgba(13, 24, 37, 0.7);
    --border: rgba(0, 194, 45, 0.18);
    --text: #E6F0EA;
    --muted: #6B7A8F;
}

/* Reset Streamlit */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    color: var(--text);
}
[data-testid="stHeader"], [data-testid="stSidebar"], #MainMenu, footer {
    display: none !important;
}
[data-testid="stAppViewContainer"] > .main {
    padding: 0 !important;
}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ===== Fundo animado ===== */
.stApp {
    background:
        radial-gradient(ellipse at top, rgba(0,194,45,0.18), transparent 55%),
        radial-gradient(circle at 20% 80%, rgba(0,194,45,0.10), transparent 40%),
        linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%) !important;
    background-attachment: fixed !important;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

/* Grid animado */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,194,45,0.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,194,45,0.06) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: grid-pan 20s linear infinite;
    pointer-events: none;
    z-index: 0;
}

/* Orbes flutuantes */
.stApp::after {
    content: '';
    position: fixed;
    top: 10%; left: -10%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(0,194,45,0.25), transparent 70%);
    filter: blur(80px);
    animation: orb-float 14s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}

@keyframes grid-pan {
    0% { background-position: 0 0; }
    100% { background-position: 80px 80px; }
}
@keyframes orb-float {
    0%, 100% { transform: translate(0,0) scale(1); }
    50% { transform: translate(60px,-40px) scale(1.15); }
}
@keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 rgba(0,194,45,0.6); }
    100% { box-shadow: 0 0 0 22px rgba(0,194,45,0); }
}
@keyframes scan-line {
    0% { transform: translateY(0); }
    100% { transform: translateY(600px); }
}
@keyframes ticker {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
@keyframes fade-up {
    0% { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}
@keyframes glow-pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
}

/* ===== Layout principal ===== */
.salog-wrap {
    position: relative;
    z-index: 10;
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px 32px 0 32px;
}

/* HEADER */
.salog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0 32px 0;
}
.salog-logo {
    display: flex; align-items: center; gap: 12px;
}
.salog-logo-badge {
    width: 38px; height: 38px;
    border-radius: 10px;
    background: rgba(0,194,45,0.12);
    border: 1px solid rgba(0,194,45,0.45);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 30px rgba(0,194,45,0.35);
    animation: pulse-ring 2s ease-out infinite;
    font-size: 18px;
}
.salog-logo-text { line-height: 1.1; }
.salog-logo-name {
    font-size: 18px; font-weight: 800;
    letter-spacing: 0.25em; color: #fff;
}
.salog-logo-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; letter-spacing: 0.3em;
    color: var(--neon);
}
.salog-nav {
    display: flex; gap: 28px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 0.18em;
    color: var(--muted); text-transform: uppercase;
}
.salog-nav span:hover { color: #fff; cursor: pointer; }

/* GRID 2 colunas */
.salog-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 48px;
    padding: 24px 0 80px 0;
    animation: fade-up 0.7s ease-out both;
}
@media (max-width: 900px) {
    .salog-grid { grid-template-columns: 1fr; }
}

/* LEFT PANE */
.salog-badge-live {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(0,194,45,0.06);
    border: 1px solid rgba(0,194,45,0.3);
    border-radius: 999px;
    padding: 6px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 600;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: var(--neon);
}
.live-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--neon);
    box-shadow: 0 0 10px var(--neon);
    animation: glow-pulse 1.5s ease-in-out infinite;
}
.salog-title {
    font-size: 56px; font-weight: 800;
    line-height: 1.02; letter-spacing: -0.02em;
    margin: 24px 0 20px 0; color: #fff;
}
.salog-title .neon-text {
    background: linear-gradient(90deg, var(--neon), #4DE89A);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
}
.salog-desc {
    font-size: 15px; line-height: 1.7;
    color: var(--muted); max-width: 420px;
    margin-bottom: 36px;
}
.salog-features { list-style: none; padding: 0; margin: 0 0 40px 0; }
.salog-feature {
    display: flex; gap: 16px; margin-bottom: 22px;
    align-items: flex-start;
}
.salog-feat-icon {
    width: 40px; height: 40px; flex-shrink: 0;
    border-radius: 10px;
    background: rgba(0,194,45,0.06);
    border: 1px solid rgba(0,194,45,0.3);
    display: flex; align-items: center; justify-content: center;
    color: var(--neon); font-size: 18px;
}
.salog-feat-title {
    font-size: 15px; font-weight: 600; color: #fff;
    margin-bottom: 2px;
}
.salog-feat-desc { font-size: 13px; color: var(--muted); }

.salog-kpis {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 12px; max-width: 420px;
}
.salog-kpi {
    background: rgba(13,24,37,0.6);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    backdrop-filter: blur(8px);
}
.salog-kpi-k {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; text-transform: uppercase;
    letter-spacing: 0.2em; color: var(--muted);
}
.salog-kpi-v {
    font-size: 20px; font-weight: 700;
    color: var(--neon); margin-top: 2px;
}

/* CARD CADASTRO */
.salog-card-wrap {
    position: relative;
    animation: fade-up 0.8s 0.1s ease-out both;
}
.salog-card-glow {
    position: absolute; inset: -2px;
    background: linear-gradient(135deg, rgba(0,194,45,0.6), rgba(0,194,45,0.05), transparent);
    border-radius: 18px;
    filter: blur(8px); opacity: 0.7;
    z-index: 0;
}
.salog-card {
    position: relative;
    background: rgba(13,24,37,0.75);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 36px;
    overflow: hidden;
    box-shadow: 0 0 50px rgba(0,194,45,0.15);
    z-index: 1;
}
.salog-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--neon), transparent);
    animation: scan-line 4s linear infinite;
    z-index: 1;
}
.salog-card-header {
    display: flex; justify-content: space-between;
    align-items: flex-start; margin-bottom: 28px;
}
.salog-card-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: 0.2em;
    color: var(--neon); text-transform: uppercase;
}
.salog-card-tag .cursor { animation: blink 1s step-end infinite; }
.salog-card-title {
    font-size: 26px; font-weight: 700;
    color: #fff; margin-top: 6px;
}
.salog-card-pill {
    background: rgba(0,194,45,0.06);
    border: 1px solid rgba(0,194,45,0.3);
    border-radius: 999px;
    padding: 5px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.18em;
    color: var(--neon); text-transform: uppercase;
}

/* ===== Inputs Streamlit estilizados ===== */
.stTextInput > div > div > input,
.stPasswordInput > div > div > input,
[data-testid="stTextInput"] input {
    background: rgba(13,24,37,0.6) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: #fff !important;
    padding: 12px 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    transition: all 0.2s ease;
}
.stTextInput > div > div > input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: var(--neon) !important;
    box-shadow: 0 0 0 3px rgba(0,194,45,0.15), 0 0 25px rgba(0,194,45,0.25) !important;
}
.stTextInput label, [data-testid="stTextInput"] label,
.stCheckbox label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
}

/* Checkbox */
.stCheckbox { color: var(--muted); }
.stCheckbox [data-testid="stMarkdownContainer"] p {
    font-size: 13px !important;
    color: var(--muted) !important;
    font-family: 'Inter', sans-serif !important;
    text-transform: none !important;
    letter-spacing: normal !important;
}
.stCheckbox span[data-baseweb="checkbox"] > div:first-child {
    background: rgba(13,24,37,0.6) !important;
    border-color: var(--border) !important;
    border-radius: 4px !important;
}
.stCheckbox input:checked ~ span > div:first-child {
    background: var(--neon) !important;
    border-color: var(--neon) !important;
}

/* Botão principal */
.stButton > button, .stFormSubmitButton > button {
    width: 100% !important;
    background: var(--neon) !important;
    color: #05070A !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.05em !important;
    transition: all 0.25s ease;
    box-shadow: 0 0 20px rgba(0,194,45,0.3);
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    box-shadow: 0 0 40px rgba(0,194,45,0.6), 0 0 80px rgba(0,194,45,0.25) !important;
    transform: translateY(-1px);
    filter: brightness(1.05);
}
.stButton > button:disabled, .stFormSubmitButton > button:disabled {
    opacity: 0.4; cursor: not-allowed;
    box-shadow: none !important;
}

/* Alertas */
.stAlert {
    background: rgba(13,24,37,0.6) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* Divisor "ou com credenciais" */
.salog-divider {
    display: flex; align-items: center; gap: 12px;
    margin: 24px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.25em;
    color: var(--muted); text-transform: uppercase;
}
.salog-divider::before, .salog-divider::after {
    content: ''; flex: 1; height: 1px;
    background: var(--border);
}

/* Botões sociais (HTML puro, visual apenas) */
.salog-socials {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 12px; margin: 24px 0;
}
.salog-social {
    display: flex; align-items: center; justify-content: center;
    gap: 8px;
    background: rgba(13,24,37,0.5);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 11px;
    color: #fff; font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.2s;
    text-decoration: none;
}
.salog-social:hover {
    border-color: rgba(0,194,45,0.5);
    background: rgba(0,194,45,0.05);
    color: var(--neon);
}

/* Nota de rodapé */
.salog-foot {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.2em;
    color: var(--muted); text-transform: uppercase;
    margin-top: 18px;
}

/* Medidor de força */
.salog-strength {
    display: flex; gap: 4px; margin-top: 8px;
    align-items: center;
}
.salog-strength-bar {
    flex: 1; height: 4px; border-radius: 2px;
    background: rgba(0,194,45,0.1);
    transition: all 0.3s;
}
.salog-strength-bar.on {
    background: var(--neon);
    box-shadow: 0 0 8px var(--neon);
}
.salog-strength-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.15em;
    color: var(--muted); text-transform: uppercase;
    margin-left: 10px; min-width: 60px;
}

/* TICKER */
.salog-ticker {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: rgba(13,24,37,0.85);
    border-top: 1px solid var(--border);
    backdrop-filter: blur(8px);
    padding: 10px 0;
    overflow: hidden;
    z-index: 100;
}
.salog-ticker-inner {
    display: inline-flex; gap: 40px;
    animation: ticker 30s linear infinite;
    white-space: nowrap;
}
.salog-ticker-item {
    display: inline-flex; align-items: center; gap: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; color: var(--muted);
    letter-spacing: 0.08em;
}
.salog-ticker-dot {
    width: 4px; height: 4px; border-radius: 50%;
    background: var(--neon);
    animation: glow-pulse 2s ease-in-out infinite;
}

/* Card de sucesso */
.salog-success {
    text-align: center; padding: 24px 0;
    animation: fade-up 0.6s ease-out both;
}
.salog-success-circle {
    width: 80px; height: 80px; margin: 0 auto 20px;
    border-radius: 50%;
    background: rgba(0,194,45,0.1);
    border: 1px solid rgba(0,194,45,0.45);
    display: flex; align-items: center; justify-content: center;
    font-size: 36px; color: var(--neon);
    box-shadow: 0 0 60px rgba(0,194,45,0.6);
    animation: pulse-ring 2s ease-out infinite;
}
.salog-success-title {
    font-size: 22px; font-weight: 700; color: #fff;
    margin-bottom: 8px;
}
.salog-success-desc {
    font-size: 13px; color: var(--muted);
    max-width: 280px; margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
def calc_strength(pwd: str) -> int:
    s = 0
    if len(pwd) >= 8: s += 1
    if re.search(r'[A-Z]', pwd): s += 1
    if re.search(r'[0-9]', pwd): s += 1
    if re.search(r'[^A-Za-z0-9]', pwd): s += 1
    return s

LABELS = ["—", "Fraca", "Razoável", "Boa", "Forte"]

# =========================
# HEADER + LEFT PANE (HTML)
# =========================
st.markdown(f"""
<div class="salog-wrap">
  <div class="salog-header">
       <div class="salog-nav">
      <span>/ops</span><span>/rec</span><span>/sla</span><span>/cd</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# Grid 2 colunas — usamos colunas reais do Streamlit
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("""
    <div style="padding: 0 32px;">
      <div class="salog-badge-live">
        <span class="live-dot"></span> AO VIVO · CD ITUPEVA
      </div>
      <h1 class="salog-title">
        Torre de<br>
        <span class="neon-text">Controle</span><br>
        SALOG.
      </h1>
      <p class="salog-desc">
        Monitoramento WMS em tempo real — expedições, recebimentos, SLA de separação
        e performance do CD em um único cockpit.
      </p>
      <ul class="salog-features">
        <li class="salog-feature">
          <div class="salog-feat-icon">⚡</div>
          <div>
            <div class="salog-feat-title">Tempo real</div>
            <div class="salog-feat-desc">Status de OPS/REC sincronizado a cada segundo</div>
          </div>
        </li>
        <li class="salog-feature">
          <div class="salog-feat-icon">🛡</div>
          <div>
            <div class="salog-feat-title">Acesso seguro</div>
            <div class="salog-feat-desc">Credenciais criptografadas e log de auditoria</div>
          </div>
        </li>
        <li class="salog-feature">
          <div class="salog-feat-icon">✦</div>
          <div>
            <div class="salog-feat-title">Inteligência operacional</div>
            <div class="salog-feat-desc">KPIs, SLA e performance em um só painel</div>
          </div>
        </li>
      </ul>
      <div class="salog-kpis">
        <div class="salog-kpi"><div class="salog-kpi-k">uptime</div><div class="salog-kpi-v">99.98%</div></div>
        <div class="salog-kpi"><div class="salog-kpi-k">ops/dia</div><div class="salog-kpi-v">12.4k</div></div>
        <div class="salog-kpi"><div class="salog-kpi-k">sla</div><div class="salog-kpi-v">98.2%</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# CARD CADASTRO (HTML wrapper + form Streamlit)
# =========================
with col_right:
    st.markdown("""
    <div style="padding: 0 32px;">
      <div class="salog-card-wrap">
        <div class="salog-card-glow"></div>
        <div class="salog-card">
          <div class="salog-card-header">
            <div>
              <div class="salog-card-tag"><span class="cursor">▌</span> /cadastro</div>
              <div class="salog-card-title">Cadastro de operador</div>
            </div>
            <div class="salog-card-pill">SALOG · WMS</div>
          </div>
    """, unsafe_allow_html=True)

    if False:
        pass
    else:
        # Sociais (visual)
        st.markdown("""
          <div class="salog-socials">
            <div class="salog-social">🐙 GitHub</div>
            <div class="salog-social">🇬 Google</div>
          </div>
          <div class="salog-divider">ou com credenciais</div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            login = st.text_input("LOGIN", placeholder="seu.login")
            email = st.text_input("E-MAIL CORPORATIVO", placeholder="voce@salog.com.br")
            senha = st.text_input("SENHA", type="password", placeholder="••••••••••")

            # Medidor de força
            strength = calc_strength(senha)
            bars = "".join([
                f'<div class="salog-strength-bar {"on" if i < strength else ""}"></div>'
                for i in range(4)
            ])
            st.markdown(
                f'<div class="salog-strength">{bars}'
                f'<span class="salog-strength-label">{LABELS[strength]}</span></div>',
                unsafe_allow_html=True
            )

            aceito = st.checkbox("Concordo com os Termos e a Política de Privacidade.")
            submit = st.form_submit_button("ENTRAR ⟶")

            if submit:
                if not (login and email and senha and aceito):
                    st.error("Preencha todos os campos e aceite os termos.")
                elif AUTH_LOGIN is None:
                    st.error("Credenciais não configuradas em .streamlit/secrets.toml ([auth]).")
                elif (login.strip() == AUTH_LOGIN
                      and email.strip().lower() == AUTH_EMAIL.lower()
                      and senha == AUTH_SENHA):
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Login, e-mail ou senha incorretos.")

        st.markdown(
            '<div class="salog-foot">acesso protegido · log de auditoria ativo</div>',
            unsafe_allow_html=True
        )

    # Fecha card
    st.markdown("</div></div></div>", unsafe_allow_html=True)

# =========================
# TICKER (rodapé fixo)
# =========================
ticker_items = [
    "// cd_itupeva", "uptime 99.98%", "ops_realtime", "wms_v2",
    "sla_98.2%", "rec_online", "exp_online", "salog_control_tower"
]
items_html = "".join([
    f'<span class="salog-ticker-item"><span class="salog-ticker-dot"></span>{t}</span>'
    for t in (ticker_items * 2)
])
st.markdown(f"""
<div class="salog-ticker">
  <div class="salog-ticker-inner">{items_html}</div>
</div>
""", unsafe_allow_html=True)