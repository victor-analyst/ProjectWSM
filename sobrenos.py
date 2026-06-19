import streamlit as st


def show():

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    .particles {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: 0; overflow: hidden;
    }
    .particle {
        position: absolute; border-radius: 50%;
        background: radial-gradient(circle, rgba(0,194,45,0.6), transparent 70%);
        animation: floatUp linear infinite;
        opacity: 0;
    }
    @keyframes floatUp {
        0%   { transform: translateY(100vh) scale(0); opacity: 0; }
        10%  { opacity: 0.4; }
        90%  { opacity: 0.1; }
        100% { transform: translateY(-10vh) scale(1); opacity: 0; }
    }

    .hero {
        position: relative; min-height: 92vh;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center; padding: 60px 20px;
        overflow: hidden;
    }
    .hero-bg {
        position: absolute; inset: 0; z-index: 0;
        background:
            radial-gradient(ellipse 80% 60% at 50% 0%,   rgba(0,194,45,0.18), transparent 60%),
            radial-gradient(ellipse 60% 40% at 20% 80%,  rgba(0,194,45,0.10), transparent 50%),
            radial-gradient(ellipse 50% 40% at 80% 100%, rgba(0,194,45,0.08), transparent 50%),
            linear-gradient(180deg, #03060A 0%, #050C10 50%, #03060A 100%);
    }
    .hero-grid {
        position: absolute; inset: 0; z-index: 0;
        background-image:
            linear-gradient(rgba(0,194,45,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,194,45,0.04) 1px, transparent 1px);
        background-size: 60px 60px;
        mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black, transparent);
    }
    .hero-content { position: relative; z-index: 2; max-width: 860px; }

    .hero-eyebrow {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(0,194,45,0.08);
        border: 1px solid rgba(0,194,45,0.25);
        border-radius: 30px; padding: 6px 18px;
        font-family: Inter, sans-serif;
        font-size: 0.68rem; font-weight: 700;
        letter-spacing: 0.2em; text-transform: uppercase;
        color: #00C22D; margin-bottom: 28px;
    }
    .hero-eyebrow-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: #00C22D; box-shadow: 0 0 8px #00C22D;
        animation: glowPulse 2s ease-in-out infinite;
    }
    @keyframes glowPulse {
        0%,100% { box-shadow: 0 0 6px #00C22D; }
        50%      { box-shadow: 0 0 16px #00C22D, 0 0 30px rgba(0,194,45,0.4); }
    }

    .hero-title {
        font-family: Inter, sans-serif;
        font-size: clamp(2.8rem, 7vw, 5.5rem);
        font-weight: 900; line-height: 1.05;
        letter-spacing: -0.03em;
        color: #FFFFFF; margin-bottom: 10px;
    }
    .hero-title-green {
        color: transparent;
        background: linear-gradient(135deg, #00C22D 0%, #22D3EE 100%);
        -webkit-background-clip: text; background-clip: text;
        filter: drop-shadow(0 0 24px rgba(0,194,45,0.5));
    }
    .hero-subtitle {
        font-family: Inter, sans-serif;
        font-size: clamp(1rem, 2.5vw, 1.3rem);
        font-weight: 300; color: rgba(200,214,229,0.7);
        line-height: 1.7; max-width: 600px; margin: 0 auto 40px;
    }

    .neon-divider {
        width: 100%; height: 1px; border: none;
        background: linear-gradient(90deg, transparent, rgba(0,194,45,0.6), rgba(34,211,238,0.4), rgba(0,194,45,0.6), transparent);
        box-shadow: 0 0 12px rgba(0,194,45,0.3);
        margin: 60px 0;
    }

    .section { padding: 60px 0; position: relative; }
    .section-label {
        font-family: Inter, sans-serif;
        font-size: 0.60rem; font-weight: 700;
        letter-spacing: 0.22em; text-transform: uppercase;
        color: rgba(0,194,45,0.5); margin-bottom: 12px;
        display: flex; align-items: center; gap: 10px;
    }
    .section-label::after {
        content: ''; flex: 1; height: 1px;
        background: linear-gradient(90deg, rgba(0,194,45,0.3), transparent);
    }
    .section-title {
        font-family: Inter, sans-serif;
        font-size: clamp(1.6rem, 4vw, 2.6rem);
        font-weight: 800; color: #FFFFFF;
        letter-spacing: -0.02em; line-height: 1.2;
        margin-bottom: 16px;
    }
    .section-desc {
        font-family: Inter, sans-serif;
        font-size: 0.95rem; font-weight: 400;
        color: rgba(200,214,229,0.6); line-height: 1.8;
        max-width: 560px;
    }

    .values-grid {
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 20px; margin-top: 40px;
    }
    .value-card {
        background: linear-gradient(135deg, #0D1825 0%, #0A1420 100%);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px; padding: 32px 26px;
        position: relative; overflow: hidden;
        transition: border-color 0.3s, transform 0.3s;
    }
    .value-card::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, #00C22D, transparent);
        opacity: 0; transition: opacity 0.3s;
    }
    .value-card:hover { border-color: rgba(0,194,45,0.25); transform: translateY(-4px); }
    .value-card:hover::before { opacity: 0.8; }
    .value-icon {
        font-size: 1.6rem; margin-bottom: 16px; display: block;
        filter: drop-shadow(0 0 8px rgba(0,194,45,0.4));
    }
    .value-title {
        font-family: Inter, sans-serif; font-size: 0.85rem;
        font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: #00C22D; margin-bottom: 10px;
    }
    .value-desc {
        font-family: Inter, sans-serif; font-size: 0.83rem;
        color: rgba(200,214,229,0.55); line-height: 1.7;
    }

    .stats-row {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 2px; border-radius: 20px; overflow: hidden;
        border: 1px solid rgba(0,194,45,0.1);
        margin-top: 50px;
    }
    .stat-item {
        background: linear-gradient(135deg, #0D1825 0%, #0A1420 100%);
        padding: 36px 24px; text-align: center;
        border-right: 1px solid rgba(0,194,45,0.06);
        position: relative;
    }
    .stat-item:last-child { border-right: none; }
    .stat-item::after {
        content: ''; position: absolute; bottom: 0; left: 20%; right: 20%; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0,194,45,0.2), transparent);
    }
    .stat-number {
        font-family: Inter, sans-serif;
        font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 900;
        letter-spacing: -0.03em; line-height: 1;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #FFFFFF 0%, #C8D6E5 100%);
        -webkit-background-clip: text; background-clip: text;
        color: transparent;
    }
    .stat-number span { color: #00C22D; -webkit-text-fill-color: #00C22D; }
    .stat-label {
        font-family: Inter, sans-serif; font-size: 0.65rem;
        font-weight: 600; letter-spacing: 0.12em;
        text-transform: uppercase; color: #6B7A8F;
    }

    .team-card {
        background: linear-gradient(135deg, #0D1825 0%, #0A1420 100%);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px; overflow: hidden;
        text-align: center;
        transition: border-color 0.3s, transform 0.3s;
    }
    .team-card:hover { border-color: rgba(0,194,45,0.2); transform: translateY(-4px); }
    .team-info { padding: 18px 14px; }
    .team-name {
        font-family: Inter, sans-serif; font-size: 0.85rem;
        font-weight: 700; color: #FFFFFF; margin-bottom: 4px;
    }
    .team-role {
        font-family: Inter, sans-serif; font-size: 0.68rem;
        font-weight: 500; color: #00C22D; letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .cta-section {
        text-align: center; padding: 80px 20px;
        position: relative; overflow: hidden;
    }
    .cta-bg {
        position: absolute; inset: 0;
        background: radial-gradient(ellipse 70% 80% at 50% 50%, rgba(0,194,45,0.07), transparent 70%);
        pointer-events: none;
    }
    .cta-title {
        font-family: Inter, sans-serif;
        font-size: clamp(1.8rem, 4vw, 3rem);
        font-weight: 900; color: #FFFFFF;
        letter-spacing: -0.02em; margin-bottom: 16px;
    }
    .cta-sub {
        font-family: Inter, sans-serif;
        font-size: 0.95rem; color: rgba(200,214,229,0.6);
        margin-bottom: 36px;
    }
    .cta-btn {
        display: inline-flex; align-items: center; gap: 10px;
        background: linear-gradient(135deg, #00C22D, #00A826);
        color: #000; font-family: Inter, sans-serif;
        font-size: 0.85rem; font-weight: 700;
        letter-spacing: 0.06em; text-transform: uppercase;
        padding: 14px 32px; border-radius: 50px;
        text-decoration: none;
        box-shadow: 0 0 30px rgba(0,194,45,0.35), 0 4px 20px rgba(0,0,0,0.4);
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .cta-btn:hover {
        box-shadow: 0 0 50px rgba(0,194,45,0.55), 0 6px 28px rgba(0,0,0,0.5);
        transform: translateY(-2px);
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(0,194,45,0.3); border-radius: 4px; }
    </style>

    <div class="particles" id="particles"></div>
    <script>
    (function() {
        const c = document.getElementById('particles');
        if (!c) return;
        for (let i = 0; i < 18; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            const s = Math.random() * 6 + 3;
            p.style.cssText = `
                width:${s}px; height:${s}px;
                left:${Math.random()*100}%;
                animation-duration:${Math.random()*14+10}s;
                animation-delay:${Math.random()*12}s;
            `;
            c.appendChild(p);
        }
    })();
    </script>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # HERO
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="hero">
        <div class="hero-bg"></div>
        <div class="hero-grid"></div>
        <div class="hero-content">
            <div class="hero-eyebrow">
                <span class="hero-eyebrow-dot"></span>
                Logística de Alta Performance
            </div>
            <h1 class="hero-title">
                Movendo o futuro<br>
                <span class="hero-title-green">com inteligência</span>
            </h1>
            <p class="hero-subtitle">
                Soluções integradas em armazenagem, distribuição e controle logístico —
                entregando eficiência onde cada detalhe importa.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.image("imagens/cdexterno.jpeg", use_container_width=True)

    # ══════════════════════════════════════════
    # NÚMEROS
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="section">
        <div class="section-label">Nossos Números</div>
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-number">27<span>+</span></div>
                <div class="stat-label">Anos de mercado</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">2<span></span></div>
                <div class="stat-label">Centros de distribuição</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">500<span>K</span></div>
                <div class="stat-label">Pedidos processados/ano</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">99<span>%</span></div>
                <div class="stat-label">Acuracidade de estoque</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="neon-divider">', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SOBRE — texto + imagem lado a lado
    # ══════════════════════════════════════════
    col_txt, col_img = st.columns([1, 1], gap="large")

    with col_txt:
        st.markdown("""
        <div class="section-label">Quem Somos</div>
        <h2 class="section-title">Uma empresa construída para a excelência operacional</h2>
        <p class="section-desc">
            A SALOG nasceu da convicção de que logística vai além de movimentar produtos —
            é sobre criar conexões confiáveis entre empresas e seus clientes.
            Com tecnologia de ponta e uma equipe dedicada, entregamos soluções que
            transformam complexidade em eficiência.
        </p>
        <p class="section-desc" style="margin-top:16px;">
            Nossa plataforma de controle em tempo real garante visibilidade total
            da operação, do recebimento à expedição, com dados precisos para
            decisões mais inteligentes.
        </p>
        """, unsafe_allow_html=True)

    with col_img:
        st.image("imagens/cdadm.png", use_container_width=True)

    st.markdown('<hr class="neon-divider">', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # MISSÃO / VISÃO / VALORES
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="section">
        <div class="section-label">Missão • Visão • Valores</div>
        <div class="values-grid">
            <div class="value-card">
                <span class="value-icon">🎯</span>
                <div class="value-title">Missão</div>
                <p class="value-desc">
                    Oferecer soluções logísticas ágeis, precisas e tecnológicas,
                    gerando valor para nossos clientes e parceiros com excelência
                    em cada etapa da cadeia de suprimentos.
                </p>
            </div>
            <div class="value-card">
                <span class="value-icon">🔭</span>
                <div class="value-title">Visão</div>
                <p class="value-desc">
                    Ser referência nacional em operações logísticas inteligentes,
                    reconhecidos pela inovação, confiabilidade e pelo impacto
                    positivo que geramos em cada parceria.
                </p>
            </div>
            <div class="value-card">
                <span class="value-icon">💎</span>
                <div class="value-title">Valores</div>
                <p class="value-desc">
                    Transparência · Comprometimento · Inovação contínua ·
                    Foco no cliente · Responsabilidade e respeito com pessoas
                    e o meio ambiente.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="neon-divider">', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # GALERIA DE IMAGENS
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="section">
        <div class="section-label">Nossa Operação</div>
        <h2 class="section-title">Veja de perto o que fazemos</h2>
    </div>
    """, unsafe_allow_html=True)

    g1, g2, g3 = st.columns([2, 1, 1], gap="small")

    with g1:
        # ▼▼▼ IMAGEM GRANDE DA GALERIA ▼▼▼
        st.image("imagens/cdinterno1.png", use_container_width=True)

    with g2:
        # ▼▼▼ IMAGEM GALERIA 2 ▼▼▼
        st.image("imagens/cdinterno3.png", use_container_width=True)
        # ▼▼▼ IMAGEM GALERIA 3 ▼▼▼
        st.image("imagens/cdinterno4.png", use_container_width=True)

    with g3:
        # ▼▼▼ IMAGEM GALERIA 4 — substitua pelo nome do arquivo ▼▼▼
       
        st.image("imagens/cdinterno5.png", use_container_width=True)

        # ▼▼▼ IMAGEM GALERIA 5 — substitua pelo nome do arquivo ▼▼▼
        
        st.image("imagens/cdinterno6.png", use_container_width=True)

    
    # ══════════════════════════════════════════
    # EQUIPE
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="section">
        <div class="section-label">Time</div>
        <h2 class="section-title">As pessoas por trás da operação</h2>
    </div>
    """, unsafe_allow_html=True)

    team = [
        ("Murilo", "Diretor de Operações",  "👤", "t1"),
        ("Evandro", "Gerente de Logística",  "👤", "t2"),
        ("Ugo", "Analista de TI",        "👤", "t3"),
        ("Winigles", "Supervisor de CD",     "👤", "t4"),
    ]

    cols = st.columns(4, gap="medium")
    for i, (nome, cargo, icon, key) in enumerate(team):
        with cols[i]:
            st.markdown(f"""
            <div class="team-card">
                <div style="width:100%;aspect-ratio:1;display:flex;align-items:center;
                    justify-content:center;background:linear-gradient(135deg,#0A1820,#0D2218);
                    font-size:3rem;">
                    {icon}
                </div>
                <div class="team-info">
                    <div class="team-name">{nome}</div>
                    <div class="team-role">{cargo}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # st.image(f"imagens/team_{key}.jpg", use_container_width=True)

    st.markdown('<hr class="neon-divider">', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # CTA FINAL
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="cta-section">
        <div class="cta-bg"></div>
        <h2 class="cta-title">Pronto para elevar<br>sua operação logística?</h2>
        <p class="cta-sub">Entre em contato e descubra como a SALOG pode transformar sua cadeia de suprimentos.</p>
        <a class="cta-btn" href="mailto:contato@salog.com.br">
            ✉ Falar com a SALOG
        </a>
    </div>
    """, unsafe_allow_html=True)