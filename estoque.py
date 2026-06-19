import streamlit as st
import pandas as pd
import json
import re
import streamlit.components.v1 as components
from db import get_engine


@st.cache_data(ttl=60, show_spinner=False)
def _load_estoque():
    query = """
    SELECT
        ENDERECO,
        STATUS,
        AREA,
        UA
    FROM db_visual_SALOG.dbo.VW_PAINEL_STATUS_ENDERECOS_ARMAZEM
    WHERE AREA = 'SECO'
      AND ENDERECO IS NOT NULL
    """
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)


def show():

    # =========================
    # ESTILOS GLOBAIS — DARK PREMIUM
    # =========================
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    * { box-sizing: border-box; }

    /* ── Cores base ── */
    :root {
        --bg:       #0F172A;
        --surface:  #1E293B;
        --surface2: #273548;
        --border:   rgba(148,163,184,0.12);
        --border2:  rgba(148,163,184,0.20);
        --text:     #F8FAFC;
        --muted:    #94A3B8;
        --green:    #22C55E;
        --amber:    #F59E0B;
        --red:      #EF4444;
        --blue:     #3B82F6;
        --cyan:     #06B6D4;
        --purple:   #8B5CF6;
        --mono:     'JetBrains Mono', monospace;
        --sans:     'Inter', sans-serif;
    }

    /* ── Reset Streamlit ── */
    html, body, [class*="css"] { font-family: var(--sans) !important; }
    .stApp { background: var(--bg) !important; }
    .block-container { padding: 1.5rem 2rem 2rem !important; max-width: 100% !important; }
    div[data-testid="stVerticalBlock"] { gap: 0 !important; }
    .stMarkdown { margin: 0 !important; }

    /* ── Hero header ── */
    .dt-hero {
        position: relative;
        background: linear-gradient(135deg, #0F172A 0%, #162032 50%, #0F172A 100%);
        border: 1px solid rgba(59,130,246,0.20);
        border-radius: 14px;
        padding: 28px 36px 24px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .dt-hero-bg {
        position: absolute; inset: 0; pointer-events: none;
        background-image:
            linear-gradient(rgba(59,130,246,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59,130,246,0.025) 1px, transparent 1px);
        background-size: 44px 44px;
    }
    .dt-hero-glow {
        position: absolute; inset: 0; pointer-events: none;
        background: radial-gradient(ellipse at 80% 50%, rgba(59,130,246,0.08) 0%, transparent 60%);
    }
    .dt-hero-inner { position: relative; z-index: 1; }
    .dt-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(59,130,246,0.10);
        border: 1px solid rgba(59,130,246,0.30);
        border-radius: 6px; padding: 4px 12px;
        font-family: var(--mono); font-size: 10px; font-weight: 600;
        color: #60A5FA; letter-spacing: 0.14em; margin-bottom: 12px;
    }
    .dt-pulse {
        width: 6px; height: 6px; border-radius: 50%;
        background: #22C55E; flex-shrink: 0;
        animation: pulse-anim 2s ease-in-out infinite;
    }
    @keyframes pulse-anim {
        0%, 100% { opacity: 1; box-shadow: 0 0 6px #22C55E; }
        50% { opacity: 0.3; box-shadow: none; }
    }
    .dt-title {
        font-size: 2.2rem; font-weight: 800;
        color: var(--text); letter-spacing: -0.04em; line-height: 1.1;
        margin: 0 0 6px;
    }
    .dt-title em { font-style: normal; color: #60A5FA; }
    .dt-sub {
        font-family: var(--mono); font-size: 11px;
        color: var(--muted); letter-spacing: 0.05em; margin: 0;
    }

    /* ── KPI Cards ── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    @media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 18px 20px 16px;
        transition: border-color 0.2s, transform 0.2s;
        cursor: default;
    }
    .kpi-card:hover {
        border-color: var(--border2);
        transform: translateY(-1px);
    }
    .kpi-label {
        font-size: 11px; font-weight: 500; color: var(--muted);
        letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 10px;
        display: flex; align-items: center; gap: 6px;
    }
    .kpi-icon { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .kpi-value {
        font-family: var(--mono); font-size: 28px; font-weight: 700;
        color: var(--text); letter-spacing: -0.03em; line-height: 1;
        margin-bottom: 6px;
    }
    .kpi-sub { font-size: 11px; color: var(--muted); }
    .kpi-bar {
        height: 3px; background: rgba(148,163,184,0.10);
        border-radius: 2px; margin-top: 12px; overflow: hidden;
    }
    .kpi-bar-fill { height: 100%; border-radius: 2px; transition: width 0.8s ease; }

    /* ── Toolbar ── */
    .dt-toolbar {
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 14px; flex-wrap: wrap;
    }
    .dt-toolbar-group {
        display: flex; align-items: center; gap: 6px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px; padding: 5px 6px;
    }
    .dt-divider-v {
        width: 1px; height: 22px;
        background: var(--border); margin: 0 4px;
    }

    /* ── Inputs override ── */
    div[data-testid="stTextInput"] > div > div > input {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        font-family: var(--mono) !important;
        font-size: 13px !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    div[data-testid="stTextInput"] > div > div > input:focus {
        border-color: rgba(59,130,246,0.50) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.08) !important;
        outline: none !important;
    }
    div[data-testid="stMultiSelect"] > div > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }
    div[data-testid="stExpander"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    /* ── Hint ── */
    .dt-hint {
        display: flex; align-items: center; gap: 12px;
        background: rgba(59,130,246,0.05);
        border: 1px solid rgba(59,130,246,0.14);
        border-radius: 10px; padding: 14px 18px;
        font-size: 13px; color: rgba(148,163,184,0.85);
        margin-top: 14px;
    }
    .dt-hint-icon { font-size: 16px; flex-shrink: 0; }

    /* ── Section label ── */
    .dt-section {
        display: flex; align-items: center; gap: 10px;
        margin: 18px 0 10px;
    }
    .dt-section-line {
        flex: 1; height: 1px;
        background: linear-gradient(90deg, var(--border2), transparent);
    }
    .dt-section-label {
        font-family: var(--mono); font-size: 10px; font-weight: 600;
        color: rgba(148,163,184,0.45); letter-spacing: 0.18em;
        white-space: nowrap; text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

    # =========================
    # HERO
    # =========================
    st.markdown("""
    <div class="dt-hero">
      <div class="dt-hero-bg"></div>
      <div class="dt-hero-glow"></div>
      <div class="dt-hero-inner">
        <div class="dt-badge">
          <span class="dt-pulse"></span>
          DIGITAL TWIN · ÁREA SECO · LIVE OPERATIONS
        </div>
        <h1 class="dt-title">CENTRO DE DISTRIBUIÇÃO <em>3D</em></h1>
        <p class="dt-sub">// drag → rotacionar &nbsp;·&nbsp; shift+drag → deslocar &nbsp;·&nbsp; scroll → zoom &nbsp;·&nbsp; clique → detalhes &nbsp;·&nbsp; dblclick → reset câmera</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # QUERY  (cacheada)
    # =========================
    try:
        df = _load_estoque()
    except Exception as e:
        st.error("Não foi possível conectar ao banco de dados.")
        st.exception(e)
        return

    if df.empty:
        st.info("Nenhum endereço retornado pela consulta (AREA = 'SECO').")
        return

    # =========================
    # NORMALIZAÇÃO  (inalterada)
    # =========================
    df["ENDERECO"] = df["ENDERECO"].astype(str).str.strip().str.upper()
    df["STATUS"]   = df["STATUS"].astype(str).str.strip().str.upper()
    if "UA" in df.columns:
        df["UA"] = df["UA"].astype(str).str.strip()
        df.loc[df["UA"].isin(["NAN", "NONE", ""]), "UA"] = None

    LIVRES     = {"LIVRE", "VAZIO", "VAZIA", "DISPONIVEL", "DISPONÍVEL", ""}
    BLOQUEADOS = {"BLOQUEADO", "BLOQUEADA", "BLOCKED", "INATIVO", "INATIVA"}
    df["OCUPADO"]   = ~df["STATUS"].isin(LIVRES) & ~df["STATUS"].isin(BLOQUEADOS)
    df["BLOQUEADO"] = df["STATUS"].isin(BLOQUEADOS)

    # =========================
    # PARSE ENDERECO  (inalterado)
    # =========================
    def parse_endereco(end):
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

    total_enderecos_view = len(df)
    parsed = df["ENDERECO"].apply(
        lambda e: pd.Series(parse_endereco(e), index=["RUA", "NIVEL", "POSICAO"])
    )
    df_full = pd.concat([df.reset_index(drop=True), parsed.reset_index(drop=True)], axis=1)
    nao_reconhecidos = df_full[df_full["RUA"].isna()]["ENDERECO"].dropna().unique().tolist()
    df = df_full.dropna(subset=["RUA", "NIVEL", "POSICAO"]).copy()
    df["NIVEL"]   = df["NIVEL"].astype(int)
    df["POSICAO"] = df["POSICAO"].astype(int)
    reconhecidos = len(df)

    # =========================
    # LÓGICA DE TÚNEL  (inalterada)
    # =========================
    NIVEIS_TUNEL = {1, 2, 3}
    df["TUNEL"] = df["BLOQUEADO"] & df["NIVEL"].isin(NIVEIS_TUNEL)
    df.loc[df["TUNEL"], "BLOQUEADO"] = False

    with st.expander(
        f"⬡ Diagnóstico de parsing — {reconhecidos:,}/{total_enderecos_view:,} endereços reconhecidos",
        expanded=False
    ):
        st.write(f"**Endereços SECO totais:** {total_enderecos_view:,}")
        st.write(f"**Reconhecidos (RUA-NÍVEL-POSIÇÃO):** {reconhecidos:,}")
        st.write(f"**Não reconhecidos:** {len(nao_reconhecidos):,}")
        tuneis_count = int(df["TUNEL"].sum())
        st.write(f"**Túneis de empilhadeira (níveis 1-3, bloqueados):** {tuneis_count:,}")
        if nao_reconhecidos:
            st.caption("Exemplos de ENDERECO que não bateram com o parser:")
            st.dataframe(
                pd.DataFrame({"ENDERECO": nao_reconhecidos[:30]}),
                use_container_width=True
            )

    if df.empty:
        st.warning("Nenhum endereço com formato reconhecível foi encontrado para a área SECO.")
        return

    def ordena_ruas(ruas):
        return sorted(ruas, key=lambda r: (len(str(r)), str(r)))

    todas_ruas = ordena_ruas(df["RUA"].dropna().unique().tolist())

    # =========================
    # BUSCA POR U.A  (lógica inalterada)
    # =========================
    st.markdown("""
    <div class="dt-section">
        <span class="dt-section-label">// LOCALIZAR U.A</span>
        <div class="dt-section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    col_ua1, col_ua2 = st.columns([3, 2])
    with col_ua1:
        ua_input = st.text_input(
            "U.A",
            value="",
            placeholder="Digite o número da U.A — ex.: 12345678",
            help="Informe a U.A para localizar o endereço correspondente.",
            label_visibility="collapsed",
        ).strip()

    rua_destacar = None
    if ua_input:
        if "UA" not in df.columns:
            st.error("A coluna UA não está disponível na view.")
        else:
            achados = df[df["UA"].astype(str).str.contains(ua_input, case=False, na=False)]
            if achados.empty:
                with col_ua2:
                    st.warning(f"Nenhum endereço encontrado para U.A '{ua_input}'.")
            else:
                with col_ua2:
                    st.success(f"{len(achados)} endereço(s) encontrado(s).")
                st.dataframe(
                    achados[["UA", "ENDERECO", "RUA", "NIVEL", "POSICAO", "STATUS"]]
                        .rename(columns={"NIVEL": "NÍVEL", "POSICAO": "POSIÇÃO"})
                        .reset_index(drop=True),
                    use_container_width=True,
                )
                rua_destacar = sorted(
                    achados["RUA"].unique().tolist(),
                    key=lambda r: (len(str(r)), str(r))
                )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # =========================
    # FILTRO DE RUA  (lógica inalterada)
    # =========================
    st.markdown("""
    <div class="dt-section">
        <span class="dt-section-label">// SELECIONAR RUAS</span>
        <div class="dt-section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    if "ruas_sel" not in st.session_state:
        st.session_state["ruas_sel"] = []

    if rua_destacar:
        for r in rua_destacar:
            if r not in st.session_state["ruas_sel"]:
                st.session_state["ruas_sel"].append(r)

    ruas_sel = st.multiselect(
        "Ruas",
        options=todas_ruas,
        key="ruas_sel",
        help="Escolha as ruas que deseja visualizar no armazém 3D.",
        label_visibility="collapsed",
    )

    if not ruas_sel:
        st.markdown("""
        <div class="dt-hint">
            <span class="dt-hint-icon">↑</span>
            Selecione pelo menos uma rua para renderizar o Digital Twin 3D do armazém.
        </div>
        """, unsafe_allow_html=True)
        return

    df_view = df[df["RUA"].isin(ruas_sel)].copy()
    if df_view.empty:
        st.info("Nenhum endereço para as ruas selecionadas.")
        return

    enderecos_destaque = set()
    if ua_input:
        try:
            enderecos_destaque = set(
                df[df["UA"].astype(str).str.contains(ua_input, case=False, na=False)]["ENDERECO"].tolist()
            )
        except Exception:
            enderecos_destaque = set()

    # =========================
    # MÉTRICAS  (cálculos inalterados)
    # =========================
    df_nao_tunel = df_view[~df_view["TUNEL"]]
    TOTAL_ENDERECOS      = len(df_nao_tunel)
    enderecos_ocupados   = int(df_nao_tunel["OCUPADO"].sum())
    enderecos_bloqueados = int(df_nao_tunel["BLOQUEADO"].sum())
    enderecos_vazios     = TOTAL_ENDERECOS - enderecos_ocupados - enderecos_bloqueados
    taxa_ocupacao        = (enderecos_ocupados / TOTAL_ENDERECOS * 100) if TOTAL_ENDERECOS else 0
    total_uas            = int(df_nao_tunel["UA"].notna().sum()) if "UA" in df_nao_tunel.columns else 0
    ruas_ativas          = len(ruas_sel)

    if taxa_ocupacao < 60:
        taxa_cor = "#22C55E"
        taxa_ico = "#22C55E"
    elif taxa_ocupacao < 85:
        taxa_cor = "#F59E0B"
        taxa_ico = "#F59E0B"
    else:
        taxa_cor = "#EF4444"
        taxa_ico = "#EF4444"

    # =========================
    # KPI CARDS — STRIPE STYLE
    # =========================
    st.markdown(f"""
    <div class="kpi-grid">

      <div class="kpi-card">
        <div class="kpi-label">
          <span class="kpi-icon" style="background:#3B82F6;"></span>
          Total de Posições
        </div>
        <div class="kpi-value">{TOTAL_ENDERECOS:,}</div>
        <div class="kpi-sub">{ruas_ativas} rua(s) selecionada(s)</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:100%;background:#3B82F6;"></div></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">
          <span class="kpi-icon" style="background:#22C55E;"></span>
          Posições Ocupadas
        </div>
        <div class="kpi-value" style="color:#22C55E;">{enderecos_ocupados:,}</div>
        <div class="kpi-sub">{enderecos_ocupados/TOTAL_ENDERECOS*100:.1f}% do total</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{enderecos_ocupados/TOTAL_ENDERECOS*100:.1f}%;background:#22C55E;"></div></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">
          <span class="kpi-icon" style="background:#EF4444;"></span>
          Posições Livres
        </div>
        <div class="kpi-value" style="color:#EF4444;">{enderecos_vazios:,}</div>
        <div class="kpi-sub">{enderecos_vazios/TOTAL_ENDERECOS*100:.1f}% disponível</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{enderecos_vazios/TOTAL_ENDERECOS*100:.1f}%;background:#EF4444;"></div></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">
          <span class="kpi-icon" style="background:{taxa_ico};"></span>
          Taxa de Ocupação
        </div>
        <div class="kpi-value" style="color:{taxa_cor};">{taxa_ocupacao:.1f}<span style="font-size:16px;font-weight:400;color:#94A3B8;">%</span></div>
        <div class="kpi-sub">Meta: &lt; 85%</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{min(taxa_ocupacao,100):.1f}%;background:{taxa_cor};"></div></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">
          <span class="kpi-icon" style="background:#8B5CF6;"></span>
          Total de UAs
        </div>
        <div class="kpi-value" style="color:#A78BFA;">{total_uas:,}</div>
        <div class="kpi-sub">Unidades de armazenamento</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{total_uas/max(enderecos_ocupados,1)*100:.1f}%;background:#8B5CF6;"></div></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">
          <span class="kpi-icon" style="background:#F59E0B;"></span>
          Bloqueadas
        </div>
        <div class="kpi-value" style="color:#F59E0B;">{enderecos_bloqueados:,}</div>
        <div class="kpi-sub">Endereços indisponíveis</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{enderecos_bloqueados/max(TOTAL_ENDERECOS,1)*100:.1f}%;background:#F59E0B;"></div></div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    # =========================
    # PREPARAÇÃO DOS DADOS 3D  (lógica inalterada)
    # =========================
    ruas_unicas = ordena_ruas(df_view["RUA"].unique().tolist())
    rua_idx = {r: i for i, r in enumerate(ruas_unicas)}

    minimap_data = []
    for rua in ruas_unicas:
        sub = df_view[(df_view["RUA"] == rua) & (~df_view["TUNEL"])]
        total_r = len(sub)
        ocup_r  = int(sub["OCUPADO"].sum())
        blk_r   = int(sub["BLOQUEADO"].sum())
        pct_r   = round(ocup_r / total_r * 100, 1) if total_r else 0
        minimap_data.append({
            "rua": rua,
            "total": total_r,
            "ocupados": ocup_r,
            "bloqueados": blk_r,
            "pct": pct_r,
        })
    minimap_json = json.dumps(minimap_data)

    cubos = []
    for _, row in df_view.iterrows():
        cubos.append({
            "x": int(row["POSICAO"]),
            "y": int(row["NIVEL"]),
            "z": rua_idx[row["RUA"]],
            "rua": str(row["RUA"]),
            "nivel": int(row["NIVEL"]),
            "posicao": int(row["POSICAO"]),
            "occupied": bool(row["OCUPADO"]),
            "blocked": bool(row["BLOQUEADO"]),
            "tunnel": bool(row["TUNEL"]),
            "label": str(row["ENDERECO"]),
            "ua": str(row["UA"]) if "UA" in df_view.columns and pd.notna(row.get("UA")) else "",
            "status": str(row["STATUS"]),
            "highlight": bool(row["ENDERECO"] in enderecos_destaque),
        })

    cubos_json     = json.dumps(cubos)
    ruas_json      = json.dumps(ruas_unicas)
    auto_focus_rua = (len(ruas_unicas) == 1)

    # =========================
    # THREE.JS — DIGITAL TWIN 3D PREMIUM
    # =========================
    html_3d = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#0F172A;--surface:#1E293B;--surface2:#273548;
  --border:rgba(148,163,184,0.12);--border2:rgba(148,163,184,0.22);
  --text:#F8FAFC;--muted:#94A3B8;
  --green:#22C55E;--amber:#F59E0B;--red:#EF4444;
  --blue:#3B82F6;--cyan:#06B6D4;--purple:#8B5CF6;
  --mono:'JetBrains Mono',monospace;--sans:'Inter',sans-serif;
}}
body{{background:var(--bg);overflow:hidden;font-family:var(--sans);}}
#cc{{width:100vw;height:100vh;position:relative;}}
canvas{{display:block;}}
canvas.can-hover{{cursor:crosshair;}}

/* scanline overlay */
#cc::after{{
  content:'';position:absolute;inset:0;pointer-events:none;z-index:2;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.018) 3px,rgba(0,0,0,0.018) 4px);
}}

/* ── Panel base ── */
.pnl{{
  position:absolute;z-index:10;
  background:rgba(15,23,42,0.88);
  border:1px solid var(--border2);
  border-radius:12px;
  backdrop-filter:blur(24px) saturate(1.8);
  -webkit-backdrop-filter:blur(24px) saturate(1.8);
  color:var(--text);overflow:hidden;
  box-shadow:0 20px 60px rgba(0,0,0,0.5),0 0 0 1px rgba(148,163,184,0.05);
}}
.pnl-head{{
  display:flex;align-items:center;gap:8px;
  padding:9px 14px 8px;
  border-bottom:1px solid var(--border);
  font-family:var(--mono);font-size:9px;font-weight:600;
  letter-spacing:0.18em;color:var(--muted);text-transform:uppercase;
}}
.pnl-dot{{
  width:5px;height:5px;border-radius:50%;
  background:var(--green);
  animation:dot-blink 2.5s ease-in-out infinite;
}}
@keyframes dot-blink{{0%,100%{{opacity:1;box-shadow:0 0 5px var(--green)}}50%{{opacity:0.25;box-shadow:none}}}}

/* ── HUD occupancy ── */
#hud{{top:16px;right:16px;min-width:224px;}}
.hud-body{{padding:14px 16px;}}
.occ-pct{{
  font-family:var(--mono);font-size:30px;font-weight:700;
  color:{taxa_cor};letter-spacing:-0.04em;line-height:1;margin-bottom:3px;
}}
.occ-pct span{{font-size:14px;font-weight:400;color:var(--muted);}}
.occ-label{{font-size:11px;color:var(--muted);margin-bottom:12px;}}
.occ-bar{{height:3px;background:rgba(148,163,184,0.10);border-radius:2px;overflow:hidden;margin-bottom:3px;}}
.occ-fill{{height:100%;border-radius:2px;background:{taxa_cor};width:{taxa_ocupacao:.1f}%;}}
.occ-ticks{{display:flex;justify-content:space-between;font-family:var(--mono);font-size:8px;color:var(--muted);margin-bottom:12px;}}
.sep{{height:1px;background:var(--border);margin:10px 0;}}
.stat{{display:flex;justify-content:space-between;align-items:center;padding:3.5px 0;font-size:11.5px;}}
.stat-l{{display:flex;align-items:center;gap:8px;color:var(--muted);}}
.stat-sq{{width:7px;height:7px;border-radius:1.5px;flex-shrink:0;}}
.stat-v{{font-family:var(--mono);font-size:11.5px;font-weight:600;color:var(--text);}}

/* ── Minimap ruas ── */
#mm{{top:16px;left:16px;min-width:178px;max-width:200px;max-height:64vh;overflow-y:auto;}}
#mm::-webkit-scrollbar{{width:2px;}}
#mm::-webkit-scrollbar-thumb{{background:rgba(148,163,184,0.18);border-radius:1px;}}
.mm-body{{padding:10px 14px;}}
.mm-row{{display:flex;align-items:center;gap:8px;margin-bottom:8px;}}
.mm-row:last-child{{margin-bottom:0;}}
.mm-lbl{{font-family:var(--mono);font-size:9.5px;font-weight:600;color:var(--muted);min-width:28px;}}
.mm-rail{{flex:1;height:3px;background:rgba(148,163,184,0.08);border-radius:2px;overflow:hidden;}}
.mm-bar{{height:100%;border-radius:2px;}}
.mm-pct{{font-family:var(--mono);font-size:8.5px;font-weight:600;min-width:30px;text-align:right;}}

/* ── Camera controls ── */
#camctrl{{bottom:20px;right:16px;}}
.camctrl-body{{padding:10px 12px;display:flex;flex-direction:column;gap:6px;}}
.cam-btn-row{{display:flex;gap:6px;}}
.cam-btn{{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:7px;padding:6px 12px;
  font-family:var(--mono);font-size:10px;font-weight:600;
  color:var(--muted);cursor:pointer;flex:1;text-align:center;
  transition:background 0.15s,border-color 0.15s,color 0.15s;
  user-select:none;
}}
.cam-btn:hover{{background:rgba(59,130,246,0.12);border-color:rgba(59,130,246,0.35);color:var(--text);}}
.cam-btn.active{{background:rgba(59,130,246,0.18);border-color:rgba(59,130,246,0.50);color:#93C5FD;}}

/* ── Legend ── */
#leg{{bottom:20px;left:50%;transform:translateX(-50%);display:flex;align-items:stretch;}}
.leg-i{{
  display:flex;align-items:center;gap:7px;
  font-size:10.5px;color:var(--muted);
  padding:8px 14px;border-right:1px solid var(--border);
}}
.leg-i:last-child{{border-right:none;}}
.leg-sq{{width:9px;height:9px;border-radius:2px;flex-shrink:0;}}
.leg-tunnel{{display:flex;align-items:center;width:14px;height:9px;font-size:11px;color:var(--green);flex-shrink:0;}}

/* ── Activity ticker ── */
#ticker{{bottom:20px;left:16px;min-width:238px;max-width:272px;}}
.tick-body{{padding:8px 13px;}}
.tick-row{{
  display:flex;align-items:center;gap:8px;
  font-size:10px;color:var(--muted);
  padding:2.5px 0;font-family:var(--mono);
  opacity:0;animation:tick-in 0.4s ease forwards;
}}
@keyframes tick-in{{to{{opacity:1}}}}
.tick-dot{{width:5px;height:5px;border-radius:50%;flex-shrink:0;}}

/* ── Tooltip ── */
#tip{{
  display:none;position:absolute;z-index:30;
  min-width:210px;pointer-events:none;
  background:rgba(15,23,42,0.97);
  border:1px solid var(--border2);
  border-radius:12px;
  box-shadow:0 16px 60px rgba(0,0,0,0.7),0 0 0 1px rgba(148,163,184,0.05);
  overflow:hidden;
}}
.tip-head{{
  background:rgba(30,41,59,0.80);
  border-bottom:1px solid var(--border);
  padding:11px 15px 9px;
}}
.tip-addr{{font-family:var(--mono);font-size:14px;font-weight:700;color:var(--text);letter-spacing:0.02em;}}
.tip-st{{font-size:11px;font-weight:600;margin-top:4px;}}
.tip-body{{padding:11px 15px;}}
.tip-r{{display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:11.5px;}}
.tip-r:last-child{{margin-bottom:0;}}
.tip-k{{color:var(--muted);min-width:56px;}}
.tip-v{{color:var(--text);font-family:var(--mono);font-weight:500;}}
.tip-ua{{color:#93C5FD;}}
.tip-tunnel{{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.28);
  border-radius:5px;padding:3px 9px;
  font-family:var(--mono);font-size:9px;font-weight:600;
  color:var(--green);letter-spacing:0.10em;margin-top:6px;
}}

/* ── Detail panel (clique) ── */
#detail{{
  top:16px;right:260px;width:270px;
  display:none;z-index:20;
}}
.detail-body{{padding:14px 16px;}}
.detail-title{{
  font-family:var(--mono);font-size:18px;font-weight:700;
  color:var(--text);letter-spacing:0.02em;margin-bottom:4px;
}}
.detail-status{{font-size:12px;font-weight:600;margin-bottom:14px;}}
.detail-row{{
  display:flex;align-items:flex-start;gap:8px;
  padding:6px 0;border-bottom:1px solid var(--border);
  font-size:12px;
}}
.detail-row:last-child{{border-bottom:none;}}
.detail-k{{color:var(--muted);min-width:70px;flex-shrink:0;}}
.detail-v{{color:var(--text);font-family:var(--mono);font-weight:500;word-break:break-all;}}
.detail-close{{
  position:absolute;top:10px;right:12px;
  background:none;border:none;color:var(--muted);
  font-size:16px;cursor:pointer;padding:2px 6px;
  border-radius:4px;transition:color 0.15s;
  font-family:var(--sans);
}}
.detail-close:hover{{color:var(--text);background:rgba(148,163,184,0.10);}}
.detail-ua-badge{{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.30);
  border-radius:6px;padding:4px 10px;
  font-family:var(--mono);font-size:12px;font-weight:600;
  color:#93C5FD;margin-top:2px;
}}
.detail-highlight-badge{{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(234,179,8,0.12);border:1px solid rgba(234,179,8,0.30);
  border-radius:6px;padding:4px 10px;
  font-family:var(--mono);font-size:11px;font-weight:600;
  color:#FDE047;margin-top:8px;
}}
</style>
</head>
<body>
<div id="cc">

<!-- HUD: Ocupação -->
<div id="hud" class="pnl">
  <div class="pnl-head"><span class="pnl-dot"></span>OCUPAÇÃO — SELEÇÃO</div>
  <div class="hud-body">
    <div class="occ-pct">{taxa_ocupacao:.1f}<span>%</span></div>
    <div class="occ-label">taxa de ocupação</div>
    <div class="occ-bar"><div class="occ-fill"></div></div>
    <div class="occ-ticks"><span>0%</span><span>50%</span><span>100%</span></div>
    <div class="sep"></div>
    <div class="stat">
      <span class="stat-l"><span class="stat-sq" style="background:#22C55E;box-shadow:0 0 6px rgba(34,197,94,0.5);"></span>Ocupados</span>
      <span class="stat-v" style="color:#22C55E;">{enderecos_ocupados:,}</span>
    </div>
    <div class="stat">
      <span class="stat-l"><span class="stat-sq" style="background:#EF4444;opacity:0.7;"></span>Livres</span>
      <span class="stat-v" style="color:#EF4444;">{enderecos_vazios:,}</span>
    </div>
    <div class="stat">
      <span class="stat-l"><span class="stat-sq" style="background:#F59E0B;"></span>Bloqueados</span>
      <span class="stat-v" style="color:#F59E0B;">{enderecos_bloqueados:,}</span>
    </div>
    <div class="sep"></div>
    <div class="stat">
      <span class="stat-l" style="color:var(--muted);">Total</span>
      <span class="stat-v">{TOTAL_ENDERECOS:,}</span>
    </div>
    <div class="stat">
      <span class="stat-l" style="color:var(--muted);">UAs</span>
      <span class="stat-v" style="color:#A78BFA;">{total_uas:,}</span>
    </div>
  </div>
</div>

<!-- Minimap ruas -->
<div id="mm" class="pnl">
  <div class="pnl-head"><span class="pnl-dot"></span>RUAS</div>
  <div class="mm-body" id="mm-body"></div>
</div>

<!-- Detail panel (clique em endereço) -->
<div id="detail" class="pnl">
  <div class="pnl-head">
    <span class="pnl-dot"></span>DETALHE DO ENDEREÇO
    <button class="detail-close" id="detail-close" title="Fechar">✕</button>
  </div>
  <div class="detail-body" id="detail-body"></div>
</div>

<!-- Legend -->
<div id="leg" class="pnl">
  <div class="leg-i"><div class="leg-sq" style="background:#22C55E;box-shadow:0 0 5px rgba(34,197,94,0.6);"></div>Ocupado</div>
  <div class="leg-i"><div class="leg-sq" style="background:#EF4444;opacity:0.55;"></div>Livre</div>
  <div class="leg-i"><div class="leg-sq" style="background:#F59E0B;"></div>Bloqueado</div>
  <div class="leg-i"><div class="leg-sq" style="background:#3B82F6;box-shadow:0 0 6px rgba(59,130,246,0.6);"></div>Hover</div>
  <div class="leg-i"><div class="leg-sq" style="background:#FACC15;box-shadow:0 0 8px rgba(250,204,21,0.8);"></div>U.A buscada</div>
  <div class="leg-i"><div class="leg-tunnel">⇔</div>Túnel</div>
</div>

<!-- Camera controls -->
<div id="camctrl" class="pnl">
  <div class="pnl-head"><span class="pnl-dot"></span>CÂMERA</div>
  <div class="camctrl-body">
    <div class="cam-btn-row">
      <div class="cam-btn active" id="btn-iso" onclick="setCamView('iso')">ISO</div>
      <div class="cam-btn" id="btn-top" onclick="setCamView('top')">TOP</div>
      <div class="cam-btn" id="btn-front" onclick="setCamView('front')">FRONT</div>
    </div>
    <div class="cam-btn-row">
      <div class="cam-btn" id="btn-reset" onclick="setCamView('reset')" style="flex:1;">⟳ RESET</div>
    </div>
  </div>
</div>

<!-- Activity ticker -->
<div id="ticker" class="pnl">
  <div class="pnl-head"><span class="pnl-dot"></span>ATIVIDADE EM TEMPO REAL</div>
  <div class="tick-body" id="tick-body"></div>
</div>

<!-- Tooltip hover -->
<div id="tip">
  <div class="tip-head">
    <div class="tip-addr" id="ta"></div>
    <div class="tip-st" id="ts"></div>
    <div id="tip-tunnel" style="display:none;"><span class="tip-tunnel">⇔ TÚNEL EMPILHADEIRA</span></div>
  </div>
  <div class="tip-body">
    <div class="tip-r"><span class="tip-k">Rua</span><span class="tip-v" id="tr"></span></div>
    <div class="tip-r"><span class="tip-k">Nível</span><span class="tip-v" id="tn"></span></div>
    <div class="tip-r"><span class="tip-k">Posição</span><span class="tip-v" id="tp2"></span></div>
    <div class="tip-r" id="tu-row" style="display:none;"><span class="tip-k">U.A</span><span class="tip-v tip-ua" id="tu"></span></div>
  </div>
</div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const CUBOS      = {cubos_json};
const RUAS       = {ruas_json};
const MINIMAP    = {minimap_json};
const AUTO_FOCUS = {'true' if auto_focus_rua else 'false'};

/* ── MINIMAP ── */
(function(){{
  const b = document.getElementById('mm-body');
  MINIMAP.forEach(d => {{
    const c = d.pct < 60 ? '#22C55E' : d.pct < 85 ? '#F59E0B' : '#EF4444';
    const r = document.createElement('div');
    r.className = 'mm-row';
    r.innerHTML = `<span class="mm-lbl">${{d.rua}}</span>
      <div class="mm-rail"><div class="mm-bar" style="width:${{d.pct}}%;background:${{c}};"></div></div>
      <span class="mm-pct" style="color:${{c}}">${{d.pct}}%</span>`;
    b.appendChild(r);
  }});
}})();

/* ── TICKER ── */
const TICK_MSGS = [
  {{c:'#22C55E', m:'Palete recebido — zona A'}},
  {{c:'#F59E0B', m:'Endereço bloqueado — manutenção'}},
  {{c:'#3B82F6', m:'Empilhadeira #03 em movimento'}},
  {{c:'#22C55E', m:'Reabastecimento concluído'}},
  {{c:'#F59E0B', m:'Contagem de inventário ativa'}},
  {{c:'#22C55E', m:'Carga liberada — doca 2'}},
  {{c:'#EF4444', m:'Endereço livre — aguardando palete'}},
  {{c:'#3B82F6', m:'Transferência entre ruas iniciada'}},
  {{c:'#22C55E', m:'Picking confirmado — pedido 4482'}},
  {{c:'#F59E0B', m:'Empilhadeira #07 retornando'}},
];
let tickIdx = 0;
function addTick() {{
  const tb = document.getElementById('tick-body');
  const ev = TICK_MSGS[tickIdx++ % TICK_MSGS.length];
  const rows = tb.querySelectorAll('.tick-row');
  if (rows.length >= 4) rows[0].remove();
  const r = document.createElement('div'); r.className = 'tick-row';
  const now = new Date();
  const ts = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map(n => String(n).padStart(2,'0')).join(':');
  r.innerHTML = `<span class="tick-dot" style="background:${{ev.c}};box-shadow:0 0 4px ${{ev.c}};"></span>
    <span style="color:rgba(148,163,184,0.35);min-width:50px">${{ts}}</span>
    <span style="color:rgba(200,210,230,0.75)">${{ev.m}}</span>`;
  tb.appendChild(r);
}}
addTick(); setInterval(addTick, 4200);

/* ── SCENE ── */
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0F172A);
scene.fog = new THREE.FogExp2(0x0F172A, 0.0048);

const W = window.innerWidth, H = window.innerHeight;
const camera = new THREE.PerspectiveCamera(48, W/H, 0.1, 2000);
const renderer = new THREE.WebGLRenderer({{ antialias: true, powerPreference: 'high-performance' }});
renderer.setSize(W, H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.10;
document.getElementById('cc').appendChild(renderer.domElement);

/* ── LIGHTS ── */
scene.add(new THREE.AmbientLight(0x1E293B, 1.0));
const sunL = new THREE.DirectionalLight(0xC8D8FF, 0.55);
sunL.position.set(80, 130, 60); sunL.castShadow = true;
sunL.shadow.mapSize.set(2048, 2048);
sunL.shadow.camera.near = 1; sunL.shadow.camera.far = 600;
sunL.shadow.camera.left = -160; sunL.shadow.camera.right = 160;
sunL.shadow.camera.top = 160; sunL.shadow.camera.bottom = -160;
sunL.shadow.bias = -0.001;
scene.add(sunL);
const fillL = new THREE.DirectionalLight(0x3B5580, 0.22);
fillL.position.set(-60, 80, -40); scene.add(fillL);

const spots = [];
for (let i = 0; i < 6; i++) {{
  const sp = new THREE.SpotLight(0xA0C0FF, 0.70, 130, Math.PI/7, 0.5, 1.8);
  sp.castShadow = true; sp.shadow.mapSize.set(512, 512); sp.shadow.bias = -0.002;
  scene.add(sp); scene.add(sp.target); spots.push(sp);
}}
const neonBlue = new THREE.PointLight(0x3B82F6, 0.30, 160);
neonBlue.position.set(20, 28, 10); scene.add(neonBlue);
const neonPurple = new THREE.PointLight(0x8B5CF6, 0.18, 100);
neonPurple.position.set(-12, 18, 8); scene.add(neonPurple);

/* ── FLOOR ── */
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(1200, 1200),
  new THREE.MeshStandardMaterial({{ color: 0x0A1120, roughness: 0.90, metalness: 0.15 }})
);
floor.rotation.x = -Math.PI/2; floor.position.y = -0.5; floor.receiveShadow = true;
scene.add(floor);
const gridBig = new THREE.GridHelper(900, 80, 0x1E293B, 0x162032); gridBig.position.y = -0.49; scene.add(gridBig);
const gridFine = new THREE.GridHelper(900, 360, 0x131F35, 0x131F35); gridFine.position.y = -0.48; scene.add(gridFine);

function makeStripe(x1, z1, x2, z2, w) {{
  const dx = x2-x1, dz = z2-z1, len = Math.sqrt(dx*dx+dz*dz);
  const ang = Math.atan2(dx, dz);
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(w, len),
    new THREE.MeshStandardMaterial({{ color: 0x2563EB, roughness: 1, metalness: 0, transparent: true, opacity: 0.35 }})
  );
  m.rotation.x = -Math.PI/2; m.rotation.z = ang;
  m.position.set((x1+x2)/2, -0.47, (z1+z2)/2); scene.add(m);
}}

/* ── RACK MATERIALS ── */
const RACK_MAT = new THREE.MeshStandardMaterial({{ color: 0x1E293B, roughness: 0.80, metalness: 0.60 }});
const BEAM_MAT_GOLD = new THREE.MeshStandardMaterial({{ color: 0x3B82F6, roughness: 0.55, metalness: 0.80, emissive: 0x0A1535, emissiveIntensity: 0.35 }});

function mkCol(x, y, z, h) {{
  const m = new THREE.Mesh(new THREE.BoxGeometry(0.08, h, 0.08), RACK_MAT);
  m.position.set(x, y, z); m.castShadow = true; scene.add(m);
}}
function mkBeamSegmented(segments, y, z, gold) {{
  segments.forEach(([x0, x1]) => {{
    const w = x1-x0; if (w <= 0) return;
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, 0.06, 0.06), gold ? BEAM_MAT_GOLD : RACK_MAT);
    m.position.set(x0+w/2, y, z); m.castShadow = true; scene.add(m);
  }});
}}
function mkBrace(x, y, z, h) {{
  const m = new THREE.Mesh(new THREE.BoxGeometry(0.05, h*0.65, 0.05), RACK_MAT);
  m.position.set(x, y+h*0.12, z); m.rotation.z = Math.PI/6; scene.add(m);
}}

/* ── CUBE MATERIALS ── */
const mkMat = (color, emissive, ei, op=1, tr=false) =>
  new THREE.MeshStandardMaterial({{ color, emissive, emissiveIntensity: ei, roughness: 0.50, metalness: 0.30, opacity: op, transparent: tr }});

const MAT_OCC  = mkMat(0x22C55E, 0x052010, 0.20);
const MAT_BLK  = mkMat(0xF59E0B, 0x2A1A00, 0.22);
const MAT_EMP  = mkMat(0xEF4444, 0x200505, 0.06, 0.35, true);
const MAT_HOV  = mkMat(0x3B82F6, 0x051535, 0.55);
const MAT_HIGH = mkMat(0xFACC15, 0xC09000, 0.95);

const mkEdge = (hex, op) => new THREE.LineBasicMaterial({{ color: hex, transparent: true, opacity: op }});
const EDGE_OCC  = mkEdge(0x4ADE80, 0.30);
const EDGE_BLK  = mkEdge(0xFBBF24, 0.28);
const EDGE_EMP  = mkEdge(0xF87171, 0.16);
const EDGE_HIGH = mkEdge(0xFACC15, 1.00);

const CUBE_SZ = 1.0, GAP = 0.12, STEP = CUBE_SZ + GAP, RUA_GAP = 2.4;
const NIVEL_H = STEP * 0.65;
const cubeGeo = new THREE.BoxGeometry(CUBE_SZ, CUBE_SZ*0.55, CUBE_SZ);
const edgeGeo = new THREE.EdgesGeometry(cubeGeo);
const palletBaseGeo = new THREE.BoxGeometry(CUBE_SZ*0.92, 0.08, CUBE_SZ*0.92);
const palletMat = new THREE.MeshStandardMaterial({{ color: 0x5C3D20, roughness: 0.9, metalness: 0.05 }});

/* ── TUNNEL HITBOXES ── */
const tunnelHoverMeshes = [];
const tunnelHoverMat = new THREE.MeshBasicMaterial({{ transparent: true, opacity: 0, side: THREE.DoubleSide }});

const meshes = [], hlMeshes = [], blkMeshes = [];

/* ── PRE-PROCESS TUNNELS ── */
const tunnelXByRua = {{}};
CUBOS.forEach(c => {{
  if (!c.tunnel) return;
  if (!tunnelXByRua[c.z]) tunnelXByRua[c.z] = new Set();
  tunnelXByRua[c.z].add(c.x);
}});

/* ── BUILD CUBES ── */
CUBOS.forEach((c, idx) => {{
  const ex = c.x * STEP;
  const ey = c.y * NIVEL_H;
  const ez = c.z * (STEP*4 + RUA_GAP);

  if (c.tunnel) {{
    const hitGeo = new THREE.BoxGeometry(CUBE_SZ, CUBE_SZ*0.55, CUBE_SZ);
    const hitM = new THREE.Mesh(hitGeo, tunnelHoverMat.clone());
    hitM.position.set(ex, ey, ez);
    hitM.userData = {{ ...c, isTunnel: true }};
    scene.add(hitM);
    tunnelHoverMeshes.push(hitM);
    return;
  }}

  let bMat;
  if      (c.highlight) bMat = MAT_HIGH.clone();
  else if (c.blocked)   bMat = MAT_BLK.clone();
  else if (c.occupied)  bMat = MAT_OCC.clone();
  else                  bMat = MAT_EMP.clone();
  bMat.transparent = true; bMat.opacity = 0;

  const mesh = new THREE.Mesh(cubeGeo, bMat);
  mesh.position.set(ex, ey, ez);
  mesh.castShadow = c.occupied || c.blocked || c.highlight;
  mesh.receiveShadow = true;
  mesh.userData = {{ ...c,
    baseOpacity: c.highlight ? 1.0 : (c.occupied || c.blocked) ? 1.0 : 0.35,
    fadeDelay: Math.floor(idx/30),
  }};
  scene.add(mesh); meshes.push(mesh);
  if (c.highlight) hlMeshes.push(mesh);
  if (c.blocked)   blkMeshes.push(mesh);

  if (c.occupied || c.highlight) {{
    const pb = new THREE.Mesh(palletBaseGeo, palletMat.clone());
    pb.position.set(ex, ey - CUBE_SZ*0.275 - 0.04, ez);
    pb.receiveShadow = true; pb.castShadow = true;
    pb.material.transparent = true; pb.material.opacity = 0;
    pb.userData = {{ baseOpacity: 0.88, fadeDelay: Math.floor(idx/30) }};
    scene.add(pb); meshes.push(pb);
  }}

  let eMat;
  if      (c.highlight) eMat = EDGE_HIGH.clone();
  else if (c.blocked)   eMat = EDGE_BLK.clone();
  else if (c.occupied)  eMat = EDGE_OCC.clone();
  else                  eMat = EDGE_EMP.clone();
  eMat.transparent = true; eMat.opacity = 0;
  const edges = new THREE.LineSegments(edgeGeo, eMat);
  edges.position.copy(mesh.position);
  edges.userData = {{ baseOpacity: c.highlight ? 1.0 : (c.occupied || c.blocked) ? 0.30 : 0.15, fadeDelay: Math.floor(idx/30) }};
  scene.add(edges);
  mesh.userData.edgeRef = edges;
}});

/* ── RACK STRUCTURE ── */
RUAS.forEach((rua, ri) => {{
  const zBase = ri * (STEP*4 + RUA_GAP);
  const rc2 = CUBOS.filter(c => c.z === ri && !c.tunnel);
  if (!rc2.length) return;
  const maxX = Math.max(...rc2.map(c => c.x));
  const maxN = Math.max(...rc2.map(c => c.y));
  const rackH = (maxN+1) * NIVEL_H + 0.5;

  const tXSet = tunnelXByRua[ri] || new Set();
  const tunnelWorldRanges = [...tXSet].map(gx => [gx*STEP - CUBE_SZ*0.6, gx*STEP + CUBE_SZ*0.6]);

  function subtractHoles(start, end, holes) {{
    let segs = [[start, end]];
    holes.forEach(([h0, h1]) => {{
      const next = [];
      segs.forEach(([s, e]) => {{
        if (h1 <= s || h0 >= e) {{ next.push([s, e]); return; }}
        if (s < h0) next.push([s, h0]);
        if (e > h1) next.push([h1, e]);
      }});
      segs = next;
    }});
    return segs;
  }}

  if (ri > 0) {{
    const zStr = ri * (STEP*4 + RUA_GAP) - RUA_GAP/2;
    makeStripe(-2, zStr - 0.12, maxX*STEP+2, zStr - 0.12, 0.18);
    makeStripe(-2, zStr + 0.12, maxX*STEP+2, zStr + 0.12, 0.18);
  }}

  for (let xi = 0; xi <= maxX+1; xi += 3) {{
    const xc = xi*STEP - CUBE_SZ*0.5;
    const isTunnelCol = tunnelWorldRanges.some(([h0, h1]) => xc >= h0 && xc <= h1);
    if (!isTunnelCol) {{
      mkCol(xc, rackH/2 - 0.5, zBase - CUBE_SZ*0.55, rackH);
      mkCol(xc, rackH/2 - 0.5, zBase + CUBE_SZ*0.55, rackH);
      mkBrace(xc, 0, zBase - CUBE_SZ*0.55, rackH);
    }} else {{
      const tunnelTopY = 3 * NIVEL_H + CUBE_SZ*0.3;
      const aboveH = rackH - tunnelTopY;
      if (aboveH > 0.2) {{
        mkCol(xc, tunnelTopY + aboveH/2, zBase - CUBE_SZ*0.55, aboveH);
        mkCol(xc, tunnelTopY + aboveH/2, zBase + CUBE_SZ*0.55, aboveH);
      }}
    }}
  }}

  const TUNNEL_NIVEIS = new Set([1,2,3]);
  for (let ni = 0; ni <= maxN; ni++) {{
    const yb = ni*NIVEL_H - CUBE_SZ*0.28;
    const bStart = -CUBE_SZ*0.5, bEnd = (maxX+0.5)*STEP;
    const gold = ni === 0 || ni === maxN;
    const holes = TUNNEL_NIVEIS.has(ni) ? tunnelWorldRanges : [];
    const segs = subtractHoles(bStart, bEnd, holes);
    mkBeamSegmented(segs.map(([s,e]) => [s,e]), yb, zBase - CUBE_SZ*0.54, gold);
    mkBeamSegmented(segs.map(([s,e]) => [s,e]), yb, zBase + CUBE_SZ*0.54, gold);
  }}

  const si = ri % spots.length;
  const cx = (maxX/2)*STEP, cy = (maxN/2)*NIVEL_H;
  spots[si].position.set(cx, rackH+14, zBase);
  spots[si].target.position.set(cx, cy, zBase);
  spots[si].target.updateMatrixWorld();
}});

/* ── FORKLIFTS ── */
const forklifts = [];
function mkFork(sx, sz, dirX, spd, col) {{
  const body = new THREE.Group();
  const chassi = new THREE.Mesh(
    new THREE.BoxGeometry(0.55, 0.50, 1.10),
    new THREE.MeshStandardMaterial({{ color: col, roughness: 0.6, metalness: 0.5, emissive: col, emissiveIntensity: 0.08 }})
  );
  chassi.castShadow = true; body.add(chassi);
  const mast = new THREE.Mesh(
    new THREE.BoxGeometry(0.08, 1.6, 0.08),
    new THREE.MeshStandardMaterial({{ color: 0x334155, roughness: 0.7, metalness: 0.6 }})
  );
  mast.position.set(0.2, 1.05, 0.45); mast.castShadow = true; body.add(mast);
  const fork = new THREE.Mesh(
    new THREE.BoxGeometry(0.48, 0.06, 0.55),
    new THREE.MeshStandardMaterial({{ color: 0x3B82F6, roughness: 0.5, metalness: 0.8, emissive: 0x051535, emissiveIntensity: 0.4 }})
  );
  fork.position.set(0.2, 0.25, 0.72); fork.castShadow = true; body.add(fork);
  const fLight = new THREE.PointLight(0x60A5FA, 0.55, 5);
  fLight.position.set(0.2, 0.45, 0.75); body.add(fLight);
  body.position.set(sx, -0.22, sz); body.scale.setScalar(0.75);
  scene.add(body);
  forklifts.push({{ mesh: body, x: sx, z: sz, dirX, spd, t: Math.random()*100, fLight, maxX: 60 }});
}}
RUAS.forEach((rua, ri) => {{
  if (ri === 0) return;
  const zCorr = ri*(STEP*4+RUA_GAP) - RUA_GAP/2;
  const rc2 = CUBOS.filter(c => c.z === ri && !c.tunnel);
  if (!rc2.length) return;
  const maxX = Math.max(...rc2.map(c => c.x));
  const cols = [0x1D4ED8, 0x0369A1, 0x334155];
  mkFork(-2, zCorr, 1, 0.008+Math.random()*0.006, cols[ri%3]);
  if (maxX > 8) mkFork(maxX*STEP+4, zCorr, -1, 0.006+Math.random()*0.005, cols[(ri+1)%3]);
}});

/* ── DUST PARTICLES ── */
const dustCount = 200;
const dustPos = new Float32Array(dustCount*3);
const dustVel = [];
for (let i = 0; i < dustCount; i++) {{
  dustPos[i*3] = Math.random()*80 - 10;
  dustPos[i*3+1] = Math.random()*12;
  dustPos[i*3+2] = Math.random()*60 - 5;
  dustVel.push({{ vx: (Math.random()-0.5)*0.004, vy: Math.random()*0.005-0.001, vz: (Math.random()-0.5)*0.003 }});
}}
const dustGeo = new THREE.BufferGeometry();
dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({{
  color: 0x64748B, size: 0.055, transparent: true, opacity: 0.28, sizeAttenuation: true
}}));
scene.add(dust);

/* ── LABELS ── */
function makeLabel(text, x, y, z, color, scale) {{
  const cvs = document.createElement('canvas');
  cvs.width = 380; cvs.height = 76;
  const ctx = cvs.getContext('2d');
  ctx.font = 'bold 28px "JetBrains Mono",monospace';
  ctx.fillStyle = color; ctx.textAlign = 'center';
  ctx.fillText(text, 190, 50);
  const tex = new THREE.CanvasTexture(cvs);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({{ map: tex, transparent: true, depthTest: false }}));
  sp.position.set(x, y, z); sp.scale.set(scale, scale*0.20, 1); scene.add(sp);
}}
RUAS.forEach((rua, i) => {{
  const z = i*(STEP*4+RUA_GAP);
  const rc2 = CUBOS.filter(c => c.z === i && !c.tunnel);
  const maxX = rc2.length ? Math.max(...rc2.map(c => c.x)) : 0;
  const maxN = rc2.length ? Math.max(...rc2.map(c => c.y)) : 0;
  const rackH = (maxN+1)*NIVEL_H+1.5;
  makeLabel('RUA '+rua, (maxX/2)*STEP, rackH, z, 'rgba(96,165,250,0.85)', 8);
}});
const niveisUniq = [...new Set(CUBOS.filter(c => !c.tunnel).map(c => c.y))].sort((a,b) => a-b);
niveisUniq.forEach(n => makeLabel('N'+n, -5.5, n*NIVEL_H, -2, 'rgba(148,163,184,0.45)', 4));

/* ── CAMERA STATE ── */
let sph = {{ theta: Math.PI/4.2, phi: Math.PI/3.0, radius: 90 }};
let tgt = new THREE.Vector3(25, 5, 14);
const UP = new THREE.Vector3(0, 1, 0);
let currentView = 'iso';

function updCam() {{
  camera.position.set(
    tgt.x + sph.radius * Math.sin(sph.phi) * Math.sin(sph.theta),
    tgt.y + sph.radius * Math.cos(sph.phi),
    tgt.z + sph.radius * Math.sin(sph.phi) * Math.cos(sph.theta)
  ); camera.lookAt(tgt);
}}

/* ── COMPUTE CENTER ── */
const nTunnel = CUBOS.filter(c => !c.tunnel);
let centerX = 25, centerY = 5, centerZ = 14;
if (nTunnel.length) {{
  const xs = nTunnel.map(c => c.x*STEP);
  const ys = nTunnel.map(c => c.y*NIVEL_H);
  const zs = nTunnel.map(c => c.z*(STEP*4+RUA_GAP));
  centerX = (Math.min(...xs)+Math.max(...xs))/2;
  centerY = (Math.min(...ys)+Math.max(...ys))/2;
  centerZ = (Math.min(...zs)+Math.max(...zs))/2;
}}

if (AUTO_FOCUS) {{
  tgt.set(centerX, centerY, centerZ);
  sph.radius = 30;
}} else if (hlMeshes.length > 0) {{
  const p = hlMeshes[0].position;
  tgt.set(p.x, p.y, p.z); sph.radius = 30;
}}
updCam();

/* ── CAMERA VIEW PRESETS ── */
window.setCamView = function(view) {{
  document.querySelectorAll('.cam-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('btn-'+view);
  if (btn) btn.classList.add('active');
  currentView = view;
  tgt.set(centerX, centerY, centerZ);
  if (view === 'iso') {{
    sph = {{ theta: Math.PI/4.2, phi: Math.PI/3.0, radius: 90 }};
  }} else if (view === 'top') {{
    sph = {{ theta: Math.PI/4.2, phi: 0.05, radius: 80 }};
  }} else if (view === 'front') {{
    sph = {{ theta: 0, phi: Math.PI/2.4, radius: 90 }};
  }} else if (view === 'reset') {{
    sph = {{ theta: Math.PI/4.2, phi: Math.PI/3.0, radius: 90 }};
    tgt.set(25, 5, 14);
    document.getElementById('btn-iso').classList.add('active');
  }}
  updCam();
}};

/* ── RAYCASTER ── */
const rc = new THREE.Raycaster();
const ms = new THREE.Vector2();
const tip = document.getElementById('tip');
const detail = document.getElementById('detail');
let selM = null, selMat2 = null, hQ = false, lastE = null;
const hittable = [...meshes.filter(m => m.userData.label), ...tunnelHoverMeshes];

function openDetail(ud) {{
  const db = document.getElementById('detail-body');
  const stTxt = ud.isTunnel || ud.tunnel ? 'TÚNEL EMPILHADEIRA'
    : (ud.status || (ud.occupied ? 'OCUPADO' : ud.blocked ? 'BLOQUEADO' : 'LIVRE'));
  const stCol = ud.isTunnel || ud.tunnel ? '#22C55E'
    : ud.occupied ? '#22C55E' : ud.blocked ? '#F59E0B' : '#EF4444';

  let extraBadge = '';
  if (ud.highlight) extraBadge = `<div class="detail-highlight-badge">⭐ U.A BUSCADA</div>`;
  if (ud.isTunnel || ud.tunnel) extraBadge = `<div class="detail-highlight-badge" style="background:rgba(34,197,94,0.10);border-color:rgba(34,197,94,0.30);color:#4ADE80;">⇔ TÚNEL EMPILHADEIRA</div>`;

  const uaRow = (ud.ua && !ud.tunnel && !ud.isTunnel)
    ? `<div class="detail-row"><span class="detail-k">U.A</span><div class="detail-ua-badge">${{ud.ua}}</div></div>` : '';

  db.innerHTML = `
    <div class="detail-title">${{ud.label}}</div>
    <div class="detail-status" style="color:${{stCol}}">${{stTxt}}</div>
    ${{extraBadge}}
    <div style="margin-top:12px;">
      <div class="detail-row"><span class="detail-k">Rua</span><span class="detail-v">${{ud.rua || '—'}}</span></div>
      <div class="detail-row"><span class="detail-k">Nível</span><span class="detail-v">${{ud.nivel != null ? ud.nivel : '—'}}</span></div>
      <div class="detail-row"><span class="detail-k">Posição</span><span class="detail-v">${{ud.posicao != null ? ud.posicao : '—'}}</span></div>
      ${{uaRow}}
      <div class="detail-row"><span class="detail-k">Status</span><span class="detail-v" style="color:${{stCol}}">${{stTxt}}</span></div>
    </div>
  `;
  detail.style.display = 'block';
}}
document.getElementById('detail-close').addEventListener('click', () => {{
  detail.style.display = 'none';
}});

function doHover() {{
  hQ = false; if (!lastE) return;
  const e = lastE;
  const rect = renderer.domElement.getBoundingClientRect();
  ms.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  ms.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  rc.setFromCamera(ms, camera);
  const hits = rc.intersectObjects(hittable);
  if (hits.length > 0) {{
    const hit = hits[0].object;
    renderer.domElement.classList.add('can-hover');
    if (!hit.userData.isTunnel) {{
      if (selM !== hit) {{
        if (selM && selMat2) selM.material = selMat2;
        selM = hit; selMat2 = hit.material; hit.material = MAT_HOV.clone();
      }}
    }} else {{
      if (selM && selMat2) {{ selM.material = selMat2; selM = null; selMat2 = null; }}
    }}
    const ud = hit.userData;
    document.getElementById('ta').textContent = ud.label;
    let stTxt, stCol;
    if (ud.isTunnel || ud.tunnel) {{
      stTxt = 'TÚNEL EMPILHADEIRA'; stCol = '#22C55E';
    }} else {{
      stTxt = ud.status || (ud.occupied ? 'OCUPADO' : ud.blocked ? 'BLOQUEADO' : 'LIVRE');
      stCol = ud.occupied ? '#22C55E' : ud.blocked ? '#F59E0B' : '#EF4444';
    }}
    const ts3 = document.getElementById('ts'); ts3.textContent = stTxt; ts3.style.color = stCol;
    document.getElementById('tr').textContent = ud.rua || '—';
    document.getElementById('tn').textContent = ud.nivel != null ? ud.nivel : '—';
    document.getElementById('tp2').textContent = ud.posicao != null ? ud.posicao : '—';
    const uRow = document.getElementById('tu-row');
    if (ud.ua && !ud.tunnel && !ud.isTunnel) {{
      document.getElementById('tu').textContent = ud.ua; uRow.style.display = 'flex';
    }} else uRow.style.display = 'none';
    document.getElementById('tip-tunnel').style.display = (ud.tunnel || ud.isTunnel) ? 'block' : 'none';
    tip.style.display = 'block';
    tip.style.left = (e.clientX - rect.left + 18) + 'px';
    tip.style.top  = (e.clientY - rect.top  - 14) + 'px';
  }} else {{
    renderer.domElement.classList.remove('can-hover');
    if (selM && selMat2) {{ selM.material = selMat2; selM = null; selMat2 = null; }}
    tip.style.display = 'none';
  }}
}}
renderer.domElement.addEventListener('mousemove', e => {{
  if (isDrag || isPan) return; lastE = e;
  if (!hQ) {{ hQ = true; requestAnimationFrame(doHover); }}
}});

/* Click → open detail panel */
renderer.domElement.addEventListener('click', e => {{
  if (dragMoved) return;
  const rect = renderer.domElement.getBoundingClientRect();
  ms.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  ms.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  rc.setFromCamera(ms, camera);
  const hits = rc.intersectObjects(hittable);
  if (hits.length > 0) {{
    openDetail(hits[0].object.userData);
  }}
}});

/* ── CAMERA CONTROLS ── */
let isDrag = false, isPan = false, prevM = {{ x: 0, y: 0 }}, dragMoved = false;
function panDirs() {{
  const fwd = new THREE.Vector3().copy(tgt).sub(camera.position).normalize();
  const rt = new THREE.Vector3().crossVectors(fwd, UP).normalize();
  const up2 = new THREE.Vector3().crossVectors(rt, fwd).normalize();
  return {{ rt, up2 }};
}}
renderer.domElement.addEventListener('contextmenu', e => e.preventDefault());
renderer.domElement.addEventListener('mousedown', e => {{
  dragMoved = false;
  if (e.button === 2 || (e.button === 0 && e.shiftKey)) {{ isPan = true; isDrag = false; }}
  else if (e.button === 0) {{ isDrag = true; isPan = false; }}
  prevM = {{ x: e.clientX, y: e.clientY }};
}});
renderer.domElement.addEventListener('mouseup', () => {{ isDrag = false; isPan = false; }});
renderer.domElement.addEventListener('mouseleave', () => {{ isDrag = false; isPan = false; tip.style.display = 'none'; }});
renderer.domElement.addEventListener('mousemove', e => {{
  if (!isDrag && !isPan) return;
  const dx = e.clientX - prevM.x, dy = e.clientY - prevM.y;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragMoved = true;
  if (isPan) {{
    const {{ rt, up2 }} = panDirs(); const s = sph.radius * 0.0010;
    tgt.sub(rt.multiplyScalar(dx*s)); tgt.add(up2.multiplyScalar(dy*s));
  }} else {{
    sph.theta -= dx * 0.007;
    sph.phi = Math.max(0.10, Math.min(Math.PI/2.02, sph.phi + dy*0.005));
  }}
  prevM = {{ x: e.clientX, y: e.clientY }}; updCam();
}});
renderer.domElement.addEventListener('wheel', e => {{
  sph.radius = Math.max(8, Math.min(280, sph.radius + e.deltaY*0.08));
  updCam(); e.preventDefault();
}}, {{ passive: false }});
renderer.domElement.addEventListener('dblclick', () => setCamView('reset'));
window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

/* ── ANIMATION LOOP ── */
let frame = 0;
function animate() {{
  requestAnimationFrame(animate);
  frame++; const t = Date.now() * 0.001;

  spots.forEach((sp, i) => {{ sp.intensity = 0.55 + Math.sin(t*0.5+i)*0.20; }});
  neonBlue.position.x   = 22 + Math.sin(t*0.30)*20; neonBlue.position.z   = 10 + Math.cos(t*0.24)*16;
  neonPurple.position.x =  5 + Math.cos(t*0.26)*14; neonPurple.position.z = 18 + Math.sin(t*0.20)*10;

  forklifts.forEach(fk => {{
    fk.t += fk.spd;
    fk.mesh.position.x = fk.x + Math.sin(fk.t*fk.dirX)*fk.maxX/2 + fk.maxX/2;
    fk.mesh.position.y = -0.22 + Math.abs(Math.sin(fk.t*3))*0.015;
    const vx = Math.cos(fk.t*fk.dirX)*fk.dirX;
    fk.mesh.rotation.y = vx > 0 ? Math.PI : 0;
    fk.fLight.intensity = 0.45 + Math.sin(fk.t*8)*0.12;
  }});

  const dPos = dust.geometry.attributes.position.array;
  for (let i = 0; i < dustCount; i++) {{
    dPos[i*3]   += dustVel[i].vx; dPos[i*3+1] += dustVel[i].vy; dPos[i*3+2] += dustVel[i].vz;
    if (dPos[i*3+1] > 14) dPos[i*3+1] = 0;
    if (dPos[i*3] > 85 || dPos[i*3] < -10) dustVel[i].vx *= -1;
    if (dPos[i*3+2] > 65 || dPos[i*3+2] < -8) dustVel[i].vz *= -1;
  }}
  dust.geometry.attributes.position.needsUpdate = true;

  /* Fade-in on load */
  const FADE = 60;
  if (frame <= FADE + Math.ceil(meshes.length/30)) {{
    meshes.forEach(m => {{
      const d = m.userData.fadeDelay || 0;
      const p = Math.min(1, Math.max(0, (frame - d*1.8) / FADE));
      if (p > 0) {{
        m.material.opacity = p * m.userData.baseOpacity;
        const er = m.userData.edgeRef;
        if (er) er.material.opacity = p * er.userData.baseOpacity;
      }}
    }});
  }}

  /* Highlight pulse */
  const ph = 0.55 + Math.abs(Math.sin(t*2.0))*0.80;
  hlMeshes.forEach(m => {{
    if (m.material.emissive) {{ m.material.emissiveIntensity = ph; m.scale.setScalar(1+(ph-0.55)*0.10); }}
  }});
  const pb = 0.18 + Math.abs(Math.sin(t*0.75))*0.18;
  blkMeshes.forEach(m => {{ if (m.material.emissive) m.material.emissiveIntensity = pb; }});

  renderer.render(scene, camera);
}}
animate();
</script>
</body>
</html>"""

    components.html(html_3d, height=760, scrolling=False)