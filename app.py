import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Mário Móveis - Gestão",
    page_icon="🪑",
    layout="centered"
)

# Estilização Visual (CSS Customizado para deixar com cara de marca grande)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stTextInput input {
        background-color: #1a1c23;
        color: #ffffff;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    .stButton button {
        background-color: #2ea043;
        color: white;
        border-radius: 8px;
        width: 100%;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton button:hover {
        background-color: #238636;
        color: white;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Estado de Autenticação
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# Tela de Login
if not st.session_state.autenticado:
    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # LOGO NA TELA DE LOGIN (Substitua o st.image pelo arquivo da logo do Mário se tiver,
    # ou deixamos o destaque visual da marca)
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Se você tiver a imagem da logo salva no projeto (ex: 'logo_mario.png'),
        # basta descomentar a linha abaixo:
        # st.image("logo_mario.png", use_column_width=True)

        # Por enquanto, usamos um banner de destaque profissional para fixar na mente:
        st.markdown("<h1 style='text-align: center; color: #2ea043;'>MÁRIO MÓVEIS</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align: center; color: #8b949e; font-size: 14px;'>EXCELÊNCIA EM MÓVEIS PLANEJADOS</p>",
            unsafe_allow_html=True)

    st.markdown("## 🔒 Acesso Restrito")
    st.markdown("Insira suas credenciais para acessar o sistema de gestão.")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Entrar no Sistema"):
        if usuario == "admin" and senha == "1234":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# Tela Principal do Sistema (Após Login)
else:
    # ---------------------------------------------------------
    # LOGO DENTRO DO APLICATIVO (Fixando a marca na cabeça do cliente)
    # ---------------------------------------------------------
    st.markdown("<h2 style='color: #2ea043;'>MÁRIO MÓVEIS — Painel de Gestão</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e;'>Controle total de estoque e móveis sob medida.</p>", unsafe_allow_html=True)
    st.success("Sessão ativa com segurança.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        codigo = st.text_input("Código do Móvel", value="MOV-001")
        nome = st.text_input("Nome do Móvel (ex: Armário Planejado, Mesa de Jantar)")
        tipo = st.selectbox("Tipo de Móvel", ["Móvel Sob Medida", "Móvel Pronta Entrega"])

    with col2:
        preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, value=0.0, format="%.2f")
        preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, value=0.0, format="%.2f")
        quantidade = st.number_input("Quantidade em Estoque", min_value=0, value=1)

    if st.button("➕ Salvar Móvel no Estoque"):
        st.info("Funcionalidade de salvamento pronta para integração!")

    st.markdown("---")
    st.subheader("📋 Estoque Atual")
    st.info("Nenhum móvel cadastrado até o momento.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sair / Encerrar Sessão"):
        st.session_state.autenticado = False
        st.rerun()


















