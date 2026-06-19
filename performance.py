import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db import get_engine


@st.cache_data(ttl=120, show_spinner=False)
def _load_separacao():
    query = """
        SELECT
            FILIAL, PEDIDO, PEDIDO_CLIENTE, RAZAO_SOCIAL,
            QTD_UAM, OS, DATA_EMISSAO, SEPARADOR,
            DATA_INICIAL, DATA_FINAL
        FROM db_visual_SALOG.dbo.VW_WMS_PRODUTIVIDADE_SEPARACAO
        """
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=120, show_spinner=False)
def _load_recebimento_perf():
    query = """
        SELECT
            FILIAL, PEDIDO, PEDIDO_CLIENTE, FISICA, RAZAO_SOCIAL, NF_REMESSA,
            CONFERENTE_1, CONFERENTE_2, DATA_INICIAL, DATA_FINAL,
            USU_ENDERAMENTO, DATA_ENDERECAMENTO, QTD_UAM, OS, DATA_EMISSAO
        FROM db_visual_SALOG.dbo.VW_WMS_PRODUTIVIDADE_RECEBIMENTO
        """
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)


def show():

    # =========================
    # PALETA
    # =========================
    PLOT_BG    = "#0A1420"
    PAPER_BG   = "#0D1825"
    GRID_COLOR = "rgba(255,255,255,0.04)"
    TEXT_COLOR = "#6B7A8F"
    GREEN      = "#00C22D"
    NEON       = "#00E27A"
    COLORS     = ["#00C22D", "#22D3EE", "#F59E0B", "#EF4444", "#8B5CF6",
                  "#EC4899", "#14B8A6", "#F97316", "#A3E635", "#60A5FA",
                  "#818CF8", "#FB923C", "#34D399", "#F472B6", "#38BDF8"]

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

    def separador(label=""):
        st.markdown(f"""
        <style>
        @keyframes expandLine {{
            from {{ width: 0; opacity: 0; }}
            to   {{ width: 100%; opacity: 1; }}
        }}
        .sep-wrap {{ display: flex; align-items: center; gap: 14px; margin: 28px 0 20px 0; }}
        .sep-label {{
            font-family: Inter, sans-serif; font-size: 0.60rem; font-weight: 700;
            letter-spacing: 0.18em; text-transform: uppercase;
            color: rgba(0,194,45,0.5); white-space: nowrap;
        }}
        .sep-line {{
            flex: 1; height: 1px;
            background: linear-gradient(90deg, rgba(0,194,45,0.4), rgba(0,194,45,0.05), transparent);
            animation: expandLine 0.8s ease both;
        }}
        .sep-dot {{ width: 4px; height: 4px; border-radius: 50%; background: rgba(0,194,45,0.4); flex-shrink: 0; }}
        </style>
        <div class="sep-wrap">
            <span class="sep-dot"></span>
            {'<span class="sep-label">' + label + '</span>' if label else ''}
            <div class="sep-line"></div>
        </div>
        """, unsafe_allow_html=True)

    def kpi_card_destaque(label, valor_display, sublinha, accent_color):
        return f"""
        <div style="
            background:linear-gradient(135deg,#0D1825 0%,#0A1420 100%);
            border:1px solid rgba(255,255,255,0.06);
            border-radius:16px; padding:18px 20px 16px 20px;
            position:relative; overflow:hidden;
        ">
            <div style="
                position:absolute; top:0; left:0; right:0; height:2px;
                background:linear-gradient(90deg,transparent,{accent_color},transparent);
                opacity:0.6;
            "></div>
            <div style="
                font-family:Inter,sans-serif; font-size:0.62rem;
                font-weight:600; letter-spacing:0.1em;
                text-transform:uppercase; color:#C8D6E5; margin-bottom:10px;
            ">{label}</div>
            <div style="
                font-family:Inter,sans-serif; font-size:1.6rem;
                font-weight:800; color:#FFFFFF;
                letter-spacing:-0.02em; line-height:1.1; margin-bottom:6px;
            ">{valor_display}</div>
            <div style="
                font-family:Inter,sans-serif; font-size:0.68rem;
                font-weight:600; color:{accent_color};
            ">{sublinha}</div>
        </div>
        """

    # =========================
    # HEADER
    # =========================
    st.markdown("""
    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap; margin-bottom:4px;">
        <h1 style="margin:0;">PERFORMANCE OPERACIONAL - SALOG</h1>
    </div>
    <p style='color:#FFFFFF;margin-top:4px;margin-bottom:0;'>Produtividade de Separação e Recebimento</p>
    """, unsafe_allow_html=True)

    separador("-")

    # =========================
    # FILTRO DE PROCESSO
    # =========================
    processo = st.selectbox(
        "Processo",
        ["Separação", "Recebimento"],
        label_visibility="collapsed"
    )

    # =========================
    # TERMINOLOGIA POR PROCESSO
    # =========================
    TERMO = {
        "Separação": {
            "colaborador":       "Separador",
            "colaboradores":     "Separadores",
            "colaborador_ativo": "Separadores Ativos",
            "volume_label":      "UAM",
            "volume_plural":     "UAMs",
            "pedido_label":      "Pedido",
            "pedido_plural":     "Pedidos",
            "grafico_volume":    "Ranking de UAMs por Separador",
            "grafico_pedidos":   "Pedidos por Separador",
            "grafico_horas":     "Horas Trabalhadas por Separador",
            "grafico_tempo":     "Tempo Médio por Pedido por Separador",
            "grafico_produt":    "Produtividade por Hora — UAM/h",
            "grafico_diario":    "Evolução Diária — UAMs",
            "grafico_diario_op": "Evolução Diária por Separador — UAMs",
            "grafico_donut":     "Participação no Volume Total — UAMs",
            "subtitulo":         "Produtividade de Separação",
        },
        "Recebimento": {
            "colaborador":       "Conferente",
            "colaboradores":     "Conferentes",
            "colaborador_ativo": "Conferentes Ativos",
            "volume_label":      "Pallet",
            "volume_plural":     "Pallets",
            "pedido_label":      "NF",
            "pedido_plural":     "NFs",
            "grafico_volume":    "Ranking de Pallets por Conferente",
            "grafico_pedidos":   "NFs por Conferente",
            "grafico_horas":     "Horas Trabalhadas por Conferente",
            "grafico_tempo":     "Tempo Médio por NF por Conferente",
            "grafico_produt":    "Produtividade por Hora — Pallets/h",
            "grafico_diario":    "Evolução Diária — Pallets",
            "grafico_diario_op": "Evolução Diária por Conferente — Pallets",
            "grafico_donut":     "Participação no Volume Total — Pallets",
            "subtitulo":         "Produtividade de Recebimento",
        },
    }

    T = TERMO[processo]

    # =========================
    # QUERY + CARGA (cacheada)
    # =========================
    if processo == "Separação":
        df = _load_separacao()
    else:
        df = _load_recebimento_perf()

    # =========================
    # TRATAMENTO COMUM
    # =========================
    df["DATA_INICIAL"] = pd.to_datetime(df["DATA_INICIAL"], errors="coerce")
    df["DATA_FINAL"]   = pd.to_datetime(df["DATA_FINAL"],   errors="coerce")

    df["TEMPO_MINUTOS"] = (df["DATA_FINAL"] - df["DATA_INICIAL"]).dt.total_seconds() / 60
    df["TEMPO_HORAS"]   = df["TEMPO_MINUTOS"] / 60

    # remove linhas com tempo inválido
    df = df[df["TEMPO_MINUTOS"].notna() & (df["TEMPO_MINUTOS"] > 0)]

    # ── teto de 12h: descarta registros com tempo acima do limite operacional ──
    TETO_HORAS = 72
    registros_antes = len(df)
    df = df[df["TEMPO_HORAS"] <= TETO_HORAS]
    registros_descartados = registros_antes - len(df)
    if registros_descartados > 0:
        st.caption(f"⚠️ {registros_descartados} registro(s) descartado(s) por tempo acima de {TETO_HORAS}h (dados inconsistentes).")

    # ── normaliza nomes: uppercase + ponto → espaço ──
    def normalizar_nome(s):
        if pd.isna(s):
            return s
        return str(s).upper().replace(".", " ").strip()

    if processo == "Separação":
        df["OPERADOR"] = df["SEPARADOR"].apply(normalizar_nome)
    else:
        c1 = df["CONFERENTE_1"].apply(normalizar_nome)
        c2 = df["CONFERENTE_2"].apply(normalizar_nome)
        df["OPERADOR"] = c1.where(c1.notna() & (c1 != ""), c2)

    df = df[df["OPERADOR"].notna() & (df["OPERADOR"] != "")]

    # ── normaliza cliente ──
    df["RAZAO_SOCIAL"] = df["RAZAO_SOCIAL"].apply(normalizar_nome)

    # ── normaliza filial ──
    df["FILIAL"] = df["FILIAL"].astype(str).str.strip().str.upper()

    # =========================
    # FILTROS: Filial | Cliente | Colaborador | Data Inicial | Data Final
    # =========================
    f1, f2, f3, f4, f5 = st.columns([1.2, 1.8, 1.8, 1, 1])

    with f1:
        filiais = sorted(df["FILIAL"].dropna().unique().tolist())
        filial_sel = st.multiselect("Filial", filiais, placeholder="Todas")

    with f2:
        clientes = sorted(df["RAZAO_SOCIAL"].dropna().unique().tolist())
        cliente_sel = st.multiselect("Cliente", clientes, placeholder="Todos")

    with f3:
        colaboradores = sorted(df["OPERADOR"].dropna().unique().tolist())
        colab_sel = st.multiselect(T["colaborador"], colaboradores, placeholder="Todos")

    with f4:
        data_min = df["DATA_INICIAL"].min().date()
        data_max = df["DATA_INICIAL"].max().date()
        data_ini = st.date_input(
            "De",
            value=data_min,
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY",
        )

    with f5:
        data_fim = st.date_input(
            "Até",
            value=data_max,
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY",
        )

    # ── aplica filtros ──
    if filial_sel:
        df = df[df["FILIAL"].isin(filial_sel)]
    if cliente_sel:
        df = df[df["RAZAO_SOCIAL"].isin(cliente_sel)]
    if colab_sel:
        df = df[df["OPERADOR"].isin(colab_sel)]
    df = df[
        (df["DATA_INICIAL"].dt.date >= data_ini) &
        (df["DATA_INICIAL"].dt.date <= data_fim)
    ]

    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # =========================
    # AGREGAÇÃO POR OPERADOR
    # =========================
    agg_dict = {
        "QTD_UAM":       "sum",
        "PEDIDO":        "nunique",
        "TEMPO_HORAS":   "sum",
        "TEMPO_MINUTOS": "mean",
    }
    if processo == "Recebimento":
        agg_dict["NF_REMESSA"] = "nunique"

    op_df = df.groupby("OPERADOR").agg(agg_dict).reset_index()
    op_df = op_df.rename(columns={
        "QTD_UAM":       "QTD_TOTAL",
        "PEDIDO":        "QTD_PEDIDOS",
        "TEMPO_HORAS":   "HORAS_TRABALHADAS",
        "TEMPO_MINUTOS": "TEMPO_MEDIO_MIN",
    })
    if "NF_REMESSA" in op_df.columns:
        op_df = op_df.rename(columns={"NF_REMESSA": "QTD_NFS"})

    op_df["PRODUTIVIDADE_HORA"] = (
        op_df["QTD_TOTAL"] / op_df["HORAS_TRABALHADAS"].replace(0, pd.NA)
    )
    op_df = op_df.dropna(subset=["PRODUTIVIDADE_HORA"])

    # =========================
    # HELPER: formata tempo médio
    # =========================
    def fmt_tempo(minutos):
        if minutos >= 60:
            h = int(minutos // 60)
            m = int(minutos % 60)
            return f"{h}h {m:02d}min" if m else f"{h}h"
        return f"{minutos:.1f} min"

    # =========================
    # KPIs
    # =========================
    total_pedidos     = df["PEDIDO"].nunique()
    total_uam         = df["QTD_UAM"].sum()
    qtd_operadores    = df["OPERADOR"].nunique()
    tempo_medio_geral = df["TEMPO_MINUTOS"].mean()
    produt_media_geral = op_df["PRODUTIVIDADE_HORA"].mean() if not op_df.empty else 0

    if not op_df.empty:
        melhor_row   = op_df.sort_values("PRODUTIVIDADE_HORA", ascending=False).iloc[0]
        melhor_nome  = melhor_row["OPERADOR"]
        melhor_valor = melhor_row["PRODUTIVIDADE_HORA"]
    else:
        melhor_nome, melhor_valor = "—", 0

    separador("Indicadores do Período")

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(kpi_card_destaque(
            f"Total de {T['pedido_plural']}",
            f"{total_pedidos:,}",
            T["subtitulo"],
            "#22D3EE"
        ), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card_destaque(
            f"Total de {T['volume_plural']}",
            f"{total_uam:,.0f}",
            "Volume processado no período",
            NEON
        ), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card_destaque(
            T["colaborador_ativo"],
            f"{qtd_operadores}",
            "Colaboradores no período",
            "#8B5CF6"
        ), unsafe_allow_html=True)

    k4, k5, k6 = st.columns(3)
    with k4:
        st.markdown(kpi_card_destaque(
            f"Tempo Médio por {T['pedido_label']}",
            fmt_tempo(tempo_medio_geral),
            "Média geral da operação",
            "#F59E0B"
        ), unsafe_allow_html=True)
    with k5:
        st.markdown(kpi_card_destaque(
            "Produtividade Média",
            f"{produt_media_geral:.1f} {T['volume_label']}/h",
            f"Média entre {T['colaboradores'].lower()}",
            GREEN
        ), unsafe_allow_html=True)
    with k6:
        st.markdown(kpi_card_destaque(
            f"Melhor {T['colaborador']}",
            melhor_nome,
            f"{melhor_valor:.1f} {T['volume_label']}/h",
            "#EC4899"
        ), unsafe_allow_html=True)

    # =========================
    # GRÁFICO 1 — RANKING DE VOLUME (top 10)
    # =========================
    separador("-")
    st.subheader(T["grafico_volume"])

    rank_df = op_df.sort_values("QTD_TOTAL", ascending=False).head(10)
    rank_df = rank_df.sort_values("QTD_TOTAL", ascending=True)

    fig1 = px.bar(
        rank_df, x="QTD_TOTAL", y="OPERADOR", orientation="h",
        color="QTD_TOTAL",
        color_continuous_scale=[[0, "#0D3320"], [1, NEON]],
        text="QTD_TOTAL"
    )
    fig1.update_traces(
        texttemplate="<b>%{text:,.0f}</b>",
        textposition="outside",
        textfont_color="#E2E8F0",
        marker_line_width=0
    )
    layout1 = base_layout(height=460)
    layout1["coloraxis_showscale"] = False
    layout1["bargap"]  = 0.3
    layout1["xaxis"]   = dict(visible=False, range=[0, rank_df["QTD_TOTAL"].max() * 1.18])
    layout1["yaxis"]   = dict(title=None, tickfont=dict(size=11, color="#C8D6E5"), linecolor='rgba(0,0,0,0)')
    layout1["margin"]  = dict(l=200, r=80, t=10, b=10)
    fig1.update_layout(**layout1)
    st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # GRÁFICO 2 — PEDIDOS/NFs POR OPERADOR (top 10)
    # =========================
    separador("-")
    st.subheader(T["grafico_pedidos"])

    pedidos_df = op_df.sort_values("QTD_PEDIDOS", ascending=False).head(10)

    fig2 = px.bar(
        pedidos_df, x="OPERADOR", y="QTD_PEDIDOS",
        color="QTD_PEDIDOS",
        color_continuous_scale=[[0, "#0D3320"], [1, NEON]],
        text="QTD_PEDIDOS"
    )
    fig2.update_traces(
        texttemplate="<b>%{text:,.0f}</b>",
        textposition="outside",
        textfont_color="#E2E8F0",
        marker_line_width=0
    )
    layout2 = base_layout(height=420)
    layout2["coloraxis_showscale"] = False
    layout2["bargap"] = 0.3
    layout2["yaxis"]  = dict(visible=False)
    layout2["xaxis"]  = dict(
        title=None,
        tickfont=dict(size=10, color="#C8D6E5"),
        linecolor='rgba(0,0,0,0)', tickangle=-30
    )
    layout2["margin"] = dict(l=20, r=20, t=10, b=100)
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # GRÁFICO 3 — HORAS TRABALHADAS (top 10)
    # =========================
    separador("-")
    st.subheader(T["grafico_horas"])

    horas_df = op_df.sort_values("HORAS_TRABALHADAS", ascending=False).head(10)
    horas_df = horas_df.sort_values("HORAS_TRABALHADAS", ascending=True)

    fig3 = px.bar(
        horas_df, x="HORAS_TRABALHADAS", y="OPERADOR", orientation="h",
        color="HORAS_TRABALHADAS",
        color_continuous_scale=[[0, "#1C3A6E"], [1, "#22D3EE"]],
        text="HORAS_TRABALHADAS"
    )
    fig3.update_traces(
        texttemplate="<b>%{text:.1f}h</b>",
        textposition="outside",
        textfont_color="#E2E8F0",
        marker_line_width=0
    )
    layout3 = base_layout(height=460)
    layout3["coloraxis_showscale"] = False
    layout3["bargap"] = 0.3
    layout3["xaxis"]  = dict(visible=False, range=[0, horas_df["HORAS_TRABALHADAS"].max() * 1.18])
    layout3["yaxis"]  = dict(title=None, tickfont=dict(size=11, color="#C8D6E5"), linecolor='rgba(0,0,0,0)')
    layout3["margin"] = dict(l=200, r=80, t=10, b=10)
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True)

    # =========================
    # GRÁFICO 4 — TEMPO MÉDIO POR PEDIDO/NF (top 10 mais rápidos)
    # =========================
    separador("-")
    st.subheader(T["grafico_tempo"])

    tempo_df = op_df.sort_values("TEMPO_MEDIO_MIN", ascending=True).head(10)
    tempo_df = tempo_df.sort_values("TEMPO_MEDIO_MIN", ascending=False)
    tempo_df["TEMPO_FMT"] = tempo_df["TEMPO_MEDIO_MIN"].apply(fmt_tempo)

    fig4 = go.Figure(go.Bar(
        x=tempo_df["TEMPO_MEDIO_MIN"],
        y=tempo_df["OPERADOR"],
        orientation="h",
        marker=dict(
            color=tempo_df["TEMPO_MEDIO_MIN"],
            colorscale=[[0, NEON], [1, "#EF4444"]],
            line=dict(width=0),
            cornerradius=8,
        ),
        text=tempo_df["TEMPO_FMT"],
        textposition="outside",
        textfont=dict(family="Inter", size=12, color="#E2E8F0"),
        hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
    ))
    layout4 = base_layout(height=460)
    layout4["bargap"] = 0.3
    layout4["xaxis"]  = dict(visible=False, range=[0, tempo_df["TEMPO_MEDIO_MIN"].max() * 1.28])
    layout4["yaxis"]  = dict(title=None, tickfont=dict(size=11, color="#C8D6E5"), linecolor='rgba(0,0,0,0)')
    layout4["margin"] = dict(l=200, r=120, t=10, b=10)
    fig4.update_layout(**layout4)
    st.plotly_chart(fig4, use_container_width=True)

    # =========================
    # GRÁFICO 5 — PRODUTIVIDADE POR HORA (top 10, principal)
    # =========================
    separador("Indicador Principal")
    st.subheader(T["grafico_produt"])

    produt_df  = op_df.sort_values("PRODUTIVIDADE_HORA", ascending=False).head(10)
    produt_df  = produt_df.sort_values("PRODUTIVIDADE_HORA", ascending=True)
    max_produt = produt_df["PRODUTIVIDADE_HORA"].max()
    n_bars5    = len(produt_df)

    bar_colors5  = []
    line_colors5 = []
    line_widths5 = []
    for i in range(n_bars5):
        is_leader = (i == n_bars5 - 1)
        bar_colors5.append(
            NEON if is_leader
            else f"rgba(0,226,122,{0.25 + 0.5 * (i / max(n_bars5 - 2, 1)):.2f})"
        )
        line_colors5.append("rgba(0,226,122,0.9)" if is_leader else "rgba(0,0,0,0)")
        line_widths5.append(2 if is_leader else 0)

    fig5 = go.Figure(go.Bar(
        x=produt_df["PRODUTIVIDADE_HORA"],
        y=produt_df["OPERADOR"],
        orientation="h",
        marker=dict(
            color=bar_colors5,
            line=dict(color=line_colors5, width=line_widths5),
            cornerradius=10
        ),
        text=produt_df["PRODUTIVIDADE_HORA"],
        texttemplate="<b>%{text:.1f}</b>",
        textposition="outside",
        textfont=dict(family="Inter", size=13, color="#E2E8F0"),
        hovertemplate=f"<b>%{{y}}</b><br>%{{x:.1f}} {T['volume_label']}/h<extra></extra>",
    ))
    layout5 = base_layout(height=480)
    layout5["bargap"]     = 0.35
    layout5["xaxis"]      = dict(visible=False, range=[0, max_produt * 1.18])
    layout5["yaxis"]      = dict(title=None, tickfont=dict(size=13, color="#E2E8F0", family="Inter"), linecolor='rgba(0,0,0,0)')
    layout5["margin"]     = dict(l=200, r=80, t=10, b=10)
    layout5["hoverlabel"] = dict(bgcolor=PAPER_BG, bordercolor="rgba(0,226,122,0.35)", font=dict(family="Inter", size=12, color="#FFFFFF"))
    fig5.update_layout(**layout5)
    st.plotly_chart(fig5, use_container_width=True)

    # =========================
    # GRÁFICO 6 — EVOLUÇÃO DIÁRIA (total)
    # =========================
    separador("-")
    st.subheader(T["grafico_diario"])

    df["DATA_DIA"] = df["DATA_INICIAL"].dt.date
    diario_df = df.groupby("DATA_DIA")["QTD_UAM"].sum().reset_index().sort_values("DATA_DIA")

    fig6 = go.Figure(go.Scatter(
        x=diario_df["DATA_DIA"], y=diario_df["QTD_UAM"],
        mode="lines+markers",
        line=dict(color=NEON, width=3, shape="spline"),
        marker=dict(size=6, color=NEON, line=dict(color=PAPER_BG, width=1)),
        fill="tozeroy",
        fillcolor="rgba(0,226,122,0.08)",
        hovertemplate="<b>%{x|%d/%m/%Y}</b><br>%{y:,.0f}<extra></extra>"
    ))
    layout6 = base_layout(height=420)
    layout6["xaxis"] = dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=10, color="#C8D6E5"), title=None)
    layout6["yaxis"] = dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=10, color="#C8D6E5"), title=None)
    fig6.update_layout(**layout6)
    st.plotly_chart(fig6, use_container_width=True)

    # =========================
    # GRÁFICO 7 — EVOLUÇÃO DIÁRIA POR OPERADOR (top 6 por volume)
    # =========================
    separador("-")
    st.subheader(T["grafico_diario_op"])

    top6 = op_df.sort_values("QTD_TOTAL", ascending=False).head(6)["OPERADOR"].tolist()
    diario_op_df = (
        df[df["OPERADOR"].isin(top6)]
        .groupby(["DATA_DIA", "OPERADOR"])["QTD_UAM"].sum()
        .reset_index()
        .sort_values("DATA_DIA")
    )

    fig7 = px.line(
        diario_op_df, x="DATA_DIA", y="QTD_UAM", color="OPERADOR",
        color_discrete_sequence=COLORS, markers=True
    )
    fig7.update_traces(line=dict(width=2.5), marker=dict(size=5))
    layout7 = base_layout(height=460)
    layout7["xaxis"]  = dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=10, color="#C8D6E5"), title=None)
    layout7["yaxis"]  = dict(gridcolor=GRID_COLOR, linecolor='rgba(0,0,0,0)', tickfont=dict(size=10, color="#C8D6E5"), title=None)
    layout7["legend"] = dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10, color="#C8D6E5"), orientation="h", y=-0.25)
    fig7.update_layout(**layout7)
    st.plotly_chart(fig7, use_container_width=True)

    # =========================
    # GRÁFICO 8 — DONUT DE PARTICIPAÇÃO
    # =========================
    separador("Participação por Operador")
    st.subheader(T["grafico_donut"])

    donut_df = op_df.sort_values("QTD_TOTAL", ascending=False)

    fig8 = go.Figure(go.Pie(
        labels=donut_df["OPERADOR"],
        values=donut_df["QTD_TOTAL"],
        hole=0.62,
        marker=dict(colors=COLORS[:len(donut_df)], line=dict(color=PAPER_BG, width=2)),
        textinfo="percent",
        textfont=dict(family="Inter", size=11, color="#0A1420"),
        hovertemplate=f"<b>%{{label}}</b><br>%{{value:,.0f}} {T['volume_plural']} (%{{percent}})<extra></extra>"
    ))
    layout8 = base_layout(height=460)
    layout8["showlegend"]  = True
    layout8["legend"]      = dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10, color="#C8D6E5"))
    layout8["annotations"] = [dict(
        text=f"<b>{donut_df['QTD_TOTAL'].sum():,.0f}</b><br><span style='font-size:10px;color:#6B7A8F;'>{T['volume_plural'].upper()}</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(family="Inter", size=18, color="#FFFFFF")
    )]
    fig8.update_layout(**layout8)
    st.plotly_chart(fig8, use_container_width=True)

    st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:32px 0 0 0;">', unsafe_allow_html=True)