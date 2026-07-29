import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import os
import sqlite3

# ---------------------------------------------------------
# BANCO DE DADOS PERMANENTE (SQLite)
# ---------------------------------------------------------
NOME_BANCO = "mario_moveis.db"


def conectar_banco():
    return sqlite3.connect(NOME_BANCO)


def inicializar_banco():
    conn = conectar_banco()
    cursor = conn.cursor()

    # Tabela de Finanças / Caixa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL
        )
    ''')

    # Tabela de Estoque Geral de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto TEXT UNIQUE,
            categoria TEXT,
            estado TEXT DEFAULT 'Móvel Novo ✨',
            quantidade INTEGER,
            preco_unitario REAL
        )
    ''')

    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            cliente TEXT,
            produto TEXT,
            estado_movel TEXT,
            quantidade INTEGER,
            preco_unitario REAL,
            valor_total REAL,
            forma_pagamento TEXT
        )
    ''')

    # Migration simples caso a coluna 'estado' ainda não exista na tabela estoque antiga
    try:
        cursor.execute("ALTER TABLE estoque ADD COLUMN estado TEXT DEFAULT 'Móvel Novo ✨'")
    except sqlite3.OperationalError:
        pass  # A coluna já existe

    conn.commit()
    conn.close()


# --- Funções do Financeiro ---
def salvar_transacao(data, tipo, categoria, descricao, valor):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transacoes (data, tipo, categoria, descricao, valor)
        VALUES (?, ?, ?, ?, ?)
    ''', (data, tipo, categoria, descricao, valor))
    conn.commit()
    conn.close()


def carregar_transacoes():
    conn = conectar_banco()
    df = pd.read_sql_query(
        "SELECT data as Data, tipo as Tipo, categoria as Categoria, descricao as Descrição, valor as [Valor (R$)] FROM transacoes ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


# --- Funções do Estoque ---
def salvar_ou_atualizar_estoque(produto, categoria, estado, qtd, preco):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM estoque WHERE produto = ?", (produto,))
    item = cursor.fetchone()

    if item:
        nova_qtd = item[0] + qtd
        cursor.execute('''
            UPDATE estoque SET quantidade = ?, preco_unitario = ?, categoria = ?, estado = ? WHERE produto = ?
        ''', (nova_qtd, preco, categoria, estado, produto))
    else:
        cursor.execute('''
            INSERT INTO estoque (produto, categoria, estado, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?, ?)
        ''', (produto, categoria, estado, qtd, preco))

    conn.commit()
    conn.close()


def dar_baixa_estoque(produto, qtd_saida):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM estoque WHERE produto = ?", (produto,))
    item = cursor.fetchone()

    if item:
        qtd_atual = item[0]
        if qtd_atual >= qtd_saida:
            nova_qtd = qtd_atual - qtd_saida
            cursor.execute("UPDATE estoque SET quantidade = ? WHERE produto = ?", (nova_qtd, produto))
            conn.commit()
            conn.close()
            return True, f"Baixa de {qtd_saida} unidade(s) de '{produto}' realizada com sucesso!"
        else:
            conn.close()
            return False, f"Estoque insuficiente! Quantidade atual disponível: {qtd_atual}"
    conn.close()
    return False, "Produto não encontrado no estoque."


def carregar_estoque():
    conn = conectar_banco()
    df = pd.read_sql_query(
        "SELECT produto as Produto, categoria as Categoria, estado as [Estado (Novo/Usado)], quantidade as [Qtd em Estoque], preco_unitario as [Preço Unitário (R$)] FROM estoque ORDER BY produto ASC",
        conn
    )
    conn.close()
    return df


# --- Funções de Vendas ---
def registrar_venda(data, cliente, produto, estado_movel, qtd, preco_unit, forma_pagamento):
    valor_total = qtd * preco_unit

    # 1. Dar baixa no estoque
    sucesso_baixa, msg_baixa = dar_baixa_estoque(produto, qtd)
    if not sucesso_baixa:
        return False, msg_baixa

    # 2. Registrar a venda na tabela de vendas
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO vendas (data, cliente, produto, estado_movel, quantidade, preco_unitario, valor_total, forma_pagamento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data, cliente, produto, estado_movel, qtd, preco_unit, valor_total, forma_pagamento))
    conn.commit()
    conn.close()

    # 3. Integrar automaticamente com o Financeiro (Lançar Receita de Venda)
    descricao_fin = f"Venda ({estado_movel}): {produto} x{qtd} - Cliente: {cliente if cliente else 'Não informado'} [{forma_pagamento}]"
    salvar_transacao(
        data=data,
        tipo="Receita",
        categoria="Venda de Produtos",
        descricao=descricao_fin,
        valor=valor_total
    )

    return True, f"Venda de {qtd}x '{produto}' registrada com sucesso! Lançamento financeiro e baixa no estoque realizados automaticamente."


def carregar_vendas():
    conn = conectar_banco()
    df = pd.read_sql_query(
        "SELECT data as Data, cliente as Cliente, produto as Produto, estado_movel as [Novo / Usado], quantidade as Qtd, preco_unitario as [Preço Unit. (R$)], valor_total as [Valor Total (R$)], forma_pagamento as [Forma de Pagamento] FROM vendas ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


# Inicializa o banco de dados
inicializar_banco()

# ---------------------------------------------------------
# CARREGAMENTO SEGURO DA LOGO (PIL / Pillow)
# ---------------------------------------------------------
CAMINHO_LOGO = os.path.join("static", "logo.png")


def exibir_logo():
    if os.path.exists(CAMINHO_LOGO):
        img = Image.open(CAMINHO_LOGO)
        st.image(img, width=180)
    else:
        st.title("🪵 Mário Móveis")


# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mário Móveis - Gestão Comercial",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# AUTENTICAÇÃO E LOGIN
# ---------------------------------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

USUARIO_SISTEMA = "mario"
SENHA_SISTEMA = "mario2026"


def tela_login():
    exibir_logo()
    st.caption("🔒 Painel de Controle e Gestão Comercial")

    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)

        if submit:
            if usuario == USUARIO_SISTEMA and senha == SENHA_SISTEMA:
                st.session_state.logado = True
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")


if not st.session_state.logado:
    tela_login()
    st.stop()

# ---------------------------------------------------------
# PAINEL PRINCIPAL
# ---------------------------------------------------------

with st.sidebar:
    exibir_logo()
    st.write("Painel de Controle")
    st.divider()
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

exibir_logo()

# Navegação por Abas (Nova Aba de Vendas Acrescentada)
aba_vendas, aba_financeiro, aba_estoque = st.tabs([
    "🛒 Central de Vendas",
    "📊 Controle Financeiro e Caixa",
    "📦 Gestão de Estoque e Produtos"
])

# =========================================================
# ABA 1: CENTRAL DE VENDAS
# =========================================================
with aba_vendas:
    st.title("🛒 Registro de Vendas")
    st.subheader("🛍️ Nova Venda")

    df_est_vendas = carregar_estoque()

    if not df_est_vendas.empty:
        # Filtra apenas produtos com estoque disponível > 0 para facilitar a venda
        produtos_disponiveis = df_est_vendas[df_est_vendas["Qtd em Estoque"] > 0]

        if not produtos_disponiveis.empty:
            with st.form("form_venda", clear_on_submit=True):
                col_v1, col_v2 = st.columns(2)

                with col_v1:
                    lista_prod_nomes = produtos_disponiveis["Produto"].tolist()
                    prod_venda = st.selectbox("Selecione o Produto", lista_prod_nomes)

                    # Busca as informações do produto selecionado no DataFrame de estoque
                    item_info = produtos_disponiveis[produtos_disponiveis["Produto"] == prod_venda].iloc[0]
                    estado_sugerido = item_info.get("Estado (Novo/Usado)", "Móvel Novo ✨")
                    preco_sugerido = float(item_info["Preço Unitário (R$)"])
                    qtd_disponivel = int(item_info["Qtd em Estoque"])

                    st.info(
                        f"ℹ️ Estoque disponível: **{qtd_disponivel} un.** | Preço Cadastrado: **R$ {preco_sugerido:,.2f}**")

                    cliente_venda = st.text_input("Nome do Cliente (Opcional)", placeholder="Ex: João da Silva")
                    estado_movel_venda = st.radio("Estado do Móvel", ["Móvel Novo ✨", "Móvel Usado ♻️"],
                                                  index=0 if "Novo" in str(estado_sugerido) else 1)

                with col_v2:
                    qtd_venda = st.number_input("Quantidade Vendida", min_value=1, max_value=max(1, qtd_disponivel),
                                                value=1, step=1)
                    preco_venda = st.number_input("Preço de Venda Unitário (R$)", min_value=0.0, value=preco_sugerido,
                                                  step=50.0, format="%.2f")
                    forma_pagto = st.selectbox("Forma de Pagamento",
                                               ["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro",
                                                "Transferência / TED", "Fiado / Outro"])
                    data_venda = st.date_input("Data da Venda", datetime.now())

                val_total_venda = qtd_venda * preco_venda
                st.markdown(f"### 💰 **Total da Venda: R$ {val_total_venda:,.2f}**")

                btn_finalizar_venda = st.form_submit_button("🛒 Finalizar Venda", use_container_width=True)

                if btn_finalizar_venda:
                    ok, msg = registrar_venda(
                        data=data_venda.strftime("%d/%m/%Y"),
                        cliente=cliente_venda.strip(),
                        produto=prod_venda,
                        estado_movel=estado_movel_venda,
                        qtd=qtd_venda,
                        preco_unit=preco_venda,
                        forma_pagamento=forma_pagto
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.warning(
                "Não há produtos com saldo em estoque no momento para realizar vendas. Cadastre ou adicione saldo na aba de Estoque.")
    else:
        st.info("Nenhum produto cadastrado no estoque. Cadastre produtos no Estoque antes de registrar vendas.")

    st.divider()
    st.subheader("📋 Histórico e Relatório de Vendas")

    df_vendas = carregar_vendas()
    if not df_vendas.empty:
        col_m1, col_m2, col_m3 = st.columns(3)
        total_faturado = df_vendas["Valor Total (R$)"].sum()

        vendas_novos = df_vendas[df_vendas["Novo / Usado"] == "Móvel Novo ✨"]["Valor Total (R$)"].sum()
        vendas_usados = df_vendas[df_vendas["Novo / Usado"] == "Móvel Usado ♻️"]["Valor Total (R$)"].sum()

        col_m1.metric("Total Faturado em Vendas", f"R$ {total_faturado:,.2f}")
        col_m2.metric("Vendas de Móveis Novos", f"R$ {vendas_novos:,.2f}")
        col_m3.metric("Vendas de Móveis Usados", f"R$ {vendas_usados:,.2f}")

        st.dataframe(df_vendas, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada ainda.")

# =========================================================
# ABA 2: CONTROLE FINANCEIRO
# =========================================================
with aba_financeiro:
    st.title("📊 Gestão Financeira e Caixa")
    st.subheader("➕ Novo Lançamento Manual")

    with st.form("form_lancamento", clear_on_submit=True):
        tipo_operacao = st.selectbox("Tipo de Operação", ["Despesa", "Receita"])

        if tipo_operacao == "Despesa":
            lista_categorias = [
                "Transporte / Frete",
                "Combustível / Uber",
                "Matéria-Prima / Insumos",
                "Ferragens / Ferramentas",
                "Aluguel / Oficina",
                "Energia / Água",
                "Salários / Ajudantes",
                "Manutenção",
                "Outras Despesas"
            ]
        else:
            lista_categorias = [
                "Venda de Produtos",
                "Serviços e Manutenção",
                "Entradas de Encomendas (Sinal)",
                "Outras Receitas"
            ]

        categoria_sel = st.selectbox("Categoria", lista_categorias)
        descricao_obs = st.text_input("Descrição", placeholder="Ex: Pagamento de frete / Venda para cliente Maria")
        valor_lancado = st.number_input("Valor (R$)", min_value=0.01, step=50.0, format="%.2f")
        data_reg = st.date_input("Data", datetime.now())

        salvar_fin = st.form_submit_button("💾 Salvar Lançamento", use_container_width=True)

    if salvar_fin:
        salvar_transacao(
            data=data_reg.strftime("%d/%m/%Y"),
            tipo=tipo_operacao,
            categoria=categoria_sel,
            descricao=descricao_obs,
            valor=valor_lancado
        )
        st.success("Lançamento registrado com sucesso!")

    st.divider()
    st.subheader("📈 Resumo Financeiro")

    df_caixa = carregar_transacoes()

    if not df_caixa.empty:
        total_entradas = df_caixa[df_caixa["Tipo"] == "Receita"]["Valor (R$)"].sum()
        total_saidas = df_caixa[df_caixa["Tipo"] == "Despesa"]["Valor (R$)"].sum()
        gastos_transporte = df_caixa[df_caixa["Categoria"].isin(["Transporte / Frete", "Combustível / Uber"])][
            "Valor (R$)"].sum()
        saldo_caixa = total_entradas - total_saidas

        col1, col2 = st.columns(2)
        col1.metric("Total Entradas / Receitas", f"R$ {total_entradas:,.2f}")
        col2.metric("Total Saídas / Despesas", f"R$ {total_saidas:,.2f}")

        col3, col4 = st.columns(2)
        col3.metric("Custos c/ Transporte", f"R$ {gastos_transporte:,.2f}")
        col4.metric("Saldo Em Caixa", f"R$ {saldo_caixa:,.2f}")

        st.write("---")
        st.subheader("📋 Histórico de Lançamentos")
        st.dataframe(df_caixa, use_container_width=True)
    else:
        st.info("Nenhum lançamento registrado no momento.")

# =========================================================
# ABA 3: GESTÃO DE ESTOQUE DE PRODUTOS
# =========================================================
with aba_estoque:
    st.title("📦 Controle de Estoque de Produtos e Insumos")

    col_add, col_baixa = st.columns(2)

    # Formulário para Cadastro / Entrada de Produtos
    with col_add:
        st.subheader("➕ Entrada de Produto / Material")
        with st.form("form_add_estoque", clear_on_submit=True):
            nome_produto = st.text_input("Nome do Produto / Material",
                                         placeholder="Ex: Chapa MDF 18mm / Sofá 3 Lugares / Cadeira")
            cat_produto = st.selectbox("Categoria", ["Produto Acabado", "Matéria-Prima", "Ferragem / Acessório",
                                                     "Insumo / Ferramenta", "Outro"])
            estado_produto = st.selectbox("Estado do Móvel / Item",
                                          ["Móvel Novo ✨", "Móvel Usado ♻️", "Não aplicável (Insumo/Ferramenta)"])
            qtd_produto = st.number_input("Quantidade a Adicionar", min_value=1, step=1, value=1)
            preco_unit = st.number_input("Preço / Custo Unitário (R$)", min_value=0.0, step=50.0, format="%.2f")

            btn_add_est = st.form_submit_button("📥 Adicionar ao Estoque", use_container_width=True)

            if btn_add_est:
                if nome_produto.strip() != "":
                    salvar_ou_atualizar_estoque(nome_produto.strip(), cat_produto, estado_produto, qtd_produto,
                                                preco_unit)
                    st.success(f"Estoque de '{nome_produto}' atualizado!")
                    st.rerun()
                else:
                    st.warning("Por favor, digite o nome do produto.")

    # Formulário para Dar Baixa no Estoque (Manual / Avaria)
    with col_baixa:
        st.subheader("➖ Saída / Baixa do Estoque (Uso interno/Avaria)")
        df_est_atual = carregar_estoque()

        if not df_est_atual.empty:
            lista_produtos = df_est_atual["Produto"].tolist()
            with st.form("form_baixa_estoque", clear_on_submit=True):
                prod_selecionado = st.selectbox("Selecione o Item", lista_produtos)
                qtd_baixa = st.number_input("Quantidade a Retirar", min_value=1, step=1, value=1)

                btn_baixa = st.form_submit_button("📤 Confirmar Saída Manual", use_container_width=True)

                if btn_baixa:
                    sucesso, msg = dar_baixa_estoque(prod_selecionado, qtd_baixa)
                    if sucesso:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("Cadastre produtos no formulário ao lado para liberar a baixa.")

    st.divider()
    st.subheader("📋 Relatório do Estoque Atual")

    df_estoque = carregar_estoque()
    if not df_estoque.empty:
        df_estoque["Valor Total Estimado (R$)"] = df_estoque["Qtd em Estoque"] * df_estoque["Preço Unitário (R$)"]

        m1, m2 = st.columns(2)
        m1.metric("Variedade de Itens Cadastrados", len(df_estoque))
        m2.metric("Valor Total Parado em Estoque", f"R$ {df_estoque['Valor Total Estimado (R$)'].sum():,.2f}")

        st.dataframe(df_estoque, use_container_width=True)
    else:
        st.info("Nenhum item cadastrado no estoque no momento.")
        


        






