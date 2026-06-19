import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from sqlalchemy import create_engine, text
import streamlit.components.v1 as components
from db import get_engine as _get_engine


# ─────────────────────────────────────────────────────────────────
#  PERSISTÊNCIA — SALVAR/CARREGAR REGISTROS NO BANCO
# ─────────────────────────────────────────────────────────────────
_CREATE_TABLE_SQL = """
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'INV_REGISTROS'
)
CREATE TABLE dbo.INV_REGISTROS (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    operador    NVARCHAR(100)  NOT NULL,
    endereco    NVARCHAR(100)  NOT NULL,
    ua_sistema  NVARCHAR(100),
    ua_fisica   NVARCHAR(100),
    status      NVARCHAR(50)   NOT NULL,
    tipo        NVARCHAR(50),
    ts          NVARCHAR(30),
    criado_em   DATETIME       DEFAULT GETDATE(),
    CONSTRAINT UQ_INV_OP_END UNIQUE (operador, endereco)
);
"""

def _ensure_table():
    """Cria a tabela de persistência se não existir."""
    try:
        engine = _get_engine()
        with engine.begin() as conn:
            conn.execute(text(_CREATE_TABLE_SQL))
        return True
    except Exception:
        return False


def _load_registros(operador: str) -> dict:
    """Carrega os registros do banco para o operador logado."""
    try:
        engine = _get_engine()
        sql = text("""
            SELECT endereco, ua_sistema, ua_fisica, status, tipo, ts
            FROM dbo.INV_REGISTROS
            WHERE operador = :op
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"op": operador}).fetchall()
        result = {}
        for row in rows:
            result[row[0]] = {
                "ua_sistema": row[1],
                "ua_fisica":  row[2],
                "status":     row[3],
                "tipo":       row[4],
                "ts":         row[5],
                "op":         operador,
            }
        return result
    except Exception:
        return {}


def _save_registro(operador: str, endereco: str, reg: dict):
    """Salva/atualiza um registro no banco (UPSERT)."""
    try:
        engine = _get_engine()
        sql = text("""
            MERGE dbo.INV_REGISTROS AS target
            USING (SELECT :op AS operador, :end AS endereco) AS src
                ON target.operador = src.operador AND target.endereco = src.endereco
            WHEN MATCHED THEN
                UPDATE SET ua_sistema=:ua_sys, ua_fisica=:ua_fis,
                           status=:status, tipo=:tipo, ts=:ts
            WHEN NOT MATCHED THEN
                INSERT (operador, endereco, ua_sistema, ua_fisica, status, tipo, ts)
                VALUES (:op, :end, :ua_sys, :ua_fis, :status, :tipo, :ts);
        """)
        with engine.begin() as conn:
            conn.execute(sql, {
                "op":     operador,
                "end":    endereco,
                "ua_sys": reg.get("ua_sistema"),
                "ua_fis": reg.get("ua_fisica"),
                "status": reg["status"],
                "tipo":   reg.get("tipo"),
                "ts":     reg.get("ts"),
            })
        return True
    except Exception:
        return False


def _delete_registros_rua(operador: str, enderecos: list):
    """Remove registros de uma rua para o operador (usado em 'Limpar rua')."""
    if not enderecos:
        return
    try:
        engine = _get_engine()
        sql = text("""
            DELETE FROM dbo.INV_REGISTROS
            WHERE operador = :op AND endereco IN :ends
        """)
        # pyodbc não aceita lista diretamente; monta placeholders
        placeholders = ", ".join([f":e{i}" for i in range(len(enderecos))])
        sql2 = text(f"""
            DELETE FROM dbo.INV_REGISTROS
            WHERE operador = :op AND endereco IN ({placeholders})
        """)
        params = {"op": operador}
        for i, e in enumerate(enderecos):
            params[f"e{i}"] = e
        with engine.begin() as conn:
            conn.execute(sql2, params)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────
#  PARSER DE ENDEREÇO
# ─────────────────────────────────────────────────────────────────
def _parse_endereco(end):
    if end is None:
        return None, None, None
    s = str(end).strip().upper()
    if not s:
        return None, None, None
    try:
        partes = [p for p in re.split(r"[^A-Z0-9]+", s) if p]
        if len(partes) >= 3:
            rua_token = next((p for p in partes if re.search(r"[A-Z]", p)), partes[0])
            numeros = [int(p) for p in partes if p.isdigit()]
            if len(numeros) >= 2:
                return rua_token, numeros[-2], numeros[-1]
        if len(partes) == 2:
            a, b = partes
            rua_token = a if re.search(r"[A-Z]", a) else b
            num_token = b if rua_token is a else a
            if num_token.isdigit() and len(num_token) >= 2:
                meio = len(num_token) // 2
                return rua_token, int(num_token[:meio] or "0"), int(num_token[meio:])
        m = re.match(r"^([A-Z]+|\d+)(\d{2,})$", s)
        if m:
            rua = m.group(1)
            digits = m.group(2)
            if len(digits) >= 2:
                meio = len(digits) // 2
                return rua, int(digits[:meio] or "0"), int(digits[meio:])
    except Exception:
        pass
    return None, None, None


# ─────────────────────────────────────────────────────────────────
#  CACHE DE DADOS DO BANCO (TTL 90s)
# ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=90, show_spinner=False)
def _fetch_enderecos():
    """Busca endereços do banco — cacheado 90s para não travar a UI."""
    query = """
    SELECT ENDERECO, STATUS, AREA, UA
    FROM db_visual_SALOG.dbo.VW_PAINEL_STATUS_ENDERECOS_ARMAZEM
    WHERE AREA = 'SECO' AND ENDERECO IS NOT NULL
    """
    engine = _get_engine()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)


def _get_df() -> pd.DataFrame:
    """Retorna DataFrame processado com cache de sessão (recalcula só se expirou)."""
    cache_ts = st.session_state.get("inv_df_ts")
    now = datetime.now()
    if cache_ts and (now - cache_ts).total_seconds() < 90:
        return st.session_state["inv_df_cache"]

    df_raw = _fetch_enderecos()
    if df_raw.empty:
        return df_raw

    df_raw = df_raw.copy()
    df_raw["ENDERECO"] = df_raw["ENDERECO"].astype(str).str.strip().str.upper()
    df_raw["STATUS"]   = df_raw["STATUS"].astype(str).str.strip().str.upper()
    if "UA" in df_raw.columns:
        df_raw["UA"] = df_raw["UA"].astype(str).str.strip()
        df_raw.loc[df_raw["UA"].isin(["NAN", "NONE", ""]), "UA"] = None

    LIVRES     = {"LIVRE", "VAZIO", "VAZIA", "DISPONIVEL", "DISPONÍVEL", ""}
    BLOQUEADOS = {"BLOQUEADO", "BLOQUEADA", "BLOCKED", "INATIVO", "INATIVA"}
    df_raw["OCUPADO"] = ~df_raw["STATUS"].isin(LIVRES) & ~df_raw["STATUS"].isin(BLOQUEADOS)

    parsed = df_raw["ENDERECO"].apply(
        lambda e: pd.Series(_parse_endereco(e), index=["RUA", "NIVEL", "POSICAO"])
    )
    df = pd.concat([df_raw.reset_index(drop=True), parsed.reset_index(drop=True)], axis=1)
    df = df.dropna(subset=["RUA", "NIVEL", "POSICAO"]).copy()
    df["NIVEL"]   = df["NIVEL"].astype(int)
    df["POSICAO"] = df["POSICAO"].astype(int)

    st.session_state["inv_df_cache"] = df
    st.session_state["inv_df_ts"]    = now
    return df


# ─────────────────────────────────────────────────────────────────
#  ESTADO DE SESSÃO
# ─────────────────────────────────────────────────────────────────
def _init_state(operador: str):
    defaults = {
        "inv_rua":             None,
        "inv_pos_sel":         None,
        "inv_registros":       None,   # None = não carregado ainda
        "inv_registros_op":    None,   # operador cujos registros estão carregados
        "inv_df_cache":        None,
        "inv_df_ts":           None,
        "inv_last_msg":        None,
        "inv_modo_vazio":      False,  # modo seleção múltipla de vazios
        "inv_vazios_sel":      [],     # endereços selecionados no modo vazio
        "inv_table_ok":        False,  # tabela criada?
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Garante que a tabela existe (executa uma vez por sessão)
    if not st.session_state["inv_table_ok"]:
        _ensure_table()
        st.session_state["inv_table_ok"] = True

    # Carrega/recarrega registros quando muda de operador
    if st.session_state["inv_registros"] is None or st.session_state["inv_registros_op"] != operador:
        st.session_state["inv_registros"]    = _load_registros(operador)
        st.session_state["inv_registros_op"] = operador


# ─────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
* { box-sizing: border-box; }
:root {
    --bg:      #0F172A;
    --surface: #1E293B;
    --s2:      #273548;
    --border:  rgba(148,163,184,0.10);
    --border2: rgba(148,163,184,0.20);
    --text:    #F8FAFC;
    --muted:   #94A3B8;
    --green:   #22C55E;
    --amber:   #F59E0B;
    --red:     #EF4444;
    --blue:    #3B82F6;
    --mono:    'JetBrains Mono', monospace;
    --sans:    'Inter', sans-serif;
}
html, body, [class*="css"] { font-family: var(--sans) !important; }
.stApp { background: var(--bg) !important; }
.block-container {
    padding: 1.2rem 2rem 3rem !important;
    max-width: 1700px !important;
}
div[data-testid="stVerticalBlock"] { gap: 0.85rem !important; }
.stMarkdown { margin: 0 !important; }

/* ── HEADER ── */
.inv-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 0 22px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 26px;
}
.inv-title {
    font-size: 1.65rem; font-weight: 800;
    color: var(--text); letter-spacing: -0.03em; margin: 0;
}
.inv-title em { font-style: normal; color: #4ADE80; }
.inv-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 6px; padding: 6px 14px;
    font-family: var(--mono); font-size: 11px; font-weight: 600;
    color: #4ADE80; letter-spacing: 0.12em;
}
.inv-badge-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #22C55E;
    animation: inv-blink 2s ease-in-out infinite;
}
@keyframes inv-blink { 0%,100%{opacity:1;} 50%{opacity:0.25;} }

/* ── TÍTULO DE SEÇÃO ── */
.sec-title {
    display: flex; align-items: center; gap: 10px;
    margin: 24px 0 12px;
    font-family: var(--mono);
    font-size: 10.5px;
    font-weight: 700;
    color: var(--muted);
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
.sec-title::before {
    content: '';
    width: 3px; height: 14px; border-radius: 2px;
    background: linear-gradient(180deg, #22C55E, #3B82F6);
}
.sec-title .sec-count {
    margin-left: auto;
    font-size: 10px;
    color: rgba(148,163,184,0.55);
    letter-spacing: 0.08em;
}

/* ── CARD GENÉRICO ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 4px;
}

/* ── KPI GRID ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 14px;
}
@media (max-width: 1100px) {
    .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.kpi {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px 16px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}
.kpi:hover { border-color: var(--border2); transform: translateY(-1px); }
.kpi::before {
    content:''; position: absolute; left:0; top:0; bottom:0;
    width: 3px; background: var(--accent, #3B82F6);
}
.kpi-label {
    font-family: var(--mono); font-size: 10px; font-weight: 600;
    color: var(--muted); letter-spacing: 0.14em;
    text-transform: uppercase; margin-bottom: 10px;
}
.kpi-value {
    font-family: var(--mono); font-size: 28px; font-weight: 700;
    color: var(--text); line-height: 1; letter-spacing: -0.02em;
}
.kpi-sub {
    font-size: 11px; color: var(--muted); margin-top: 8px;
}
.kpi.kpi-info    { --accent: #3B82F6; }
.kpi.kpi-amber   { --accent: #F59E0B; } .kpi.kpi-amber .kpi-value   { color: #FCD34D; }
.kpi.kpi-red     { --accent: #EF4444; } .kpi.kpi-red .kpi-value     { color: #F87171; }
.kpi.kpi-muted   { --accent: #64748B; } .kpi.kpi-muted .kpi-value   { color: #CBD5E1; }
.kpi.kpi-green   { --accent: #22C55E; } .kpi.kpi-green .kpi-value   { color: #4ADE80; }

/* ── PROGRESSO ── */
.prog-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
}
.prog-head {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
}
.prog-head-left {
    font-family: var(--mono); font-size: 11px; font-weight: 700;
    color: var(--muted); letter-spacing: 0.12em; text-transform: uppercase;
}
.prog-head-right {
    font-family: var(--mono); font-size: 14px; font-weight: 700;
}
.prog-track {
    width: 100%; height: 10px;
    background: rgba(148,163,184,0.10);
    border-radius: 6px; overflow: hidden;
}
.prog-fill {
    height: 100%; border-radius: 6px;
    transition: width 0.35s cubic-bezier(.4,0,.2,1);
    background: linear-gradient(90deg, var(--pcol,#3B82F6), color-mix(in oklab, var(--pcol,#3B82F6) 70%, white));
    box-shadow: 0 0 14px color-mix(in oklab, var(--pcol,#3B82F6) 50%, transparent);
}

/* ── POSIÇÃO SELECIONADA ── */
.pos-card {
    background: linear-gradient(135deg, rgba(59,130,246,0.06), rgba(59,130,246,0.02));
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 12px;
    padding: 22px 26px;
    display: flex; align-items: center; gap: 26px; flex-wrap: wrap;
}
.pos-card .pin {
    width: 46px; height: 46px; border-radius: 12px;
    background: rgba(59,130,246,0.18);
    border: 1px solid rgba(59,130,246,0.45);
    display: grid; place-items: center;
    font-size: 20px; flex-shrink: 0;
}
.pos-block { display: flex; flex-direction: column; gap: 4px; }
.pos-block .k {
    font-family: var(--mono); font-size: 9.5px; font-weight: 600;
    color: var(--muted); letter-spacing: 0.15em; text-transform: uppercase;
}
.pos-block .v {
    font-family: var(--mono); font-size: 17px; font-weight: 700;
    color: var(--text); letter-spacing: -0.01em;
}
.pos-block .v.addr { color: #93C5FD; font-size: 20px; }
.pos-status {
    margin-left: auto;
    padding: 8px 14px; border-radius: 8px;
    font-family: var(--mono); font-size: 11px; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
}
.pos-status.ocupado { background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.35); color: #4ADE80; }
.pos-status.vazio   { background: rgba(148,163,184,0.10); border: 1px solid rgba(148,163,184,0.25); color: #94A3B8; }
.pos-empty {
    text-align: left; padding: 9px 14px;
    color: var(--muted); font-size: 12px;
    border: 1px dashed var(--border2); border-radius: 8px;
    background: rgba(30,41,59,0.4);
}

/* ── MODO VAZIO MÚLTIPLO ── */
.modo-vazio-banner {
    display: flex; align-items: center; gap: 14px;
    background: rgba(245,158,11,0.07);
    border: 1px solid rgba(245,158,11,0.30);
    border-radius: 12px; padding: 16px 20px;
    font-family: var(--mono); font-size: 12px;
    color: #FCD34D;
}
.modo-vazio-count {
    margin-left: auto;
    background: rgba(245,158,11,0.15);
    border: 1px solid rgba(245,158,11,0.35);
    border-radius: 6px; padding: 4px 10px;
    font-size: 11px; font-weight: 700;
}

/* ── ÚLTIMA LEITURA ── */
.read-card {
    border-radius: 12px;
    padding: 18px 22px;
    font-family: var(--mono);
    display: flex; align-items: center; gap: 16px;
}
.read-ok   { background: rgba(34,197,94,0.07);  border: 1px solid rgba(34,197,94,0.28); }
.read-warn { background: rgba(245,158,11,0.07); border: 1px solid rgba(245,158,11,0.28); }
.read-err  { background: rgba(239,68,68,0.07);  border: 1px solid rgba(239,68,68,0.28); }
.read-icon {
    width: 38px; height: 38px; border-radius: 10px;
    display: grid; place-items: center;
    font-size: 18px; font-weight: 700; flex-shrink: 0;
}
.read-ok   .read-icon { background: rgba(34,197,94,0.18);  color: #4ADE80; }
.read-warn .read-icon { background: rgba(245,158,11,0.18); color: #FCD34D; }
.read-err  .read-icon { background: rgba(239,68,68,0.18);  color: #F87171; }
.read-main { font-size: 13.5px; font-weight: 700; color: var(--text); }
.read-detail { font-size: 11.5px; color: var(--muted); margin-top: 3px; }

/* ── HINT ── */
.inv-hint {
    display: flex; align-items: center; gap: 12px;
    background: rgba(59,130,246,0.05);
    border: 1px solid rgba(59,130,246,0.18);
    border-radius: 10px; padding: 18px 22px;
    font-size: 13.5px; color: rgba(148,163,184,0.85);
}

/* ── INPUTS ── */
div[data-testid="stTextInput"] > div > div > input,
div[data-testid="stSelectbox"] > div > div {
    background: #182231 !important;
    border: 1px solid var(--border2) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
div[data-testid="stTextInput"] > div > div > input {
    font-family: var(--mono) !important;
    font-size: 14px !important;
    padding: 13px 16px !important;
    min-height: 46px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: rgba(34,197,94,0.55) !important;
    box-shadow: 0 0 0 3px rgba(34,197,94,0.10) !important;
    outline: none !important;
}
div[data-testid="stSelectbox"] > div > div {
    min-height: 46px !important;
    font-family: var(--mono) !important;
    font-size: 13.5px !important;
}

/* ── BOTÕES ── */
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    background: #182231 !important;
    border: 1px solid var(--border2) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    padding: 12px 18px !important;
    min-height: 46px !important;
    transition: background 0.15s, border-color 0.15s, transform 0.1s !important;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--s2) !important;
    border-color: rgba(34,197,94,0.45) !important;
    transform: translateY(-1px);
}

/* ── TABS / DATAFRAME ── */
div[data-testid="stTabs"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 8px 14px !important;
}
div[data-testid="stDataFrame"] {
    background: var(--surface) !important;
    border-radius: 10px !important;
}
</style>
"""


# ─────────────────────────────────────────────────────────────────
#  GRID VISUAL HTML — com suporte a seleção múltipla de vazios
# ─────────────────────────────────────────────────────────────────
def _build_grid_html(posicoes: list[dict], rua: str, modo_vazio: bool, vazios_sel: list) -> str:
    posicoes_json   = json.dumps(posicoes, ensure_ascii=False)
    vazios_sel_json = json.dumps(list(vazios_sel), ensure_ascii=False)
    rua_escaped     = rua.replace("'", "\\'")
    modo_vazio_js   = "true" if modo_vazio else "false"

    niveis  = sorted({p["nivel"] for p in posicoes}, reverse=True)
    altura  = max(420, len(niveis) * 60 + 160)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#0F172A;--surface:#1E293B;
  --border:rgba(148,163,184,0.10);--border2:rgba(148,163,184,0.22);
  --text:#F8FAFC;--muted:#94A3B8;
  --mono:'JetBrains Mono',monospace;
}}
body{{
  background:transparent;font-family:var(--mono);
  color:var(--text);padding:6px 4px 14px;
  min-height:{altura}px;
}}

.rack-scroll{{
  overflow-x:auto;overflow-y:auto;
  max-height:{altura - 80}px;
  padding:14px 14px 16px;
  background: rgba(15,23,42,0.45);
  border: 1px solid var(--border);
  border-radius: 12px;
}}
.rack-scroll::-webkit-scrollbar{{height:8px;width:8px;}}
.rack-scroll::-webkit-scrollbar-thumb{{background:rgba(148,163,184,0.22);border-radius:4px;}}
.rack-scroll::-webkit-scrollbar-track{{background:rgba(148,163,184,0.04);}}

.rack-inner{{
  display:flex;flex-direction:column;gap:10px;
  min-width:max-content;
}}

.nivel-row{{
  display:flex;align-items:center;gap:7px;
}}
.nivel-label{{
  font-size:10px;font-weight:700;color:rgba(148,163,184,0.55);
  min-width:34px;text-align:right;flex-shrink:0;letter-spacing:0.06em;
  padding-right:6px;border-right:1px solid var(--border);margin-right:4px;
}}

.pos{{
  width:50px;height:38px;border-radius:7px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:700;
  cursor:pointer;
  transition:transform 0.1s,filter 0.1s,box-shadow 0.15s;
  border:1px solid transparent;
  user-select:none;position:relative;
  letter-spacing:0.02em;
}}
.pos:hover{{transform:scale(1.10);z-index:5;filter:brightness(1.25);}}
.pos.selected,.pos.selecionado_bipagem{{
  box-shadow:0 0 0 2px #3B82F6,0 0 14px rgba(59,130,246,0.55)!important;
  transform:scale(1.08);z-index:6;
}}
.pos.multi-sel{{
  box-shadow:0 0 0 2px #F59E0B,0 0 14px rgba(245,158,11,0.55)!important;
  transform:scale(1.08);z-index:6;
}}

.pos.vazio{{
  background:rgba(51,65,85,0.35);
  border-color:rgba(51,65,85,0.50);
  color:rgba(148,163,184,0.45);
}}
.pos.pendente{{
  background:rgba(34,197,94,0.20);
  border-color:rgba(34,197,94,0.42);
  color:#4ADE80;
  box-shadow:0 0 8px rgba(34,197,94,0.14);
}}
.pos.ok{{
  background:rgba(245,158,11,0.22);
  border-color:rgba(245,158,11,0.48);
  color:#FCD34D;
}}
.pos.divergente{{
  background:rgba(239,68,68,0.20);
  border-color:rgba(239,68,68,0.45);
  color:#F87171;
  animation:div-pulse 2.5s ease-in-out infinite;
}}
@keyframes div-pulse{{
  0%,100%{{box-shadow:0 0 8px rgba(239,68,68,0.20);}}
  50%{{box-shadow:0 0 18px rgba(239,68,68,0.42);}}
}}
.pos.selecionado_bipagem{{
  background:rgba(59,130,246,0.25);
  border-color:rgba(59,130,246,0.60);
  color:#93C5FD;
}}

#tooltip{{
  display:none;position:fixed;z-index:1000;
  background:rgba(15,23,42,0.98);
  border:1px solid var(--border2);
  border-radius:10px;
  box-shadow:0 12px 44px rgba(0,0,0,0.65);
  overflow:hidden;pointer-events:none;
  min-width:210px;max-width:260px;
}}
.tip-head{{
  background:rgba(30,41,59,0.85);
  border-bottom:1px solid var(--border);
  padding:10px 14px 8px;
}}
.tip-addr{{font-size:14px;font-weight:700;color:var(--text);}}
.tip-st{{font-size:10.5px;font-weight:700;margin-top:3px;letter-spacing:0.08em;}}
.tip-body{{padding:10px 14px;}}
.tip-row{{display:flex;gap:8px;margin-bottom:4px;font-size:11px;}}
.tip-row:last-child{{margin-bottom:0;}}
.tip-k{{color:var(--muted);min-width:62px;flex-shrink:0;}}
.tip-v{{color:var(--text);font-weight:600;word-break:break-all;}}

.legenda{{
  display:flex;align-items:center;gap:20px;flex-wrap:wrap;
  padding:14px 4px 0;margin-top:14px;
  border-top:1px solid var(--border);
  font-size:11px;color:var(--muted);font-weight:500;
}}
.leg{{display:flex;align-items:center;gap:7px;}}
.leg-sq{{width:14px;height:14px;border-radius:3px;flex-shrink:0;}}
</style>
</head>
<body>

<div id="tooltip">
  <div class="tip-head">
    <div class="tip-addr" id="tip-addr"></div>
    <div class="tip-st"   id="tip-st"></div>
  </div>
  <div class="tip-body">
    <div class="tip-row"><span class="tip-k">Nível</span><span class="tip-v" id="tip-nivel"></span></div>
    <div class="tip-row"><span class="tip-k">Posição</span><span class="tip-v" id="tip-pos"></span></div>
    <div class="tip-row" id="tip-ua-row"><span class="tip-k">UA Sistema</span><span class="tip-v" id="tip-ua"></span></div>
    <div class="tip-row" id="tip-uaf-row"><span class="tip-k">UA Física</span><span class="tip-v" id="tip-uaf" style="color:#FCD34D;"></span></div>
    <div class="tip-row" id="tip-ts-row"><span class="tip-k">Conferido</span><span class="tip-v" id="tip-ts"></span></div>
  </div>
</div>

<div class="rack-scroll">
  <div class="rack-inner" id="rack"></div>
</div>

<div class="legenda">
  <div class="leg"><div class="leg-sq" style="background:rgba(34,197,94,0.25);border:1px solid rgba(34,197,94,0.45);"></div>Pendente</div>
  <div class="leg"><div class="leg-sq" style="background:rgba(245,158,11,0.25);border:1px solid rgba(245,158,11,0.45);"></div>Inventariado</div>
  <div class="leg"><div class="leg-sq" style="background:rgba(239,68,68,0.25);border:1px solid rgba(239,68,68,0.45);"></div>Divergência</div>
  <div class="leg"><div class="leg-sq" style="background:rgba(51,65,85,0.40);border:1px solid rgba(51,65,85,0.50);"></div>Vazio</div>
  <div class="leg"><div class="leg-sq" style="background:rgba(59,130,246,0.25);border:1px solid rgba(59,130,246,0.55);"></div>Selecionado</div>
  <div class="leg"><div class="leg-sq" style="background:rgba(245,158,11,0.25);border:1px solid rgba(245,158,11,0.55);"></div>Multi-vazio</div>
</div>

<script>
const POSICOES    = {posicoes_json};
const MODO_VAZIO  = {modo_vazio_js};
const VAZIOS_SEL  = new Set({vazios_sel_json});

const niveis = {{}};
POSICOES.forEach(p => {{
  if (!niveis[p.nivel]) niveis[p.nivel] = [];
  niveis[p.nivel].push(p);
}});
const niveisKeys = Object.keys(niveis).map(Number).sort((a,b) => b - a);

const rack = document.getElementById('rack');
let selectedEl = null;
const multiSelEls = new Map();  // endereco -> element

niveisKeys.forEach(niv => {{
  const row = document.createElement('div');
  row.className = 'nivel-row';

  const lbl = document.createElement('div');
  lbl.className = 'nivel-label';
  lbl.textContent = 'N' + String(niv).padStart(2,'0');
  row.appendChild(lbl);

  niveis[niv].slice().sort((a,b) => a.posicao - b.posicao).forEach(p => {{
    const el = document.createElement('div');
    el.className = 'pos ' + p.cls;
    el.id = 'pos_' + p.endereco.replace(/[^A-Z0-9]/g,'_');
    el.dataset.endereco = p.endereco;
    el.dataset.cls = p.cls;
    el.textContent = String(p.posicao).padStart(2,'0');

    // Restaura seleção múltipla de vazios do estado salvo
    if (VAZIOS_SEL.has(p.endereco) && p.cls === 'vazio') {{
      el.classList.add('multi-sel');
      multiSelEls.set(p.endereco, el);
    }}

    el.addEventListener('mouseenter', e => showTip(e, p));
    el.addEventListener('mouseleave', hideTip);
    el.addEventListener('mousemove',  moveTip);
    el.addEventListener('click', () => selectPos(p, el));
    row.appendChild(el);
  }});

  rack.appendChild(row);
}});

const tip = document.getElementById('tooltip');
const ST_LABEL = {{vazio:'LIVRE',pendente:'PENDENTE',ok:'INVENTARIADO',divergente:'DIVERGÊNCIA',selecionado_bipagem:'SELECIONADO'}};
const ST_COLOR = {{vazio:'#64748B',pendente:'#4ADE80',ok:'#FCD34D',divergente:'#F87171',selecionado_bipagem:'#93C5FD'}};

function showTip(e, p) {{
  document.getElementById('tip-addr').textContent  = p.endereco;
  const st = document.getElementById('tip-st');
  st.textContent = ST_LABEL[p.cls] || p.cls;
  st.style.color  = ST_COLOR[p.cls]  || '#94A3B8';
  document.getElementById('tip-nivel').textContent = p.nivel;
  document.getElementById('tip-pos').textContent   = p.posicao;

  const uaRow = document.getElementById('tip-ua-row');
  if (p.ua) {{ document.getElementById('tip-ua').textContent = p.ua; uaRow.style.display='flex'; }}
  else uaRow.style.display='none';

  const uafRow = document.getElementById('tip-uaf-row');
  if (p.ua_fisica) {{ document.getElementById('tip-uaf').textContent = p.ua_fisica; uafRow.style.display='flex'; }}
  else uafRow.style.display='none';

  const tsRow = document.getElementById('tip-ts-row');
  if (p.ts) {{ document.getElementById('tip-ts').textContent = p.ts; tsRow.style.display='flex'; }}
  else tsRow.style.display='none';

  tip.style.display='block';
  moveTip(e);
}}
function moveTip(e) {{
  const x = e.clientX + 14, y = e.clientY - 14;
  tip.style.left = Math.min(x, window.innerWidth - 270) + 'px';
  tip.style.top  = Math.max(y, 4) + 'px';
}}
function hideTip() {{ tip.style.display='none'; }}

function selectPos(p, el) {{
  if (MODO_VAZIO) {{
    // No modo vazio: só permite selecionar células vazias (sem UA no sistema)
    if (p.cls !== 'vazio') return;
    if (multiSelEls.has(p.endereco)) {{
      // deseleciona
      el.classList.remove('multi-sel');
      multiSelEls.delete(p.endereco);
      VAZIOS_SEL.delete(p.endereco);
    }} else {{
      el.classList.add('multi-sel');
      multiSelEls.set(p.endereco, el);
      VAZIOS_SEL.add(p.endereco);
    }}
    // Envia lista atualizada para o Streamlit
    try {{
      const url = new URL(window.parent.location.href);
      url.searchParams.set('vazios', JSON.stringify(Array.from(VAZIOS_SEL)));
      url.searchParams.delete('pos');
      window.parent.history.replaceState(null, '', url.toString());
    }} catch(e) {{}}
    window.parent.postMessage({{
      type: 'inv_multi_vazio',
      vazios: Array.from(VAZIOS_SEL)
    }}, '*');
  }} else {{
    // Modo normal: seleção única
    if (selectedEl) selectedEl.classList.remove('selecionado_bipagem');
    selectedEl = el;
    el.classList.add('selecionado_bipagem');
    try {{
      const url = new URL(window.parent.location.href);
      url.searchParams.set('pos', p.endereco);
      window.parent.location.href = url.toString();
    }} catch (err) {{
      window.parent.postMessage({{type:'inv_select', endereco: p.endereco}}, '*');
    }}
  }}
}}

window.addEventListener('message', e => {{
  if (!e.data) return;
  if (e.data.type === 'inv_update') {{
    const {{endereco, cls, ua_fisica, ts}} = e.data;
    const el = document.getElementById('pos_' + endereco.replace(/[^A-Z0-9]/g,'_'));
    if (!el) return;
    el.className = 'pos ' + cls;
    el.dataset.cls = cls;
    const p = POSICOES.find(x => x.endereco === endereco);
    if (p) {{ p.cls = cls; if (ua_fisica) p.ua_fisica = ua_fisica; if (ts) p.ts = ts; }}
  }}
  if (e.data.type === 'inv_deselect') {{
    if (selectedEl) {{ selectedEl.classList.remove('selecionado_bipagem'); selectedEl = null; }}
  }}
}});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
def show():
    # Recupera operador da sessão (vem do app.py via secrets)
    try:
        operador_logado = st.secrets["auth"]["login"].upper()
    except Exception:
        operador_logado = "OPERADOR"

    _init_state(operador_logado)
    st.markdown(_CSS, unsafe_allow_html=True)

    # ─── RESTAURA SELEÇÃO/RUA VINDA DA URL ───
    qp = st.query_params
    rua_url = str(qp.get("rua") or "").strip().upper()
    pos_url = str(qp.get("pos") or "").strip().upper()
    if rua_url:
        st.session_state["inv_rua"] = rua_url
    if pos_url:
        st.session_state["inv_pos_sel"] = pos_url

    # HEADER
    st.markdown("""
    <div class="inv-header">
      <h1 class="inv-title">INVENTÁRIO <em>DE POSIÇÕES</em></h1>
      <div class="inv-badge"><span class="inv-badge-dot"></span>CONTAGEM FÍSICA · ÁREA SECO</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── CARREGA DADOS (cacheado) ───
    try:
        df = _get_df()
    except Exception as e:
        st.error("Não foi possível conectar ao banco de dados.")
        st.exception(e)
        return

    if df is None or df.empty:
        st.info("Nenhum endereço retornado.")
        return

    todas_ruas = sorted(df["RUA"].dropna().unique().tolist(), key=lambda r: (len(str(r)), str(r)))

    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 1 — FILTROS OPERACIONAIS
    # ═══════════════════════════════════════════════════════════════
    st.markdown('<div class="sec-title">Filtros Operacionais</div>', unsafe_allow_html=True)

    col_rua, col_op, col_reset, col_modo_vazio = st.columns([3, 2, 1, 1])
    with col_rua:
        idx_rua = 0
        if st.session_state["inv_rua"] in todas_ruas:
            idx_rua = ([""] + todas_ruas).index(st.session_state["inv_rua"])
        rua_sel = st.selectbox(
            "Rua",
            options=[""] + todas_ruas,
            index=idx_rua,
            format_func=lambda r: f"Rua {r}" if r else "— Selecione uma rua —",
            label_visibility="collapsed",
            key="sel_rua",
        )
        if rua_sel != st.session_state["inv_rua"]:
            st.session_state["inv_rua"]      = rua_sel
            st.session_state["inv_pos_sel"]  = None
            st.session_state["inv_last_msg"] = None
            st.session_state["inv_vazios_sel"] = []
            if rua_sel:
                st.query_params["rua"] = rua_sel
            else:
                st.query_params.pop("rua", None)
            st.query_params.pop("pos", None)

    with col_op:
        st.text_input(
            "Operador",
            value=operador_logado,
            disabled=True,
            label_visibility="collapsed",
            key="txt_operador",
        )

    with col_reset:
        if st.button("⟳ Limpar rua", use_container_width=True):
            rua_atual = st.session_state["inv_rua"]
            if rua_atual:
                df_end = df[df["RUA"] == rua_atual]["ENDERECO"].tolist()
                for e in df_end:
                    st.session_state["inv_registros"].pop(e, None)
                _delete_registros_rua(operador_logado, df_end)
            st.session_state["inv_pos_sel"]    = None
            st.session_state["inv_last_msg"]   = None
            st.session_state["inv_vazios_sel"] = []
            st.session_state["inv_modo_vazio"] = False
            st.query_params.pop("pos", None)
            st.rerun()

    with col_modo_vazio:
        label_mv = "☐ Multi-Vazio" if not st.session_state["inv_modo_vazio"] else "✕ Sair Multi"
        if st.button(label_mv, use_container_width=True):
            st.session_state["inv_modo_vazio"] = not st.session_state["inv_modo_vazio"]
            st.session_state["inv_vazios_sel"] = []
            st.rerun()

    if not st.session_state["inv_rua"]:
        st.markdown("""
        <div style="margin-top:20px;" class="inv-hint">
            ↑ Selecione uma rua acima para iniciar a contagem de inventário.
        </div>
        """, unsafe_allow_html=True)
        return

    rua    = st.session_state["inv_rua"]
    df_rua = df[df["RUA"] == rua].copy()

    if df_rua.empty:
        st.info(f"Nenhuma posição encontrada para a rua {rua}.")
        return

    registros      = st.session_state["inv_registros"]
    total_pos      = len(df_rua)
    total_ocup     = int(df_rua["OCUPADO"].sum())
    enderecos_rua  = set(df_rua["ENDERECO"].tolist())

    n_ok       = sum(1 for e, r in registros.items() if e in enderecos_rua and r["status"] == "ok")
    n_div      = sum(1 for e, r in registros.items() if e in enderecos_rua and r["status"] != "ok")
    n_contados = n_ok + n_div
    n_pend     = max(total_ocup - n_contados, 0)
    pct        = (n_contados / total_ocup * 100) if total_ocup else 0
    pct_cor    = "#EF4444" if pct < 50 else ("#F59E0B" if pct < 100 else "#22C55E")

    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 2 — KPIs
    # ═══════════════════════════════════════════════════════════════
    st.markdown(f'<div class="sec-title">Indicadores do Inventário <span class="sec-count">RUA {rua}</span></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi kpi-info">
        <div class="kpi-label">Ocupadas</div>
        <div class="kpi-value">{total_ocup}</div>
        <div class="kpi-sub">posições com UA</div>
      </div>
      <div class="kpi kpi-amber">
        <div class="kpi-label">Inventariadas</div>
        <div class="kpi-value">{n_ok}</div>
        <div class="kpi-sub">conferidas OK</div>
      </div>
      <div class="kpi kpi-red">
        <div class="kpi-label">Divergências</div>
        <div class="kpi-value">{n_div}</div>
        <div class="kpi-sub">requerem atenção</div>
      </div>
      <div class="kpi kpi-muted">
        <div class="kpi-label">Pendentes</div>
        <div class="kpi-value">{n_pend}</div>
        <div class="kpi-sub">aguardando contagem</div>
      </div>
      <div class="kpi kpi-green">
        <div class="kpi-label">Concluído</div>
        <div class="kpi-value" style="color:{pct_cor};">{pct:.1f}%</div>
        <div class="kpi-sub">do total da rua</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 3 — PROGRESSO
    # ═══════════════════════════════════════════════════════════════
    st.markdown('<div class="sec-title">Progresso da Contagem</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="prog-card">
      <div class="prog-head">
        <div class="prog-head-left">Rua {rua} · {n_contados} de {total_ocup} posições</div>
        <div class="prog-head-right" style="color:{pct_cor};">{pct:.1f}%</div>
      </div>
      <div class="prog-track">
        <div class="prog-fill" style="width:{pct:.1f}%;--pcol:{pct_cor};"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # MODO MULTI-VAZIO
    # ═══════════════════════════════════════════════════════════════
    modo_vazio  = st.session_state["inv_modo_vazio"]
    vazios_sel  = st.session_state["inv_vazios_sel"]

    if modo_vazio:
        n_sel = len(vazios_sel)
        st.markdown(f"""
        <div class="modo-vazio-banner">
            ⚠ MODO SELEÇÃO MÚLTIPLA DE VAZIOS ATIVO — clique nas células <b>cinzas</b> (vazias) no mapa abaixo
            <span class="modo-vazio-count">{n_sel} selecionadas</span>
        </div>
        """, unsafe_allow_html=True)

        if n_sel > 0:
            col_conf_v, col_cancel_v = st.columns([2, 2])
            with col_conf_v:
                if st.button(f"✓ Confirmar {n_sel} posição(ões) como VAZIA", use_container_width=True):
                    ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    for end in list(vazios_sel):
                        row_e = df_rua[df_rua["ENDERECO"] == end]
                        if row_e.empty:
                            continue
                        ua_sys = str(row_e.iloc[0]["UA"]) if pd.notna(row_e.iloc[0].get("UA")) else None
                        if ua_sys:
                            reg = {"ua_sistema": ua_sys, "ua_fisica": None,
                                   "status": "divergente", "tipo": "vazio_fisico",
                                   "ts": ts, "op": operador_logado}
                        else:
                            reg = {"ua_sistema": None, "ua_fisica": None,
                                   "status": "ok", "tipo": "vazio_confirmado",
                                   "ts": ts, "op": operador_logado}
                        registros[end] = reg
                        _save_registro(operador_logado, end, reg)

                    st.session_state["inv_last_msg"] = (
                        "ok",
                        f"✓ {n_sel} posição(ões) marcada(s) como vazia(s)",
                        f"{ts} · Op: {operador_logado}"
                    )
                    st.session_state["inv_vazios_sel"] = []
                    st.session_state["inv_modo_vazio"] = False
                    st.rerun()
            with col_cancel_v:
                if st.button("✕ Limpar seleção", use_container_width=True):
                    st.session_state["inv_vazios_sel"] = []
                    st.rerun()

    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 4 — POSIÇÃO SELECIONADA (modo normal)
    # ═══════════════════════════════════════════════════════════════
    if not modo_vazio:
        st.markdown('<div class="sec-title">Posição Selecionada</div>', unsafe_allow_html=True)

        pos_sel = st.session_state["inv_pos_sel"]
        enderecos_rua_list = sorted(df_rua["ENDERECO"].tolist())
        pos_url_atual = str(st.query_params.get("pos") or "").strip().upper()
        if pos_url_atual in enderecos_rua_list:
            st.session_state["inv_pos_sel"] = pos_url_atual
            pos_sel = pos_url_atual

        pos_idx = 0
        opts_pos = ["— Selecione a posição —"] + enderecos_rua_list
        if pos_sel in enderecos_rua_list:
            pos_idx = enderecos_rua_list.index(pos_sel) + 1
        pos_escolhida = st.selectbox(
            "Posição",
            options=opts_pos,
            index=pos_idx,
            label_visibility="collapsed",
            key="sel_posicao",
        )
        if pos_url_atual in enderecos_rua_list and pos_escolhida == "— Selecione a posição —":
            pos_sel = pos_url_atual
        elif pos_escolhida != "— Selecione a posição —":
            st.session_state["inv_pos_sel"] = pos_escolhida
            pos_sel = pos_escolhida
            if st.query_params.get("pos") != pos_escolhida:
                st.query_params["pos"] = pos_escolhida
        else:
            st.session_state["inv_pos_sel"] = None
            pos_sel = None
            if "pos" in st.query_params:
                st.query_params.pop("pos", None)

        if pos_sel:
            row_pos    = df_rua[df_rua["ENDERECO"] == pos_sel].iloc[0]
            ua_sistema = str(row_pos["UA"]) if pd.notna(row_pos.get("UA")) else None
            ua_sys_display = ua_sistema if ua_sistema else "—"
            ocupado    = bool(row_pos["OCUPADO"])
            status_cls = "ocupado" if ocupado else "vazio"
            status_txt = "● Ocupado" if ocupado else "○ Vazio no sistema"
            st.markdown(f"""
            <div class="pos-card">
              <div class="pin">📍</div>
              <div class="pos-block">
                <span class="k">Endereço</span>
                <span class="v addr">{pos_sel}</span>
              </div>
              <div class="pos-block">
                <span class="k">UA Sistema</span>
                <span class="v">{ua_sys_display}</span>
              </div>
              <div class="pos-block">
                <span class="k">Nível · Posição</span>
                <span class="v">N{int(row_pos['NIVEL']):02d} · {int(row_pos['POSICAO']):02d}</span>
              </div>
              <div class="pos-status {status_cls}">{status_txt}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            ua_sistema = None
            ocupado    = False
            st.markdown("""
            <div class="pos-empty">
                Selecione a posição ou clique em alguma célula no mapa abaixo.
            </div>
            """, unsafe_allow_html=True)

        # ═══════════════════════════════════════════════════════════
        # SEÇÃO 5 — ÁREA DE CONFERÊNCIA (modo normal)
        # ═══════════════════════════════════════════════════════════
        st.markdown('<div class="sec-title">Área de Conferência</div>', unsafe_allow_html=True)

        with st.form(key="form_bipar", clear_on_submit=True):
            col_ua, col_conf, col_div, col_vazio = st.columns([3, 1, 1, 1])
            with col_ua:
                ua_input = st.text_input(
                    "UA",
                    placeholder="Bipe ou digite a U.A encontrada fisicamente",
                    label_visibility="collapsed",
                )
            with col_conf:
                btn_ok = st.form_submit_button("✓ Confirmar", use_container_width=True)
            with col_div:
                btn_div = st.form_submit_button("⚠ Divergência", use_container_width=True)
            with col_vazio:
                btn_vazio = st.form_submit_button("✕ Vazio", use_container_width=True)

        if not pos_sel:
            pos_url_submit = str(st.query_params.get("pos") or "").strip().upper()
            if pos_url_submit in enderecos_rua:
                st.session_state["inv_pos_sel"] = pos_url_submit
                pos_sel    = pos_url_submit
                row_pos    = df_rua[df_rua["ENDERECO"] == pos_sel].iloc[0]
                ua_sistema = str(row_pos["UA"]) if pd.notna(row_pos.get("UA")) else None
                ocupado    = bool(row_pos["OCUPADO"])

        msg = None
        if (btn_ok or btn_div or btn_vazio) and pos_sel:
            ua_fisica = ua_input.strip().upper() if ua_input else ""
            ts        = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            reg       = registros

            if btn_vazio:
                if ua_sistema:
                    reg[pos_sel] = {"ua_sistema": ua_sistema, "ua_fisica": None,
                                    "status": "divergente", "tipo": "vazio_fisico",
                                    "ts": ts, "op": operador_logado}
                    msg = ("warn", f"Divergência registrada — {pos_sel}",
                           f"Sistema: UA {ua_sistema} · Físico: VAZIO · {ts}")
                else:
                    reg[pos_sel] = {"ua_sistema": None, "ua_fisica": None,
                                    "status": "ok", "tipo": "vazio_confirmado",
                                    "ts": ts, "op": operador_logado}
                    msg = ("ok", f"Posição vazia confirmada — {pos_sel}", f"{ts} · Op: {operador_logado}")
            elif btn_div:
                reg[pos_sel] = {"ua_sistema": ua_sistema, "ua_fisica": ua_fisica or None,
                                "status": "divergente", "tipo": "manual",
                                "ts": ts, "op": operador_logado}
                msg = ("warn", f"Divergência registrada — {pos_sel}",
                       f"UA Sistema: {ua_sistema or '—'} · UA Física: {ua_fisica or '—'} · {ts}")
            elif btn_ok:
                if not ua_fisica:
                    msg = ("err", "Digite ou bipe a UA antes de confirmar.", "")
                elif not ua_sistema:
                    reg[pos_sel] = {"ua_sistema": None, "ua_fisica": ua_fisica,
                                    "status": "divergente", "tipo": "fantasma",
                                    "ts": ts, "op": operador_logado}
                    msg = ("warn", f"Divergência — palete fantasma em {pos_sel}",
                           f"UA Física: {ua_fisica} · Sistema: endereço vazio · {ts}")
                elif ua_fisica == ua_sistema:
                    reg[pos_sel] = {"ua_sistema": ua_sistema, "ua_fisica": ua_fisica,
                                    "status": "ok", "tipo": "correto",
                                    "ts": ts, "op": operador_logado}
                    msg = ("ok", f"✓ Inventariado — {pos_sel}",
                           f"UA {ua_fisica} · {ts} · Op: {operador_logado}")
                else:
                    reg[pos_sel] = {"ua_sistema": ua_sistema, "ua_fisica": ua_fisica,
                                    "status": "divergente", "tipo": "ua_errada",
                                    "ts": ts, "op": operador_logado}
                    msg = ("warn", f"Divergência — UA incorreta em {pos_sel}",
                           f"Sistema: {ua_sistema} · Físico: {ua_fisica} · {ts}")

            # Persiste no banco
            if pos_sel in registros:
                _save_registro(operador_logado, pos_sel, registros[pos_sel])

            st.session_state["inv_last_msg"] = msg
            if msg:
                st.rerun()

        elif (btn_ok or btn_div or btn_vazio) and not pos_sel:
            st.session_state["inv_last_msg"] = ("err", "Selecione uma posição antes de confirmar.", "")
            st.rerun()

    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 6 — ÚLTIMA LEITURA
    # ═══════════════════════════════════════════════════════════════
    lr = st.session_state.get("inv_last_msg")
    if lr:
        tipo, texto, detalhe = lr
        css_cls = "read-ok" if tipo == "ok" else ("read-warn" if tipo == "warn" else "read-err")
        icon    = "✓" if tipo == "ok" else ("⚠" if tipo == "warn" else "✗")
        st.markdown('<div class="sec-title">Última Leitura</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="read-card {css_cls}">
          <div class="read-icon">{icon}</div>
          <div>
            <div class="read-main">{texto}</div>
            <div class="read-detail">{detalhe}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # SEÇÃO 7 — MAPA DE POSIÇÕES
    # ═══════════════════════════════════════════════════════════════
    st.markdown(f'<div class="sec-title">Mapa de Posições <span class="sec-count">RUA {rua} · {total_pos} células</span></div>', unsafe_allow_html=True)

    pos_sel = st.session_state.get("inv_pos_sel") if not modo_vazio else None

    posicoes_html = []
    for _, row in df_rua.iterrows():
        end    = row["ENDERECO"]
        reg_e  = registros.get(end)
        ua_val = str(row["UA"]) if pd.notna(row.get("UA")) else ""

        if reg_e:
            cls       = "ok" if reg_e["status"] == "ok" else "divergente"
            ua_fisica = reg_e.get("ua_fisica") or ""
            inv_ts    = reg_e.get("ts", "")
        elif row["OCUPADO"]:
            cls, ua_fisica, inv_ts = "pendente", "", ""
        else:
            cls, ua_fisica, inv_ts = "vazio", "", ""

        if pos_sel and end == pos_sel and not reg_e:
            cls = "selecionado_bipagem"

        posicoes_html.append({
            "endereco": end,
            "rua":      str(row["RUA"]),
            "nivel":    int(row["NIVEL"]),
            "posicao":  int(row["POSICAO"]),
            "ua":       ua_val,
            "ua_fisica": ua_fisica,
            "cls":      cls,
            "ts":       inv_ts,
        })

    niveis_uniq = df_rua["NIVEL"].nunique()
    altura_grid = max(480, min(niveis_uniq * 60 + 200, 820))

    grid_html = _build_grid_html(posicoes_html, rua, modo_vazio, vazios_sel)
    components.html(grid_html, height=altura_grid, scrolling=True)

    # ═══════════════════════════════════════════════════════════════
    # TABELAS RESUMO
    # ═══════════════════════════════════════════════════════════════
    st.markdown('<div class="sec-title">Detalhamento</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["✓ Inventariados", "⚠ Divergências", "⏳ Pendentes"])

    with tab1:
        rows_ok = [
            {"Endereço": e, "UA Sistema": r["ua_sistema"] or "—",
             "UA Física": r["ua_fisica"] or "—",
             "Data/Hora": r["ts"], "Operador": r["op"]}
            for e, r in registros.items()
            if e in enderecos_rua and r["status"] == "ok"
        ]
        if rows_ok:
            st.dataframe(pd.DataFrame(rows_ok), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhuma posição inventariada ainda.")

    with tab2:
        rows_div = [
            {"Endereço": e, "UA Sistema": r["ua_sistema"] or "—",
             "UA Física": r["ua_fisica"] or "—",
             "Tipo": r.get("tipo", "—"),
             "Data/Hora": r["ts"], "Operador": r["op"]}
            for e, r in registros.items()
            if e in enderecos_rua and r["status"] != "ok"
        ]
        if rows_div:
            st.dataframe(pd.DataFrame(rows_div), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhuma divergência registrada.")

    with tab3:
        contados_set = set(registros.keys()) & enderecos_rua
        pend_df = df_rua[
            df_rua["OCUPADO"] & ~df_rua["ENDERECO"].isin(contados_set)
        ][["ENDERECO", "NIVEL", "POSICAO", "UA"]].copy()
        pend_df = pend_df.rename(columns={"NIVEL": "NÍVEL", "POSICAO": "POSIÇÃO"})
        if not pend_df.empty:
            st.dataframe(pend_df.reset_index(drop=True), use_container_width=True, hide_index=True)
        else:
            if total_ocup:
                st.success(f"✓ Todas as {total_ocup} posições ocupadas foram conferidas!")

    # ═══════════════════════════════════════════════════════════════
    # EXPORTAR
    # ═══════════════════════════════════════════════════════════════
    if registros:
        export_rows = []
        for _, row in df_rua.iterrows():
            end  = row["ENDERECO"]
            reg_e = registros.get(end)
            if reg_e:
                st_inv = "OK" if reg_e["status"] == "ok" else "DIVERGENTE"
                info   = reg_e
            elif row["OCUPADO"]:
                st_inv, info = "PENDENTE", {}
            else:
                st_inv, info = "LIVRE", {}

            export_rows.append({
                "RUA": str(row["RUA"]), "ENDERECO": end,
                "NIVEL": int(row["NIVEL"]), "POSICAO": int(row["POSICAO"]),
                "UA_SISTEMA": str(row["UA"]) if pd.notna(row.get("UA")) else "",
                "UA_FISICA":  info.get("ua_fisica") or "",
                "STATUS_WMS": str(row["STATUS"]), "STATUS_INV": st_inv,
                "TIPO": info.get("tipo", ""),
                "DATA_CONF": info.get("ts", ""), "OPERADOR": info.get("op", ""),
            })

        csv_bytes = pd.DataFrame(export_rows).to_csv(
            index=False, sep=";").encode("utf-8-sig")

        col_e1, _ = st.columns([2, 4])
        with col_e1:
            st.download_button(
                label="⬇ Exportar CSV",
                data=csv_bytes,
                file_name=f"inventario_rua_{rua}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )