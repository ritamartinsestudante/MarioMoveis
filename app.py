import os
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# Criar pasta para salvar as fotos se ela não existir
PASTA_IMAGENS = "imagens"
if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)


# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def conectar_bd():
    conn = sqlite3.connect("mario_moveis.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            estado TEXT,
            preco_compra REAL,
            preco_venda REAL,
            status TEXT DEFAULT 'Disponivel',
            data_entrada TEXT,
            foto_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movel_id INTEGER,
            valor_venda REAL,
            forma_pagamento TEXT,
            data_venda TEXT,
            FOREIGN KEY (movel_id) REFERENCES moveis (id)
        )
    """)
    conn.commit()

    try:
        cursor.execute("ALTER TABLE moveis ADD COLUMN foto_path TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    conn.close()


conectar_bd()

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL (CSS) ---
st.set_page_config(
    page_title="Mário Móveis - Gestão de Estoque",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização em CSS para fontes, botões, bordas e sombras
st.markdown(
    """
    <style>
    /* Importação da fonte moderna 'Inter' */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Cabeçalho principal */
    .main-title {
        color: #1E293B;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }

    .sub-title {
        color: #64748B;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }

    /* Cartões dos móveis no estoque */
    .movel-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 15px;
        transition: all 0.2s ease-in-out;
    }

    .movel-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        border-color: #CBD5E1;
    }

    /* Badges / Etiquetas de Status */
    .badge-disponivel {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .badge-vendido {
        background-color: #F1F5F9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* Botão Principal Estilizado */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    /* Estilização da barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Topo do Sistema
st.markdown("<h1 class='main-title'>🪑 Mário Móveis</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Sistema de Gestão de Estoque & Controle Financeiro</p>", unsafe_allow_html=True)

# Menu Lateral
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2400/2400629.png", width=80)
st.sidebar.title("Menu Principal")
opcao = st.sidebar.radio(
    "Ir para:",
    [
        "📦 Cadastrar Móvel",
        "🛋️ Estoque / Cadastrados",
        "💰 Registrar Venda",
        "📊 Relatório de Lucro",
    ],
)

# --- 1. CADASTRO DE MÓVEIS ---
if opcao == "📦 Cadastrar Móvel":
    st.subheader("📦 Cadastrar Novo Móvel")

    with st.form("form_cadastro"):
        nome = st.text_input("Nome do Móvel / Descrição", placeholder="Ex: Sofá retrátil 3 lugares marrom")

        col1, col2 = st.columns(2)
        with col1:
            categoria = st.selectbox("Categoria", ["Sala", "Quarto", "Cozinha", "Escritório", "Outros"])
            preco_compra = st.number_input("Preço de Compra (Custo R$)", min_value=0.0, format="%.2f")
        with col2:
            estado = st.selectbox("Estado de Conservação",
                                  ["Excelente", "Bom (Pequenos detalhes)", "Precisa de Reforma"])
            preco_venda = st.number_input("Preço de Venda Sugerido (R$)", min_value=0.0, format="%.2f")

        foto = st.file_uploader("Foto do Móvel (JPG, PNG ou JPEG)", type=["jpg", "jpeg", "png"])

        btn_cadastrar = st.form_submit_button("✨ Salvar Móvel no Estoque", type="primary")

        if btn_cadastrar:
            if nome:
                caminho_foto = ""
                if foto is not None:
                    nome_arquivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.name}"
                    caminho_foto = os.path.join(PASTA_IMAGENS, nome_arquivo)
                    with open(caminho_foto, "wb") as f:
                        f.write(foto.getbuffer())

                conn = sqlite3.connect("mario_moveis.db")
                cursor = conn.cursor()
                data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute(
                    """
                    INSERT INTO moveis (nome, categoria, estado, preco_compra, preco_venda, data_entrada, foto_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (nome, categoria, estado, preco_compra, preco_venda, data_hoje, caminho_foto),
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Móvel **'{nome}'** cadastrado com sucesso no estoque!")
            else:
                st.error("⚠️ Por favor, preencha a descrição do móvel.")

# --- 2. VER ESTOQUE ---
elif opcao == "🛋️ Estoque / Cadastrados":
    st.subheader("🛋️ Consultar Estoque")

    filtro_status = st.radio("Filtrar por Status:", ["Apenas Disponíveis", "Vendidos", "Todos"], horizontal=True)

    conn = sqlite3.connect("mario_moveis.db")

    if filtro_status == "Apenas Disponíveis":
        query = "SELECT id, nome, categoria, estado, preco_compra, preco_venda, status, foto_path FROM moveis WHERE status = 'Disponivel'"
    elif filtro_status == "Vendidos":
        query = "SELECT id, nome, categoria, estado, preco_compra, preco_venda, status, foto_path FROM moveis WHERE status = 'Vendido'"
    else:
        query = "SELECT id, nome, categoria, estado, preco_compra, preco_venda, status, foto_path FROM moveis"

    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        for _, row in df.iterrows():
            with st.container():
                col_img, col_info, col_acao = st.columns([1, 2.5, 0.8])

                with col_img:
                    foto_caminho = str(row["foto_path"]) if pd.notna(row["foto_path"]) else ""
                    if foto_caminho and os.path.exists(foto_caminho):
                        st.image(foto_caminho, use_container_width=True)
                    else:
                        st.caption("📷 *Sem imagem cadastrada*")

                with col_info:
                    status_class = "badge-disponivel" if row["status"] == "Disponivel" else "badge-vendido"
                    status_label = "Disponível" if row["status"] == "Disponivel" else "Vendido"

                    st.markdown(
                        f"### #{row['id']} - {row['nome']} <span class='{status_class}'>{status_label}</span>",
                        unsafe_allow_html=True,
                    )
                    st.write(f"**Categoria:** {row['categoria']} | **Estado:** {row['estado']}")
                    st.write(
                        f"💳 **Custo:** R$ {row['preco_compra']:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ **Sugerido:** R$ {row['preco_venda']:.2f}"
                    )

                with col_acao:
                    if st.button("🗑️ Excluir", key=f"del_{row['id']}"):
                        conn = sqlite3.connect("mario_moveis.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM vendas WHERE movel_id = ?", (row["id"],))
                        cursor.execute("DELETE FROM moveis WHERE id = ?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.success("Móvel removido!")
                        st.rerun()

                st.divider()
    else:
        st.info("Nenhum móvel encontrado com o filtro selecionado.")

# --- 3. REGISTRAR VENDA ---
elif opcao == "💰 Registrar Venda":
    st.subheader("💰 Registrar Nova Venda")

    conn = sqlite3.connect("mario_moveis.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco_venda FROM moveis WHERE status = 'Disponivel'")
    moveis_disponiveis = cursor.fetchall()

    if moveis_disponiveis:
        opcoes_moveis = {f"ID {m[0]} - {m[1]} (Sugerido: R$ {m[2]:.2f})": m[0] for m in moveis_disponiveis}
        escolha = st.selectbox("Selecione o móvel vendido:", list(opcoes_moveis.keys()))

        col1, col2 = st.columns(2)
        with col1:
            valor_final = st.number_input("Valor Final Fechado na Venda (R$)", min_value=0.0, format="%.2f")
        with col2:
            forma_pag = st.selectbox("Forma de Pagamento", ["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"])

        if st.button("🎉 Confirmar e Baixar do Estoque", type="primary"):
            movel_id = opcoes_moveis[escolha]
            data_venda = datetime.now().strftime("%Y-%m-%d %H:%M")

            cursor.execute(
                """
                INSERT INTO vendas (movel_id, valor_venda, forma_pagamento, data_venda)
                VALUES (?, ?, ?, ?)
            """,
                (movel_id, valor_final, forma_pag, data_venda),
            )

            cursor.execute("UPDATE moveis SET status = 'Vendido' WHERE id = ?", (movel_id,))

            conn.commit()
            conn.close()
            st.success("🎉 Venda registrada com sucesso! Estoque atualizado.")
            st.rerun()
    else:
        st.warning("Não há móveis disponíveis no estoque no momento.")
        conn.close()

# --- 4. RELATÓRIO DE LUCRO ---
elif opcao == "📊 Relatório de Lucro":
    st.subheader("📊 Resumo Financeiro e Lucratividade")

    conn = sqlite3.connect("mario_moveis.db")
    query = """
        SELECT 
            m.id AS 'ID', 
            m.nome AS 'Móvel', 
            m.preco_compra AS 'Custo (R$)', 
            v.valor_venda AS 'Venda (R$)', 
            (v.valor_venda - m.preco_compra) AS 'Lucro (R$)',
            v.forma_pagamento AS 'Forma Pagto',
            v.data_venda AS 'Data Venda'
        FROM vendas v
        JOIN moveis m ON v.movel_id = m.id
    """
    df_vendas = pd.read_sql_query(query, conn)
    conn.close()

    if not df_vendas.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Peças Vendidas", len(df_vendas))
        col2.metric("💵 Faturamento Total", f"R$ {df_vendas['Venda (R$)'].sum():.2f}")
        col3.metric("📈 Lucro Líquido", f"R$ {df_vendas['Lucro (R$)'].sum():.2f}")

        st.markdown("---")
        st.subheader("Detalhamento de Vendas")
        st.dataframe(df_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda realizada ainda para gerar estatísticas.")




