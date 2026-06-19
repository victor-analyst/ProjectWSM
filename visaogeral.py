import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db import get_engine


@st.cache_data(ttl=120, show_spinner=False)
def _load_saldo():
    query = """
    SELECT RAZSOC, SALFIN, ETIQUE, CODFIL
    FROM db_visual_SALOG.dbo.VW_PAINEL_SALDO_PRODUTOS_WMS
    """
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)


def show():
    df_raw = _load_saldo()
    filiais = st.multiselect(
        "Filial",
        sorted(df_raw["CODFIL"].dropna().unique())
    )
    df = df_raw[df_raw["CODFIL"].isin(filiais)] if filiais else df_raw

    # =========================
    # TRATAMENTO
    # =========================
    TOTAL_ENDERECOS = 7311

    valor_total_estoque = df["SALFIN"].sum()
    enderecos_ocupados  = df["ETIQUE"].nunique()
    taxa_ocupacao       = (enderecos_ocupados / TOTAL_ENDERECOS) * 100
    enderecos_vazios    = TOTAL_ENDERECOS - enderecos_ocupados

    # =========================
    # HEADER + PÍLULA DE REGISTROS
    # =========================
    total_registros = len(df)
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap; margin-bottom:4px;">
        <h1 style="margin:0;">VISÃO GERAL - SALOG</h1>
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
    <p style='color:#FFFFFF;margin-top:4px;margin-bottom:0;'>Monitoramento de Estoque e Ocupação</p>
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
    # KPI CARD
    # =========================
    def badge_color(valor, inverso=False):
        if inverso:
            if valor == 0:   return "#00C22D", "rgba(0,194,45,0.12)",   "rgba(0,194,45,0.3)"
            if valor <= 20:  return "#F59E0B", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)"
            return               "#EF4444", "rgba(239,68,68,0.12)",   "rgba(239,68,68,0.3)"
        else:
            if valor >= 80:  return "#00C22D", "rgba(0,194,45,0.12)",   "rgba(0,194,45,0.3)"
            if valor >= 40:  return "#F59E0B", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)"
            return               "#EF4444", "rgba(239,68,68,0.12)",   "rgba(239,68,68,0.3)"

    def kpi_card(label, valor_display, pct, bar_color, badge_color, badge_bg, badge_border, suffix="%"):
        return f"""
        <style>
        @keyframes fillBar {{
            from {{ width: 0; }}
            to   {{ width: {min(pct, 100)}%; }}
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
                ">{pct:.1f}{suffix}</span>
            </div>
            <div style="
                font-family:Inter,sans-serif; font-size:1.9rem;
                font-weight:800; color:#FFFFFF;
                letter-spacing:-0.02em; line-height:1;
                margin-bottom:12px;
            ">{valor_display}</div>
            <div style="
                height:3px; border-radius:2px;
                background:rgba(255,255,255,0.05); overflow:hidden;
            ">
                <div style="
                    height:100%; border-radius:2px;
                    background:{bar_color};
                    width:{min(pct, 100)}%;
                    animation: fillBar 1s ease both;
                "></div>
            </div>
        </div>
        """

    # ── cores dos cards ──
    c_ocu_color, c_ocu_bg, c_ocu_border = badge_color(taxa_ocupacao)
    c_vaz_color, c_vaz_bg, c_vaz_border = badge_color(
        (enderecos_vazios / TOTAL_ENDERECOS) * 100, inverso=True
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        if valor_total_estoque >= 1_000_000:
            val_fmt = f"R$ {valor_total_estoque/1_000_000:.1f}M"
        elif valor_total_estoque >= 1_000:
            val_fmt = f"R$ {valor_total_estoque/1_000:.0f}K"
        else:
            val_fmt = f"R$ {valor_total_estoque:,.0f}"
        st.markdown(kpi_card(
            "Valor Total em Estoque", val_fmt, 100,
            "#22D3EE", "#22D3EE", "rgba(34,211,238,0.12)", "rgba(34,211,238,0.3)",
            suffix=""
        ), unsafe_allow_html=True)

    with k2:
        st.markdown(kpi_card(
            "Endereços Ocupados",
            f"{enderecos_ocupados:,}",
            taxa_ocupacao,
            c_ocu_color, c_ocu_color, c_ocu_bg, c_ocu_border
        ), unsafe_allow_html=True)

    with k3:
        st.markdown(kpi_card(
            "% Ocupação",
            f"{taxa_ocupacao:.1f}%",
            taxa_ocupacao,
            c_ocu_color, c_ocu_color, c_ocu_bg, c_ocu_border
        ), unsafe_allow_html=True)

    with k4:
        pct_vaz = (enderecos_vazios / TOTAL_ENDERECOS) * 100
        st.markdown(kpi_card(
            "Endereços Vazios",
            f"{enderecos_vazios:,}",
            pct_vaz,
            c_vaz_color, c_vaz_color, c_vaz_bg, c_vaz_border
        ), unsafe_allow_html=True)

    # =========================
    # PALETA
    # =========================
    PLOT_BG    = "#0A1420"
    PAPER_BG   = "#0D1825"
    GRID_COLOR = "rgba(255,255,255,0.04)"
    TEXT_COLOR = "#6B7A8F"
    GREEN      = "#00C22D"

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
    # GRÁFICO 1 — FUNIL CUSTOMIZADO (components.html)
    # =========================
    separador("-")
    st.subheader("Valor em Estoque por Cliente")

    funil_df = (
        df.groupby("RAZSOC")["SALFIN"].sum()
        .reset_index()
        .rename(columns={"RAZSOC": "Cliente", "SALFIN": "Valor"})
        .sort_values("Valor", ascending=False)
        .head(15)
    )

    FUNNEL_TOP    = (0, 226, 122)
    FUNNEL_BOTTOM = (28, 58, 110)

    def _lerp_color(c1, c2, t):
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        return f"rgb({r},{g},{b})"

    def fmt_valor(v):
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"R$ {v/1_000:.0f}K"
        return f"R$ {v:,.0f}"

    n_steps   = len(funil_df)
    max_valor = funil_df["Valor"].iloc[0]
    valores   = funil_df["Valor"].tolist()
    clientes  = funil_df["Cliente"].tolist()

    ROW_H   = 30   # px por fatia
    GAP     = 15    # px entre fatias
    MIN_W   = 0.28 # largura mínima como fração do total
    SVG_W   = 950  # largura lógica do SVG
    TAPER   = 16   # tapering por lado em px

    # Monta linhas SVG
    slices_svg = ""
    diff_svg   = ""
    legend_rows = ""

    for i, (cliente, valor) in enumerate(zip(clientes, valores)):
        t        = i / max(n_steps - 1, 1)
        color    = _lerp_color(FUNNEL_TOP, FUNNEL_BOTTOM, t)
        frac     = MIN_W + (1 - MIN_W) * (valor / max_valor)
        slice_w  = SVG_W * frac
        x0       = (SVG_W - slice_w) / 2
        y0       = i * (ROW_H + GAP)

        top_w = slice_w
        bot_w = max(slice_w - TAPER * 2, slice_w * 0.88)
        tx    = (SVG_W - top_w) / 2
        bx    = (SVG_W - bot_w) / 2

        pts = f"{tx},{y0} {tx+top_w},{y0} {bx+bot_w},{y0+ROW_H} {bx},{y0+ROW_H}"

        val_label   = fmt_valor(valor)
        cx          = SVG_W / 2
        cy          = y0 + ROW_H / 2
        text_color  = "#0A1420" if i < 2 else "#FFFFFF"
        delay_ms    = i * 60

        slices_svg += f"""
        <g class="funil-slice" style="animation-delay:{delay_ms}ms" role="img" aria-label="{i+1}. {cliente}: {val_label}">
          <polygon points="{pts}" fill="{color}"/>
          <polygon points="{pts}" fill="rgba(255,255,255,0.07)" clip-path="url(#sheen{i})"/>
          <text x="{cx - 38}" y="{cy}" dominant-baseline="central" text-anchor="end"
                font-family="Inter,sans-serif" font-size="13" font-weight="600"
                fill="rgba(10,20,32,0.7)">{i+1}</text>
          <text x="{cx - 22}" y="{cy}" dominant-baseline="central" text-anchor="start"
                font-family="Inter,sans-serif" font-size="14" font-weight="700"
                fill="{text_color}">{val_label}</text>
        </g>
        """

        # Percentual de diferença entre fatias
        if i > 0:
            diff_pct = (valor - valores[i-1]) / valores[i-1] * 100
            diff_y   = y0 - GAP / 2
            diff_svg += f"""
            <text x="{SVG_W/2}" y="{diff_y}" dominant-baseline="central" text-anchor="middle"
                  font-family="Inter,sans-serif" font-size="10" fill="rgba(255,255,255,0.3)">{diff_pct:.1f}%</text>
            """

        # Legend rows (2 colunas)
        legend_rows += f"""
        <div class="leg-item">
          <span class="leg-dot" style="background:{color}"></span>
          <span class="leg-rank">{i+1}.</span>
          <span class="leg-name" title="{cliente}">{cliente}</span>
          <span class="leg-val">{val_label}</span>
        </div>
        """

    # Clippath para sheen (reflexo superior em cada fatia)
    defs_svg = "<defs>"
    for i, valor in enumerate(valores):
        frac    = MIN_W + (1 - MIN_W) * (valor / max_valor)
        slice_w = SVG_W * frac
        y0      = i * (ROW_H + GAP)
        tx      = (SVG_W - slice_w) / 2
        defs_svg += f'<clipPath id="sheen{i}"><rect x="{tx}" y="{y0}" width="{slice_w}" height="{ROW_H * 0.48}"/></clipPath>'
    defs_svg += "</defs>"

    total_h = n_steps * ROW_H + (n_steps - 1) * GAP

    funil_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8"/>
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{ background: #0D1825; font-family: Inter, sans-serif; padding: 16px; }}

      .funil-header {{
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 14px;
      }}
      .funil-meta {{
        font-size: 11px; color: #6B7A8F; letter-spacing: 0.06em;
      }}

      @keyframes fadeSlice {{
        from {{ opacity: 0; transform: scaleX(0.94); }}
        to   {{ opacity: 1; transform: scaleX(1); }}
      }}
      .funil-slice {{
        animation: fadeSlice 0.45s ease both;
        transform-origin: center;
      }}

      /* Tooltip */
      #tip {{
        position: fixed; background: #0D1825;
        border: 1px solid rgba(0,226,122,0.3);
        border-radius: 8px; padding: 8px 12px;
        font-size: 12px; color: #fff;
        pointer-events: none; display: none; z-index: 99;
        white-space: nowrap; max-width: 320px;
      }}

      /* Legend */
      .legend-grid {{
        display: grid; grid-template-columns: 1fr 1fr;
        gap: 5px 20px; margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid rgba(255,255,255,0.06);
      }}
      .leg-item {{
        display: flex; align-items: center; gap: 7px;
        padding: 3px 5px; border-radius: 5px; cursor: default;
        transition: background 0.15s;
      }}
      .leg-item:hover {{ background: rgba(255,255,255,0.04); }}
      .leg-dot {{
        width: 9px; height: 9px; border-radius: 2px; flex-shrink: 0;
      }}
      .leg-rank {{ font-size: 10px; color: #6B7A8F; min-width: 16px; }}
      .leg-name {{
        font-size: 11px; color: #C8D6E5;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;
      }}
      .leg-val {{ font-size: 11px; color: #6B7A8F; white-space: nowrap; }}
    </style>
    </head>
    <body>
      <div class="funil-header">
        <span class="funil-meta">Top fornecedores — valor total</span>
        <span class="funil-meta">{n_steps} fornecedores — exibindo top {n_steps}</span>
      </div>

      <svg id="funnel-svg" width="100%" viewBox="0 0 {SVG_W} {total_h}"
           xmlns="http://www.w3.org/2000/svg" style="display:block;">
        {defs_svg}
        {diff_svg}
        {slices_svg}
      </svg>

      <div class="legend-grid">
        {legend_rows}
      </div>

      <div id="tip"></div>

      <script>
        const tip = document.getElementById('tip');
        const names = {[repr(c) for c in clientes]};
        const vals  = {[repr(fmt_valor(v)) for v in valores]};

        document.querySelectorAll('.funil-slice').forEach((g, i) => {{
          g.style.cursor = 'pointer';
          g.addEventListener('mouseenter', e => {{
            tip.style.display = 'block';
            tip.innerHTML = '<strong>' + names[i] + '</strong><br>' + vals[i];
          }});
          g.addEventListener('mousemove', e => {{
            tip.style.left = (e.clientX + 14) + 'px';
            tip.style.top  = (e.clientY - 38) + 'px';
          }});
          g.addEventListener('mouseleave', () => {{ tip.style.display = 'none'; }});
        }});
      </script>
    </body>
    </html>
    """

    # Altura dinâmica: fatias + legenda (~22px por linha de legend, 2 colunas) + header + padding
    legend_rows_count = (n_steps + 1) // 2
    funil_height = total_h + legend_rows_count * 26 + 80
    components.html(funil_html, height=funil_height, scrolling=False)

    # =========================
    # GRÁFICO 2 — BARRAS (largura total)
    # =========================
    separador("-")
    st.subheader("Posições Ocupadas por Cliente")

    pos_df = (
        df.groupby("RAZSOC")["ETIQUE"].nunique()
        .reset_index()
        .rename(columns={"RAZSOC": "Cliente", "ETIQUE": "Posições"})
        .sort_values("Posições", ascending=True)
        .tail(15)
    )

    pos_df = pos_df.sort_values("Posições", ascending=False).reset_index(drop=True)
    n_bars = len(pos_df)
    max_pos = pos_df["Posições"].max()

    bars_rows = ""
    for i, row in pos_df.iterrows():
        pct = (row["Posições"] / max_pos) * 100
        is_leader = (i == 0)

        if is_leader:
            gradient = "linear-gradient(90deg, #0F6E56, #00E27A)"
            glow = "box-shadow: 0 0 22px rgba(0,226,122,0.55), 0 0 4px rgba(0,226,122,0.4) inset;"
        else:
            gradient = "linear-gradient(90deg, #0D3320, #1D9E75)"
            glow = ""

        show_inside = pct >= 18
        value_inside  = f'<span class="pos-value">{row["Posições"]:,}</span>' if show_inside else ""
        value_outside = "" if show_inside else f'<span class="pos-value-outside">{row["Posições"]:,}</span>'

        bars_rows += f"""
        <div class="pos-row">
            <div class="pos-label">{row['Cliente']}</div>
            <div class="pos-track">
                <div class="pos-fill" style="width:{pct:.2f}%; background:{gradient}; {glow}">
                    {value_inside}
                </div>
            </div>
            {value_outside}
        </div>
        """

    bars_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: transparent;
            font-family: Inter, sans-serif;
            padding: 8px 0;
        }}
        @keyframes fillBarPos {{
            from {{ width: 0%; }}
        }}
        .pos-row {{
            display: flex; align-items: center; gap: 16px;
            margin-bottom: 14px;
        }}
        .pos-label {{
            flex: 0 0 300px; text-align: right;
            font-family: Inter, sans-serif; font-size: 13px;
            color: #E2E8F0; white-space: nowrap; overflow: hidden;
            text-overflow: ellipsis;
        }}
        .pos-track {{
            flex: 1; height: 26px; border-radius: 8px;
            background: rgba(255,255,255,0.04);
            overflow: hidden; position: relative;
        }}
        .pos-fill {{
            height: 100%; border-radius: 8px;
            display: flex; align-items: center; justify-content: flex-end;
            padding-right: 10px; box-sizing: border-box;
            animation: fillBarPos 1.1s cubic-bezier(0.22,1,0.36,1) both;
            position: relative;
        }}
        .pos-fill::after {{
            content: ""; position: absolute; top: 0; left: 0; right: 0; height: 45%;
            background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(255,255,255,0));
            border-radius: 8px 8px 0 0;
        }}
        .pos-value {{
            font-family: Inter, sans-serif; font-weight: 700; font-size: 13px;
            color: #FFFFFF; position: relative; z-index: 1;
        }}
        .pos-value-outside {{
            font-family: Inter, sans-serif; font-weight: 700; font-size: 13px;
            color: #C8D6E5; margin-left: 10px; white-space: nowrap;
        }}
    </style>
    </head>
    <body>
        {bars_rows}
    </body>
    </html>
    """

    chart_height = n_bars * 42 + 20
    components.html(bars_html, height=chart_height, scrolling=False)

    # =========================
    # GAUGE — OCUPAÇÃO GERAL
    # =========================
    separador("Ocupação Geral do CD")

    col_gauge = st.columns([1, 2, 1])[1]
    with col_gauge:
        st.subheader("Taxa de Ocupação do Armazém")

        cor_gauge = (
            GREEN     if taxa_ocupacao < 70 else
            "#F59E0B" if taxa_ocupacao < 90 else
            "#EF4444"
        )

        fig3 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=taxa_ocupacao,
            number=dict(suffix="%", font=dict(size=48, color="#FFFFFF", family="Inter")),
            delta=dict(reference=80, valueformat=".1f", suffix="%"),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickwidth=1,
                    tickcolor=TEXT_COLOR,
                    tickfont=dict(size=10, color=TEXT_COLOR)
                ),
                bar=dict(color=cor_gauge, thickness=0.25),
                bgcolor=PLOT_BG,
                borderwidth=0,
                steps=[
                    dict(range=[0, 70],   color="rgba(0,194,45,0.06)"),
                    dict(range=[70, 90],  color="rgba(245,158,11,0.06)"),
                    dict(range=[90, 100], color="rgba(239,68,68,0.06)"),
                ],
                threshold=dict(
                    line=dict(color="#EF4444", width=2),
                    thickness=0.75,
                    value=90
                )
            )
        ))

        fig3.update_layout(
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PLOT_BG,
            height=320,
            margin=dict(l=40, r=40, t=40, b=20),
            font=dict(family="Inter", color=TEXT_COLOR, size=11),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown(f"""
        <div style="display:flex;justify-content:center;gap:24px;margin-top:-8px;margin-bottom:12px;">
            <span style="font-size:0.68rem;color:#00C22D;font-weight:600;">● Normal (0–70%)</span>
            <span style="font-size:0.68rem;color:#F59E0B;font-weight:600;">● Atenção (70–90%)</span>
            <span style="font-size:0.68rem;color:#EF4444;font-weight:600;">● Crítico (&gt;90%)</span>
        </div>
        <div style="
            display:flex;justify-content:center;gap:40px;
            background:rgba(13,24,37,0.6);border:1px solid rgba(0,194,45,0.1);
            border-radius:12px;padding:14px 24px;margin-bottom:24px;
        ">
            <div style="text-align:center;">
                <div style="font-size:0.60rem;color:#6B7A8F;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">Total Endereços</div>
                <div style="font-size:1.2rem;font-weight:800;color:#FFFFFF;">{TOTAL_ENDERECOS:,}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);"></div>
            <div style="text-align:center;">
                <div style="font-size:0.60rem;color:#6B7A8F;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">Ocupados</div>
                <div style="font-size:1.2rem;font-weight:800;color:{cor_gauge};">{enderecos_ocupados:,}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);"></div>
            <div style="text-align:center;">
                <div style="font-size:0.60rem;color:#6B7A8F;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">Disponíveis</div>
                <div style="font-size:1.2rem;font-weight:800;color:#22D3EE;">{enderecos_vazios:,}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # =========================
    # MAPA — DISTRIBUIÇÃO DE CLIENTES
    # =========================
    separador("Distribuição Geográfica de Clientes")
    st.subheader("Mapa de Cobertura — Clientes SALOG")

    import folium
    from streamlit_folium import st_folium
    import base64

    # ── Tabela estática de coordenadas por cidade (sem API externa) ──
    CIDADE_COORDS = {
        # São Paulo
        "SAO PAULO": (-23.5505, -46.6333), "CAMPINAS": (-22.9056, -47.0608),
        "GUARULHOS": (-23.4543, -46.5333), "SAO BERNARDO DO CAMPO": (-23.6939, -46.5650),
        "SANTO ANDRE": (-23.6639, -46.5383), "OSASCO": (-23.5325, -46.7919),
        "RIBEIRAO PRETO": (-21.1775, -47.8103), "SOROCABA": (-23.5015, -47.4526),
        "SAO JOSE DOS CAMPOS": (-23.1794, -45.8869), "SANTOS": (-23.9608, -46.3336),
        "MOGI DAS CRUZES": (-23.5228, -46.1875), "DIADEMA": (-23.6861, -46.6228),
        "JUNDIAI": (-23.1864, -46.8842), "PIRACICABA": (-22.7253, -47.6492),
        "BAURU": (-22.3246, -49.0600), "SAO JOSE DO RIO PRETO": (-20.8197, -49.3794),
        "MAUA": (-23.6678, -46.4617), "CARAPICUIBA": (-23.5228, -46.8350),
        "ITAQUAQUECETUBA": (-23.4869, -46.3483), "FRANCA": (-20.5386, -47.4008),
        "LIMEIRA": (-22.5647, -47.4014), "SUZANO": (-23.5428, -46.3108),
        "TAUBATE": (-23.0261, -45.5556), "PRAIA GRANDE": (-24.0056, -46.4028),
        "BARUERI": (-23.5058, -46.8767), "COTIA": (-23.6039, -46.9192),
        "MARILIA": (-22.2139, -49.9456), "AMERICANA": (-22.7386, -47.3314),
        "INDAIATUBA": (-23.0900, -47.2189), "ARARAQUARA": (-21.7942, -48.1758),
        "ARAÇATUBA": (-21.2094, -50.4331), "SAO CAETANO DO SUL": (-23.6211, -46.5619),
        "ITAPECERICA DA SERRA": (-23.7164, -46.8494), "EMBU DAS ARTES": (-23.6489, -46.8508),
        "TABOAO DA SERRA": (-23.6069, -46.7569), "FERRAZ DE VASCONCELOS": (-23.5411, -46.3689),
        "PRESIDENTE PRUDENTE": (-22.1208, -51.3886), "SAO VICENTE": (-23.9608, -46.3883),
        "BOTUCATU": (-22.8869, -48.4453), "CATANDUVA": (-21.1378, -48.9728),
        # Rio de Janeiro
        "RIO DE JANEIRO": (-22.9068, -43.1729), "NITEROI": (-22.8833, -43.1036),
        "DUQUE DE CAXIAS": (-22.7856, -43.3117), "NOVA IGUACU": (-22.7558, -43.4511),
        "SAO GONCALO": (-22.8269, -43.0539), "CAMPOS DOS GOYTACAZES": (-21.7553, -41.3297),
        "PETRÓPOLIS": (-22.5050, -43.1789), "VOLTA REDONDA": (-22.5231, -44.0997),
        "MACAE": (-22.3711, -41.7869), "ANGRA DOS REIS": (-23.0067, -44.3181),
        # Minas Gerais
        "BELO HORIZONTE": (-19.9167, -43.9345), "UBERLANDIA": (-18.9186, -48.2772),
        "CONTAGEM": (-19.9317, -44.0536), "JUIZ DE FORA": (-21.7642, -43.3503),
        "BETIM": (-19.9678, -44.1983), "MONTES CLAROS": (-16.7286, -43.8614),
        "RIBEIRAO DAS NEVES": (-19.7675, -44.0917), "UBERABA": (-19.7486, -47.9319),
        "GOVERNADOR VALADARES": (-18.8511, -41.9494), "IPATINGA": (-19.4678, -42.5364),
        "SETE LAGOAS": (-19.4681, -44.2469), "DIVINOPOLIS": (-20.1394, -44.8836),
        "SANTA LUZIA": (-19.7717, -43.8514), "ITABIRA": (-19.6189, -43.2267),
        "POCOS DE CALDAS": (-21.7872, -46.5614),
        # Rio Grande do Sul
        "PORTO ALEGRE": (-30.0346, -51.2177), "CAXIAS DO SUL": (-29.1681, -51.1794),
        "CANOAS": (-29.9178, -51.1839), "PELOTAS": (-31.7654, -52.3376),
        "SANTA MARIA": (-29.6842, -53.8069), "GRAVATAÍ": (-29.9444, -50.9917),
        "VIAMAO": (-30.0811, -51.0233), "NOVO HAMBURGO": (-29.6783, -51.1317),
        "SAO LEOPOLDO": (-29.7608, -51.1483), "RIO GRANDE": (-32.0350, -52.1006),
        "PASSO FUNDO": (-28.2622, -52.4083), "SAPUCAIA DO SUL": (-29.8283, -51.1508),
        # Paraná
        "CURITIBA": (-25.4284, -49.2733), "LONDRINA": (-23.3045, -51.1696),
        "MARINGA": (-23.4205, -51.9333), "PONTA GROSSA": (-25.0950, -50.1619),
        "CASCAVEL": (-24.9578, -53.4550), "SAO JOSE DOS PINHAIS": (-25.5350, -49.2083),
        "FOZ DO IGUACU": (-25.5478, -54.5882), "COLOMBO": (-25.2917, -49.2236),
        "GUARAPUAVA": (-25.3950, -51.4578), "PARANAGUA": (-25.5200, -48.5089),
        "ARAUCARIA": (-25.5928, -49.4094), "TOLEDO": (-24.7244, -53.7428),
        "APUCARANA": (-23.5508, -51.4608), "CAMPO LARGO": (-25.4589, -49.5283),
        # Santa Catarina
        "FLORIANOPOLIS": (-27.5954, -48.5480), "JOINVILLE": (-26.3044, -48.8487),
        "BLUMENAU": (-26.9194, -49.0661), "SAO JOSE": (-27.5936, -48.6236),
        "CHAPECO": (-27.1006, -52.6150), "ITAJAI": (-26.9078, -48.6619),
        "LAGES": (-27.8153, -50.3261), "CRICIUMA": (-28.6775, -49.3697),
        "CAMBORIU": (-27.0228, -48.6550), "JARAGUA DO SUL": (-26.4856, -49.0658),
        # Bahia
        "SALVADOR": (-12.9714, -38.5014), "FEIRA DE SANTANA": (-12.2664, -38.9663),
        "VITORIA DA CONQUISTA": (-14.8619, -40.8442), "CAMAÇARI": (-12.6994, -38.3244),
        "ITABUNA": (-14.7858, -39.2800), "ILHEUS": (-14.7886, -39.0492),
        "LAURO DE FREITAS": (-12.8983, -38.3294), "JUAZEIRO": (-9.4136, -40.5028),
        # Goiás
        "GOIANIA": (-16.6869, -49.2648), "APARECIDA DE GOIANIA": (-16.8236, -49.2439),
        "ANAPOLIS": (-16.3281, -48.9522), "RIO VERDE": (-17.7981, -50.9281),
        # Distrito Federal
        "BRASILIA": (-15.7942, -47.8822), "TAGUATINGA": (-15.8319, -48.0542),
        # Pernambuco
        "RECIFE": (-8.0476, -34.8770), "CARUARU": (-8.2756, -35.9764),
        "OLINDA": (-8.0089, -34.8553), "PETROLINA": (-9.3989, -40.5022),
        "PAULISTA": (-7.9397, -34.8728), "JABOATAO DOS GUARARAPES": (-8.1131, -35.0147),
        # Ceará
        "FORTALEZA": (-3.7172, -38.5433), "CAUCAIA": (-3.7361, -38.6528),
        "JUAZEIRO DO NORTE": (-7.2131, -39.3153), "MARACANAU": (-3.8775, -38.6256),
        # Mato Grosso
        "CUIABA": (-15.5989, -56.0949), "VARZEA GRANDE": (-15.6461, -56.1322),
        "RONDONOPOLIS": (-16.4700, -54.6358), "SINOP": (-11.8644, -55.5044),
        # Mato Grosso do Sul
        "CAMPO GRANDE": (-20.4428, -54.6461), "DOURADOS": (-22.2211, -54.8056),
        "TRES LAGOAS": (-20.7514, -51.6789), "CORUMBA": (-19.0078, -57.6531),
        # Pará
        "BELEM": (-1.4558, -48.5044), "ANANINDEUA": (-1.3656, -48.3722),
        "SANTAREM": (-2.4386, -54.7081), "MARABA": (-5.3686, -49.1178),
        # Amazonas
        "MANAUS": (-3.1190, -60.0217), "PARINTINS": (-2.6278, -56.7358),
        # Maranhão
        "SAO LUIS": (-2.5297, -44.3028), "IMPERATRIZ": (-5.5258, -47.4908),
        # Espírito Santo
        "VITORIA": (-20.3155, -40.3128), "VILA VELHA": (-20.3297, -40.2922),
        "SERRA": (-20.1286, -40.3072), "CARIACICA": (-20.2636, -40.4200),
        # Rio Grande do Norte
        "NATAL": (-5.7945, -35.2120), "MOSSORO": (-5.1875, -37.3442),
        # Paraíba
        "JOAO PESSOA": (-7.1195, -34.8450), "CAMPINA GRANDE": (-7.2306, -35.8814),
        # Alagoas
        "MACEIO": (-9.6658, -35.7350), "ARAPIRACA": (-9.7528, -36.6608),
        # Sergipe
        "ARACAJU": (-10.9472, -37.0731), "NOSSA SENHORA DO SOCORRO": (-10.8533, -37.1250),
        # Piauí
        "TERESINA": (-5.0920, -42.8038), "PARNAIBA": (-2.9064, -41.7764),
        # Rondônia
        "PORTO VELHO": (-8.7612, -63.9004), "JI-PARANA": (-10.8797, -61.9550),
        # Tocantins
        "PALMAS": (-10.1753, -48.2982), "ARAGUAINA": (-7.1919, -48.2044),
        # Acre
        "RIO BRANCO": (-9.9754, -67.8249),
        # Amapá
        "MACAPA": (0.0349, -51.0694),
        # Roraima
        "BOA VISTA": (2.8235, -60.6758),
    }

    # Fallback por estado quando cidade não encontrada
    ESTADO_COORDS = {
        "SP": (-23.5505, -46.6333), "RJ": (-22.9068, -43.1729),
        "MG": (-19.9167, -43.9345), "RS": (-30.0346, -51.2177),
        "PR": (-25.4284, -49.2733), "SC": (-27.5954, -48.5480),
        "BA": (-12.9714, -38.5014), "GO": (-16.6869, -49.2648),
        "DF": (-15.7942, -47.8822), "PE": (-8.0476, -34.8770),
        "CE": (-3.7172, -38.5433), "MT": (-15.5989, -56.0949),
        "MS": (-20.4428, -54.6461), "PA": (-1.4558, -48.5044),
        "AM": (-3.1190, -60.0217), "MA": (-2.5297, -44.3028),
        "ES": (-20.3155, -40.3128), "RN": (-5.7945, -35.2120),
        "PB": (-7.1195, -34.8450), "AL": (-9.6658, -35.7350),
        "SE": (-10.9472, -37.0731), "PI": (-5.0920, -42.8038),
        "RO": (-8.7612, -63.9004), "TO": (-10.1753, -48.2982),
        "AC": (-9.9754, -67.8249), "AP": (0.0349, -51.0694),
        "RR": (2.8235, -60.6758),
    }

    def normalizar(texto):
        import unicodedata
        return unicodedata.normalize("NFD", str(texto).upper().strip()) \
            .encode("ascii", "ignore").decode("ascii")

    @st.cache_data(ttl=3600, show_spinner=False)
    def load_clientes():
        query_clientes = """
        SELECT
            RAZSOC,
            CODCEP,
            DESCRI,
            BAIRRO,
            ESTADO,
            ENDERE
        FROM db_visual_SALOG.dbo.VW_EXPORTA_CLIENTES
        WHERE ESTADO IS NOT NULL AND DESCRI IS NOT NULL
        """
        with get_engine().connect() as conn:
            return pd.read_sql(query_clientes, conn)

    @st.cache_data(ttl=86400, show_spinner=False)
    def mapear_coordenadas(df_raw):
        results = []
        for _, row in df_raw.iterrows():
            cidade_raw = str(row.get("DESCRI", "")).strip()
            estado     = str(row.get("ESTADO", "")).strip().upper()
            cidade_key = normalizar(cidade_raw)

            coords = CIDADE_COORDS.get(cidade_key) or ESTADO_COORDS.get(estado, (-15.7801, -47.9292))
            lat, lon = coords

            results.append({
                "RAZSOC": row.get("RAZSOC", ""),
                "CIDADE": cidade_raw,
                "BAIRRO": row.get("BAIRRO", ""),
                "ESTADO": estado,
                "ENDERE": row.get("ENDERE", ""),
                "CODCEP": row.get("CODCEP", ""),
                "lat": lat,
                "lon": lon,
            })
        return pd.DataFrame(results)

    with st.spinner("Carregando mapa de clientes..."):
        try:
            df_cli_raw = load_clientes()
            df_geo = mapear_coordenadas(df_cli_raw)
        except Exception as e:
            st.error(f"Erro ao carregar clientes: {e}")
            df_geo = pd.DataFrame()

    if not df_geo.empty:
        # ── Inicializa mapa Folium dark ──
        mapa = folium.Map(
            location=[-15.7801, -47.9292],
            zoom_start=4,
            tiles=None,
            prefer_canvas=True,
        )

        # Tile CartoDB Dark Matter
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr='&copy; <a href="https://carto.com/">CARTO</a>',
            name="Dark Matter",
            max_zoom=19,
        ).add_to(mapa)

        # ── Ícone SVG customizado ──
        def make_icon(color="#00E27A", size=10):
            svg = f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="{size*3}" height="{size*3}" viewBox="0 0 30 30">
              <circle cx="15" cy="15" r="10" fill="{color}" fill-opacity="0.18"/>
              <circle cx="15" cy="15" r="5.5" fill="{color}" fill-opacity="0.55"/>
              <circle cx="15" cy="15" r="3" fill="{color}"/>
            </svg>
            """
            encoded = base64.b64encode(svg.encode()).decode()
            return folium.DivIcon(
                html=f'<img src="data:image/svg+xml;base64,{encoded}" style="width:{size*3}px;height:{size*3}px;margin-left:-{size*3//2}px;margin-top:-{size*3//2}px;"/>',
                icon_size=(size * 3, size * 3),
                icon_anchor=(size * 3 // 2, size * 3 // 2),
            )

        # Agrupa por cidade
        df_agg = (
            df_geo.groupby(["lat", "lon", "CIDADE", "ESTADO"])
            .agg(
                clientes=("RAZSOC", lambda x: "<br>".join(sorted(set(x))[:5]) + (f"<br>+{len(set(x))-5} mais" if len(set(x)) > 5 else "")),
                total=("RAZSOC", "nunique"),
            )
            .reset_index()
        )

        for _, row in df_agg.iterrows():
            total = row["total"]
            if total >= 5:
                cor = "#00E27A"
                sz  = 14
            elif total >= 2:
                cor = "#00C25A"
                sz  = 11
            else:
                cor = "#00954A"
                sz  = 9

            popup_html = f"""
            <div style="
                font-family:Inter,sans-serif;
                background:#0D1825;
                color:#E2E8F0;
                border:1px solid rgba(0,226,122,0.3);
                border-radius:10px;
                padding:12px 16px;
                min-width:220px;
                font-size:13px;
            ">
                <div style="color:#00E27A;font-weight:700;font-size:14px;margin-bottom:6px;">
                    📍 {row['CIDADE']} — {row['ESTADO']}
                </div>
                <div style="color:#6B7A8F;font-size:11px;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.08em;">
                    {total} cliente{'s' if total > 1 else ''}
                </div>
                <div style="color:#C8D6E5;line-height:1.7;font-size:12px;">
                    {row['clientes']}
                </div>
            </div>
            """

            folium.Marker(
                location=[row["lat"], row["lon"]],
                icon=make_icon(color=cor, size=sz),
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=folium.Tooltip(
                    f"<b style='color:#00E27A'>{row['CIDADE']}</b> · {total} cliente(s)",
                    style="background:#0D1825;border:1px solid #00E27A33;color:#E2E8F0;font-family:Inter,sans-serif;font-size:12px;border-radius:6px;padding:6px 10px;",
                ),
            ).add_to(mapa)

        # ── CSS do mapa ──
        mapa.get_root().html.add_child(folium.Element("""
        <style>
            .leaflet-container {
                background: #080F18 !important;
                font-family: Inter, sans-serif !important;
            }
            .leaflet-popup-content-wrapper {
                background: transparent !important;
                border: none !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.7) !important;
                border-radius: 10px !important;
                padding: 0 !important;
            }
            .leaflet-popup-tip {
                background: #0D1825 !important;
            }
            .leaflet-control-zoom a {
                background: #0D1825 !important;
                color: #6B7A8F !important;
                border-color: rgba(255,255,255,0.06) !important;
            }
            .leaflet-control-zoom a:hover {
                background: #1A2A3A !important;
                color: #00E27A !important;
            }
            .leaflet-bar {
                border: 1px solid rgba(0,226,122,0.15) !important;
                border-radius: 8px !important;
                overflow: hidden;
            }
        </style>
        """))

        # ── Legenda flutuante ──
        total_cidades      = df_agg.shape[0]
        total_clientes_mapa = df_geo["RAZSOC"].nunique()
        estados_rep        = df_geo["ESTADO"].nunique()

        legend_html = f"""
        <div style="
            position: fixed; bottom: 28px; left: 28px; z-index: 9999;
            background: rgba(13,24,37,0.92);
            border: 1px solid rgba(0,226,122,0.2);
            border-radius: 12px; padding: 14px 18px;
            font-family: Inter, sans-serif; backdrop-filter: blur(8px);
        ">
            <div style="color:#6B7A8F;font-size:9px;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:10px;font-weight:700;">
                Cobertura Geográfica
            </div>
            <div style="display:flex;flex-direction:column;gap:7px;">
                <div style="display:flex;align-items:center;gap:9px;">
                    <svg width="14" height="14"><circle cx="7" cy="7" r="4" fill="#00E27A"/></svg>
                    <span style="color:#C8D6E5;font-size:11px;">5+ clientes</span>
                </div>
                <div style="display:flex;align-items:center;gap:9px;">
                    <svg width="14" height="14"><circle cx="7" cy="7" r="3.5" fill="#00C25A"/></svg>
                    <span style="color:#C8D6E5;font-size:11px;">2–4 clientes</span>
                </div>
                <div style="display:flex;align-items:center;gap:9px;">
                    <svg width="14" height="14"><circle cx="7" cy="7" r="3" fill="#00954A"/></svg>
                    <span style="color:#C8D6E5;font-size:11px;">1 cliente</span>
                </div>
            </div>
            <div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:10px;padding-top:10px;">
                <div style="color:#6B7A8F;font-size:9px;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Resumo</div>
                <div style="color:#00E27A;font-weight:800;font-size:18px;line-height:1;">{total_clientes_mapa}</div>
                <div style="color:#6B7A8F;font-size:10px;margin-bottom:6px;">clientes mapeados</div>
                <div style="color:#FFFFFF;font-weight:700;font-size:13px;">{total_cidades} cidades · {estados_rep} estados</div>
            </div>
        </div>
        """
        mapa.get_root().html.add_child(folium.Element(legend_html))

        # ── Renderiza ──
        st_folium(mapa, use_container_width=True, height=580, returned_objects=[])

        # ── Mini stats abaixo do mapa ──
        st.markdown(f"""
        <div style="
            display:flex; justify-content:center; gap:32px; flex-wrap:wrap;
            background:rgba(13,24,37,0.5); border:1px solid rgba(0,226,122,0.08);
            border-radius:12px; padding:16px 24px; margin-top:8px;
        ">
            <div style="text-align:center;">
                <div style="font-size:0.58rem;color:#6B7A8F;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:3px;">Clientes Mapeados</div>
                <div style="font-size:1.4rem;font-weight:800;color:#00E27A;">{total_clientes_mapa:,}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);"></div>
            <div style="text-align:center;">
                <div style="font-size:0.58rem;color:#6B7A8F;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:3px;">Cidades</div>
                <div style="font-size:1.4rem;font-weight:800;color:#FFFFFF;">{total_cidades:,}</div>
            </div>
            <div style="width:1px;background:rgba(255,255,255,0.06);"></div>
            <div style="text-align:center;">
                <div style="font-size:0.58rem;color:#6B7A8F;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:3px;">Estados</div>
                <div style="font-size:1.4rem;font-weight:800;color:#FFFFFF;">{estados_rep}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Nenhum dado de clientes disponível para exibição no mapa.")