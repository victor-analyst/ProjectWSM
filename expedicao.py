import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from db import get_engine


@st.cache_data(ttl=60, show_spinner=False)
def _load_expedicao():
    query = """
    SELECT
        FILIAL,
        CODOSA,
        DATA_ATUALIZACAO,
        QUANTIDADE_TOTAL,
        QUANTIDADE_SEPARADA,
        QUANTIDADE_FALTANTE,
        USUARIO_SEPARACAO_2,
        RAZAO_SOCIAL,
        TRANSPORTADOR,
        STATUS
    FROM db_visual_SALOG.dbo.VW_PAINEL_STATUS_PEDIDOS_WMS_EM_SEPARACAO
    """
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)


def show():
    df = _load_expedicao()

    # =========================
    # TRATAMENTO
    # =========================
    df["DATA_ATUALIZACAO"] = pd.to_datetime(df["DATA_ATUALIZACAO"])
    df["Operador"] = (
        df["USUARIO_SEPARACAO_2"]
        .fillna("Sem Operador")
        .str.split(".")
        .str[0]
        .str.title()
    )

    # =========================
    # HEADER + PÍLULA DE REGISTROS
    # =========================
    total_registros = len(df)
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap; margin-bottom:4px;">
        <h1 style="margin:0;">PAINEL DE EXPEDIÇÃO - SALOG</h1>
        <div style="
            display:inline-flex; align-items:center; gap:7px;
            background:rgba(0,194,45,0.08);
            border:1px solid rgba(0,194,45,0.25);
            border-radius:20px; padding:5px 14px;
            font-family:Inter,sans-serif;
            font-size:0.70rem; font-weight:600;
            color:#00C22D; letter-spacing:0.06em;
            white-space:nowrap;
        ">
            <span style="width:6px;height:6px;border-radius:50%;background:#00C22D;display:inline-block;box-shadow:0 0 6px #00C22D;"></span>
            {total_registros:,} registros carregados
        </div>
    </div>
    <p style='color:#FFFFFF;margin-top:4px;margin-bottom:0;'>Monitoramento de Expedições</p>
    """, unsafe_allow_html=True)

    # =========================
    # SEPARADOR ANIMADO
    # =========================
    def separador(label=""):
        st.markdown(f"""
        <style>
        @keyframes expandLine {{
            from {{ width: 0; opacity: 0; }}
            to   {{ width: 100%; opacity: 1; }}
        }}
        .sep-wrap {{
            display: flex; align-items: center; gap: 14px;
            margin: 28px 0 20px 0;
        }}
        .sep-label {{
            font-family: Inter, sans-serif;
            font-size: 0.60rem; font-weight: 700;
            letter-spacing: 0.18em; text-transform: uppercase;
            color: rgba(0,194,45,0.5); white-space: nowrap;
        }}
        .sep-line {{
            flex: 1; height: 1px;
            background: linear-gradient(90deg, rgba(0,194,45,0.4), rgba(0,194,45,0.05), transparent);
            animation: expandLine 0.8s ease both;
        }}
        .sep-dot {{
            width: 4px; height: 4px; border-radius: 50%;
            background: rgba(0,194,45,0.4); flex-shrink: 0;
        }}
        </style>
        <div class="sep-wrap">
            <span class="sep-dot"></span>
            {'<span class="sep-label">' + label + '</span>' if label else ''}
            <div class="sep-line"></div>
        </div>
        """, unsafe_allow_html=True)

    # =========================
    # FILTROS
    # =========================
    f1, f2, f3, f4, f5 = st.columns([0.6, 0.6, 1.0, 1.0, 1.0])

    with f1:
        data_inicio = st.date_input(
            "Data Inicial",
            df["DATA_ATUALIZACAO"].min(),
            format="DD/MM/YYYY"
        )
    with f2:
        data_fim = st.date_input(
            "Data Final",
            df["DATA_ATUALIZACAO"].max(),
            format="DD/MM/YYYY"
        )
    with f3:
        filiais = st.multiselect(
            "Filial",
            sorted(df["FILIAL"].dropna().unique())
        )
    with f4:
        clientes = st.multiselect(
            "Cliente",
            sorted(df["RAZAO_SOCIAL"].dropna().unique())
        )
    with f5:
        transportadoras = st.multiselect(
            "Transportadora",
            sorted(df["TRANSPORTADOR"].dropna().unique())
        )

    # =========================
    # APLICAR FILTROS
    # =========================
    df = df[
        (df["DATA_ATUALIZACAO"] >= pd.to_datetime(data_inicio))
        & (df["DATA_ATUALIZACAO"] <= pd.to_datetime(data_fim))
    ]
    if filiais:
        df = df[df["FILIAL"].isin(filiais)]
    if clientes:
        df = df[df["RAZAO_SOCIAL"].isin(clientes)]
    if transportadoras:
        df = df[df["TRANSPORTADOR"].isin(transportadoras)]

    # =========================
    # KPIs com barra de progresso + badge
    # =========================
    total_pedidos = df["CODOSA"].nunique()
    finalizados   = df[df["STATUS"] == "FINALIZADO"]["CODOSA"].nunique()
    ag_separacao  = df[df["STATUS"] == "AGUARDANDO SEPARACAO"]["CODOSA"].nunique()
    em_separacao  = df[df["STATUS"] == "EM SEPARACAO"]["CODOSA"].nunique()

    pct_fin = int((finalizados  / total_pedidos * 100) if total_pedidos else 0)
    pct_ag  = int((ag_separacao / total_pedidos * 100) if total_pedidos else 0)
    pct_em  = int((em_separacao / total_pedidos * 100) if total_pedidos else 0)

    def badge(valor, inverso=False):
        if inverso:
            if valor == 0:  return "#00C22D", "rgba(0,194,45,0.12)",   "rgba(0,194,45,0.3)"
            if valor <= 5:  return "#F59E0B", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)"
            return              "#EF4444", "rgba(239,68,68,0.12)",   "rgba(239,68,68,0.3)"
        else:
            if valor >= 80: return "#00C22D", "rgba(0,194,45,0.12)",   "rgba(0,194,45,0.3)"
            if valor >= 40: return "#F59E0B", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)"
            return              "#EF4444", "rgba(239,68,68,0.12)",   "rgba(239,68,68,0.3)"

    def kpi_card(label, valor, pct, bar_color, badge_color, badge_bg, badge_border, suffix="%"):
        return f"""
        <style>
        @keyframes fillBar {{
            from {{ width: 0; }}
            to   {{ width: {pct}%; }}
        }}
        </style>
        <div style="
            background:linear-gradient(135deg,#0D1825 0%,#0A1420 100%);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:16px; padding:18px 20px 14px 20px;
            position:relative; overflow:hidden;
            transition: border-color 0.2s;
        ">
            <div style="
                position:absolute; top:0; left:0; right:0; height:2px;
                background:linear-gradient(90deg,transparent,{bar_color},transparent);
                opacity:0.6;
            "></div>
            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px;">
                <span style="
                    font-family:Inter,sans-serif; font-size:0.62rem;
                    font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#C8D6E5;
                ">{label}</span>
                <span style="
                    background:{badge_bg}; color:{badge_color};
                    border:1px solid {badge_border};
                    border-radius:20px; padding:2px 8px;
                    font-size:0.58rem; font-weight:700;
                    letter-spacing:0.06em; white-space:nowrap;
                ">{pct}{suffix}</span>
            </div>
            <div style="
                font-family:Inter,sans-serif; font-size:1.9rem;
                font-weight:800; color:#FFFFFF;
                letter-spacing:-0.02em; line-height:1;
                margin-bottom:12px;
            ">{valor:,}</div>
            <div style="
                height:3px; border-radius:2px;
                background:rgba(255,255,255,0.05); overflow:hidden;
            ">
                <div style="
                    height:100%; border-radius:2px;
                    background:{bar_color};
                    width:{pct}%;
                    animation: fillBar 1s ease both;
                "></div>
            </div>
        </div>
        """

    c_fin_color, c_fin_bg, c_fin_border = badge(pct_fin)
    c_ag_color,  c_ag_bg,  c_ag_border  = badge(ag_separacao, inverso=True)
    c_em_color,  c_em_bg,  c_em_border  = badge(em_separacao, inverso=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("Total de Pedidos", total_pedidos, 100, "#22D3EE",
                             "#22D3EE", "rgba(34,211,238,0.12)", "rgba(34,211,238,0.3)"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Finalizados", finalizados, pct_fin, c_fin_color,
                             c_fin_color, c_fin_bg, c_fin_border), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("AG. Separação", ag_separacao, pct_ag, c_ag_color,
                             c_ag_color, c_ag_bg, c_ag_border), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Em Separação", em_separacao, pct_em, c_em_color,
                             c_em_color, c_em_bg, c_em_border), unsafe_allow_html=True)

    # =========================
    # PALETA
    # =========================
    PLOT_BG    = "#0A1420"
    PAPER_BG   = "#0D1825"
    GRID_COLOR = "rgba(255,255,255,0.04)"
    TEXT_COLOR = "#6B7A8F"
    GREEN      = "#00C22D"
    COLORS     = ["#00C22D", "#22D3EE", "#F59E0B", "#EF4444", "#8B5CF6"]

    def base_layout(height=420):
        return dict(
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PLOT_BG,
            height=height,
            margin=dict(l=16, r=16, t=36, b=16),
            font=dict(family="Inter", color=TEXT_COLOR, size=11),
            xaxis=dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=10)),
            yaxis=dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=10)),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10))
        )

    # =========================
    # VISÃO GERAL — STATUS + SEPARADO x FALTANTE
    # =========================
    separador("Visão Geral")
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Status dos Pedidos")
        status_df = df.groupby("STATUS")["CODOSA"].count().reset_index()
        fig1 = go.Figure(go.Pie(
            labels=status_df["STATUS"], values=status_df["CODOSA"],
            hole=0.42,
            marker=dict(colors=COLORS, line=dict(color=PLOT_BG, width=3)),
            textinfo="percent+label",
            textfont=dict(size=11, color="#C8D6E5")
        ))
        layout_fig1 = base_layout(height=410)
        layout_fig1["showlegend"] = True
        layout_fig1["legend"] = dict(
            orientation="h", y=-0.15, x=0.5, xanchor="center",
            bgcolor='rgba(0,0,0,0)', font=dict(size=10, color=TEXT_COLOR)
        )
        layout_fig1["annotations"] = [dict(
            text=f"<b>{total_pedidos}</b><br>Pedidos",
            x=0.5, y=0.5,
            font=dict(size=24, color="#FFFFFF", family="Inter"),
            showarrow=False
        )]
        fig1.update_layout(**layout_fig1)
        st.plotly_chart(fig1, width='stretch')

    with c2:
        st.subheader("Separado x Faltante")
        qtd_df = df[["QUANTIDADE_SEPARADA", "QUANTIDADE_FALTANTE"]].sum().reset_index()
        qtd_df.columns = ["Tipo", "Quantidade"]
        qtd_df["Tipo"] = qtd_df["Tipo"].replace({
            "QUANTIDADE_SEPARADA": "Separado",
            "QUANTIDADE_FALTANTE": "Faltante"
        })
        fig2 = go.Figure(go.Pie(
            labels=qtd_df["Tipo"], values=qtd_df["Quantidade"],
            hole=0.68,
            marker=dict(colors=[GREEN, "#1A3A2A"], line=dict(color=PLOT_BG, width=3)),
            textinfo="percent",
            textfont=dict(size=11, color="#C8D6E5")
        ))
        layout_fig2 = base_layout(height=410)
        layout_fig2["showlegend"] = True
        layout_fig2["legend"] = dict(
            orientation="v", x=0.5, xanchor="center", y=-0.15, yanchor="top",
            bgcolor='rgba(0,0,0,0)', font=dict(size=10, color=TEXT_COLOR)
        )
        layout_fig2["annotations"] = [dict(
            text=f"<b>{int(qtd_df['Quantidade'].sum()):,}</b>",
            x=0.5, y=0.5,
            font=dict(size=18, color="#FFFFFF", family="Inter"),
            showarrow=False
        )]
        fig2.update_layout(**layout_fig2)
        st.plotly_chart(fig2, width='stretch')

    # =========================
    # PERFORMANCE — RANKING OPERADORES + EVOLUÇÃO DIÁRIA
    # =========================
    separador("Performance")
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Ranking de Operadores")
        op_rank = (
            df[df["STATUS"] == "FINALIZADO"]
            .groupby("Operador")["CODOSA"].count().reset_index()
            .rename(columns={"CODOSA": "Pedidos"})
            .sort_values("Pedidos", ascending=True).tail(10)
        )
        fig3 = px.bar(
            op_rank, x="Pedidos", y="Operador", orientation="h",
            color="Pedidos", color_continuous_scale=[[0, "#0D3320"], [1, GREEN]], text="Pedidos"
        )
        fig3.update_traces(textposition="outside", textfont_color="#C8D6E5", marker_line_width=0)
        fig3.update_layout(
            **base_layout(height=450),
            coloraxis_showscale=False, bargap=0.3,
            xaxis_title="Pedidos", yaxis_title=""
        )
        st.plotly_chart(fig3, width='stretch')

    with c4:
        st.subheader("Evolução por Dia")
        dia_df = (
            df.groupby("DATA_ATUALIZACAO")["CODOSA"].count().reset_index()
            .rename(columns={"CODOSA": "Pedidos"}).sort_values("DATA_ATUALIZACAO")
        )
        dia_df["Media_Movel"] = dia_df["Pedidos"].rolling(7, min_periods=1).mean()

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=dia_df["DATA_ATUALIZACAO"], y=dia_df["Pedidos"],
            mode="none", fill="tozeroy", fillcolor="rgba(0,194,45,0.07)",
            showlegend=False, hoverinfo="skip"
        ))
        fig4.add_trace(go.Scatter(
            x=dia_df["DATA_ATUALIZACAO"], y=dia_df["Pedidos"],
            mode="lines+markers", name="Pedidos/dia",
            line=dict(color=GREEN, width=2, shape="spline", smoothing=0.8),
            marker=dict(size=5, color=GREEN, line=dict(color=PLOT_BG, width=1.5)),
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Pedidos: %{y}<extra></extra>"
        ))
        fig4.add_trace(go.Scatter(
            x=dia_df["DATA_ATUALIZACAO"], y=dia_df["Media_Movel"],
            mode="lines", name="Média 7 dias",
            line=dict(color="rgba(0,194,45,0.35)", width=1.5, dash="dot"),
            hovertemplate="<b>Média:</b> %{y:.1f}<extra></extra>"
        ))
        layout_fig4 = base_layout(height=450)
        layout_fig4["xaxis"] = dict(
            gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)',
            tickfont=dict(size=10), tickformat="%d/%m", showgrid=True
        )
        layout_fig4["yaxis"] = dict(
            gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)',
            tickfont=dict(size=10), rangemode="tozero"
        )
        layout_fig4["xaxis_title"] = ""
        layout_fig4["yaxis_title"] = ""
        layout_fig4["hovermode"] = "x unified"
        layout_fig4["legend"] = dict(
            orientation="h", y=1.08, x=1, xanchor="right",
            bgcolor='rgba(0,0,0,0)', font=dict(size=10, color=TEXT_COLOR)
        )
        fig4.update_layout(**layout_fig4)
        st.plotly_chart(fig4, width='stretch')

    # =========================
    # RANKING DE CLIENTES
    # =========================
    separador("Clientes")
    st.subheader("Ranking de Clientes")

    cliente_rank = (
        df.groupby("RAZAO_SOCIAL")["CODOSA"].count().reset_index()
        .rename(columns={"RAZAO_SOCIAL": "Cliente", "CODOSA": "Pedidos"})
        .sort_values("Pedidos", ascending=True).tail(10)
    )
    fig5 = px.bar(
        cliente_rank, x="Pedidos", y="Cliente", orientation="h",
        color="Pedidos", color_continuous_scale=[[0, "#0D3320"], [1, GREEN]], text="Pedidos"
    )
    fig5.update_traces(textposition="outside", textfont_color="#C8D6E5", marker_line_width=0)
    fig5.update_layout(
        **base_layout(height=450),
        coloraxis_showscale=False, bargap=0.3,
        xaxis_title="Pedidos", yaxis_title=""
    )
    fig5.update_layout(margin=dict(l=320, r=60, t=36, b=16))
    st.plotly_chart(fig5, width='stretch')

    # =========================
    # RANKING DE TRANSPORTADORAS
    # =========================
    separador("Transportadoras")
    st.subheader("Ranking de Transportadoras")

    transp_rank = (
        df.groupby("TRANSPORTADOR")["CODOSA"].count().reset_index()
        .rename(columns={"CODOSA": "Pedidos", "TRANSPORTADOR": "Transportadora"})
        .sort_values("Pedidos", ascending=True).tail(10)
    )
    fig6 = px.bar(
        transp_rank, x="Pedidos", y="Transportadora", orientation="h",
        color="Pedidos", color_continuous_scale=[[0, "#0D3320"], [1, GREEN]], text="Pedidos"
    )
    fig6.update_traces(textposition="outside", textfont_color="#C8D6E5", marker_line_width=0)
    fig6.update_layout(
        **base_layout(height=380),
        coloraxis_showscale=False, bargap=0.3,
        xaxis_title="Pedidos", yaxis_title=""
    )
    fig6.update_layout(margin=dict(l=280, r=60, t=36, b=16))
    st.plotly_chart(fig6, width='stretch')

    # =========================
    # TABELA AO VIVO
    # =========================
    separador("Base Operacional")

    df_display = df[[
        "DATA_ATUALIZACAO", "STATUS", "RAZAO_SOCIAL",
        "FILIAL", "Operador", "TRANSPORTADOR", "QUANTIDADE_SEPARADA"
    ]].copy()
    df_display["DATA_ATUALIZACAO"] = df_display["DATA_ATUALIZACAO"].dt.strftime("%Y-%m-%d %H:%M")
    df_display = df_display.sort_values("DATA_ATUALIZACAO", ascending=False)

    rows_json = df_display.rename(columns={
        "DATA_ATUALIZACAO":    "date",
        "STATUS":              "status",
        "RAZAO_SOCIAL":        "razao",
        "FILIAL":              "filial",
        "Operador":            "user",
        "TRANSPORTADOR":       "transp",
        "QUANTIDADE_SEPARADA": "qty"
    }).to_dict(orient="records")

    max_qty = float(df_display["QUANTIDADE_SEPARADA"].max() or 1)

    html = f"""
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  .panel {{
    background: #0D1825;
    border: 1px solid rgba(0,194,45,0.15);
    border-radius: 12px;
    overflow: hidden;
    font-family: Inter, sans-serif;
  }}
  .panel-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 20px; border-bottom: 1px solid rgba(0,194,45,0.1);
    background: #0A1420;
  }}
  .panel-title {{
    font-size: 13px; font-weight: 600; color: #C8D6E5;
    letter-spacing: .08em; text-transform: uppercase;
  }}
  .live-badge {{
    display: flex; align-items: center; gap: 6px;
    background: rgba(0,194,45,0.08); border: 1px solid rgba(0,194,45,0.25);
    border-radius: 20px; padding: 4px 10px;
    font-size: 11px; color: #00C22D; font-weight: 600; letter-spacing: .06em;
  }}
  .live-dot {{
    width: 6px; height: 6px; background: #00C22D;
    border-radius: 50%; animation: pulse 1.4s ease-in-out infinite;
    box-shadow: 0 0 6px #00C22D;
  }}
  @keyframes pulse {{
    0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.4;transform:scale(.7)}}
  }}
  .counter-badge {{
    font-size: 11px; color: #6B7A8F;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; padding: 4px 10px;
  }}
  .table-wrapper {{ overflow: hidden; position: relative; height: 400px; }}
  .table-wrapper::after {{
    content:''; position: absolute; bottom:0; left:0; right:0; height: 60px;
    background: linear-gradient(transparent, #0D1825);
    pointer-events: none; z-index: 2;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  thead th {{
    position: sticky; top: 0; background: #0A1420; color: #6B7A8F;
    font-size: 10px; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; padding: 10px 14px; text-align: left;
    border-bottom: 1px solid rgba(0,194,45,0.1); z-index: 3;
  }}
  thead th:last-child {{ text-align: right; }}
  .scroll-body tr {{
    border-bottom: 1px solid rgba(255,255,255,0.03);
    transition: background 0.2s; animation: slideIn .4s ease both;
  }}
  @keyframes slideIn {{
    from{{opacity:0;transform:translateX(-8px)}} to{{opacity:1;transform:translateX(0)}}
  }}
  .scroll-body tr:hover {{ background: rgba(0,194,45,0.04); }}
  .scroll-body tr.new-row {{ animation: newRowFlash 1.2s ease both; }}
  @keyframes newRowFlash {{
    0%{{background:rgba(0,194,45,0.18)}} 100%{{background:transparent}}
  }}
  .scroll-body td {{ padding: 10px 14px; color: #C8D6E5; white-space: nowrap; }}
  .scroll-body td:last-child {{ text-align: right; }}
  .idx {{ color: #3A4A5C; font-size: 10px; width: 28px; }}
  .status-pill {{
    display: inline-block; padding: 3px 8px; border-radius: 20px;
    font-size: 10px; font-weight: 600; letter-spacing: .05em;
  }}
  .s-fin  {{ background:rgba(0,194,45,.12);  color:#00C22D; border:1px solid rgba(0,194,45,.25); }}
  .s-sep  {{ background:rgba(34,211,238,.1); color:#22D3EE; border:1px solid rgba(34,211,238,.2); }}
  .s-agu  {{ background:rgba(245,158,11,.1); color:#F59E0B; border:1px solid rgba(245,158,11,.2); }}
  .user-cell {{ display:flex; align-items:center; gap:7px; }}
  .avatar {{
    width:22px; height:22px; border-radius:50%;
    background:linear-gradient(135deg,#0D3320,#00C22D22);
    border:1px solid rgba(0,194,45,.3);
    display:flex; align-items:center; justify-content:center;
    font-size:8px; font-weight:700; color:#00C22D; flex-shrink:0;
  }}
  .qty-bar {{ display:flex; align-items:center; gap:6px; justify-content:flex-end; }}
  .qty-val {{ font-weight:600; color:#00C22D; min-width:36px; text-align:right; }}
  .bar-bg  {{ width:48px; height:3px; background:rgba(255,255,255,.06); border-radius:2px; overflow:hidden; }}
  .bar-fill {{ height:100%; background:#00C22D; border-radius:2px; transition:width .6s ease; }}
  .razao {{ max-width:160px; overflow:hidden; text-overflow:ellipsis; color:#8A9AB0; }}
  .transp {{ max-width:120px; overflow:hidden; text-overflow:ellipsis; color:#6B7A8F; font-size:11px; }}
  .data-cell {{ color:#4A5A6A; font-size:11px; font-family:monospace; }}
  .footer-bar {{
    display:flex; align-items:center; justify-content:space-between;
    padding: 10px 20px; border-top:1px solid rgba(0,194,45,.08);
    background:#0A1420; font-size:11px; color:#4A5A6A;
  }}
  .footer-bar span {{ color:#00C22D; font-weight:600; }}
  .speed-ctrl {{ display:flex; align-items:center; gap:8px; }}
  .speed-ctrl select {{
    background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
    color:#C8D6E5; font-size:11px; border-radius:6px; padding:2px 6px; cursor:pointer;
  }}
</style>

<div class="panel">
  <div class="panel-header">
    <span class="panel-title">Base Operacional — Expedições</span>
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="counter-badge" id="rowCount">0 registros</span>
      <span class="live-badge"><span class="live-dot"></span>AO VIVO</span>
    </div>
  </div>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th class="idx">#</th>
          <th>Data</th>
          <th>Status</th>
          <th>Cliente</th>
          <th>Filial</th>
          <th>Operador</th>
          <th>Transportadora</th>
          <th style="text-align:right">Qtd. Sep.</th>
        </tr>
      </thead>
      <tbody class="scroll-body" id="tableBody"></tbody>
    </table>
  </div>
  <div class="footer-bar">
    <div>Total separado: <span id="totalSep">0</span> unid.</div>
    <div class="speed-ctrl">
      Velocidade:
      <select id="speedSel" onchange="setSpeed(this.value)">
        <option value="2500">Normal</option>
        <option value="1200">Rápido</option>
        <option value="4500">Lento</option>
      </select>
    </div>
    <div>Último: <span id="lastTime">—</span></div>
  </div>
</div>

<script>
const ROWS = {json.dumps(rows_json, ensure_ascii=False)};
const MAX_QTY = {max_qty};
let pointer = 0, interval, displayedRows = [];
const tbody = document.getElementById('tableBody');
let speed = 2500;

function statusClass(s) {{
  if (s.includes('FINALIZADO'))                                      return 's-fin';
  if (s.includes('EM SEPARACAO') || s.includes('EM SEPARAÇÃO'))     return 's-sep';
  return 's-agu';
}}
function initials(u) {{ return (u||'??').split('.').map(p=>p[0]).join('').slice(0,2).toUpperCase(); }}
function formatDate(d) {{ return String(d).slice(5,16).replace(/-/g,'/'); }}

function renderRow(row, idx, isNew) {{
  const tr = document.createElement('tr');
  if (isNew) tr.classList.add('new-row');
  const qty = Number(row.qty) || 0;
  const pct = Math.round((qty / MAX_QTY) * 100);
  tr.innerHTML = `
    <td class="idx">${{idx}}</td>
    <td class="data-cell">${{formatDate(row.date)}}</td>
    <td><span class="status-pill ${{statusClass(row.status)}}">${{row.status}}</span></td>
    <td class="razao" title="${{row.razao}}">${{row.razao}}</td>
    <td style="color:#4A5A6A;text-align:center">${{row.filial}}</td>
    <td>
      <div class="user-cell">
        <div class="avatar">${{initials(row.user)}}</div>
        <span style="color:#8A9AB0">${{(row.user||'').split('.')[0]}}</span>
      </div>
    </td>
    <td class="transp" title="${{row.transp}}">${{row.transp || '—'}}</td>
    <td>
      <div class="qty-bar">
        <div class="bar-bg"><div class="bar-fill" style="width:${{pct}}%"></div></div>
        <span class="qty-val">${{qty}}</span>
      </div>
    </td>
  `;
  return tr;
}}

function updateStats() {{
  const total = displayedRows.reduce((s,r) => s + (Number(r.qty)||0), 0);
  document.getElementById('totalSep').textContent  = total.toLocaleString('pt-BR');
  document.getElementById('rowCount').textContent  = displayedRows.length + ' registros';
  const last = displayedRows[displayedRows.length - 1];
  if (last) document.getElementById('lastTime').textContent = formatDate(last.date);
}}

function addRow() {{
  if (!ROWS.length) return;
  const row = ROWS[pointer % ROWS.length];
  pointer++;
  displayedRows.push(row);
  const tr = renderRow(row, displayedRows.length, true);
  tbody.prepend(tr);
  if (tbody.children.length > 14) {{
    const last = tbody.lastChild;
    last.style.transition = 'opacity 0.3s';
    last.style.opacity = '0';
    setTimeout(() => {{ if (last.parentNode) last.parentNode.removeChild(last); }}, 300);
  }}
  updateStats();
}}

function setSpeed(val) {{
  speed = parseInt(val);
  clearInterval(interval);
  interval = setInterval(addRow, speed);
}}

for (let i = 0; i < 10; i++) addRow();
interval = setInterval(addRow, speed);
</script>
"""

    st.components.v1.html(html, height=520, scrolling=False)