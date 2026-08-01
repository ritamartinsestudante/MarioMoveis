from datetime import datetime
import os
import sqlite3
from PIL import Image
import pandas as pd
import streamlit as st

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
            preco_custo REAL DEFAULT 0.0,
            preco_unitario REAL DEFAULT 0.0
        )
    ''')

    # Tabela de Vendas (com custo unitário, frete e lucro líquido)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            cliente TEXT,
            produto TEXT,
            estado_movel TEXT,
            quantidade INTEGER,
            preco_custo REAL DEFAULT 0.0,
            preco_unitario REAL DEFAULT 0.0,
            custo_frete REAL DEFAULT 0.0,
            valor_total REAL DEFAULT 0.0,
            lucro_total REAL DEFAULT 0.0,
            forma_pagamento TEXT
        )
    ''')

    # Migrations para garantir compatibilidade com bases antigas
    try:
        cursor.execute("ALTER TABLE estoque ADD COLUMN estado TEXT DEFAULT 'Móvel Novo ✨'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE estoque ADD COLUMN preco_custo REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN preco_custo REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN custo_frete REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE vendas ADD COLUMN lucro_total REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

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
        "SELECT id, data as Data, tipo as Tipo, categoria as Categoria, descricao as Descrição, valor as [Valor (R$)] FROM transacoes ORDER BY id DESC",
        conn)
    conn.close()
    return df


def deletar_transacao(transacao_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()


def limpar_todas_transacoes():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes")
    conn.commit()
    conn.close()


# --- Funções do Estoque ---
def salvar_ou_atualizar_estoque(produto, categoria, estado, qtd, preco_custo, preco_venda, registrar_como_despesa=False):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, preco_custo, preco_unitario FROM estoque WHERE produto = ?", (produto,))
    item = cursor.fetchone()

    if item:
        nova_qtd = item[0] + qtd
        cursor.execute('''
            UPDATE estoque SET quantidade = ?, preco_custo = ?, preco_unitario = ?, categoria = ?, estado = ? WHERE produto = ?
        ''', (nova_qtd, preco_custo, preco_venda, categoria, estado, produto))
    else:
        cursor.execute('''
            INSERT INTO estoque (produto, categoria, estado, quantidade, preco_custo, preco_unitario)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (produto, categoria, estado, qtd, preco_custo, preco_venda))

    conn.commit()
    conn.close()

    if registrar_como_despesa and preco_custo > 0:
        total_gasto = preco_custo * qtd
        data_hj = datetime.now().strftime("%d/%m/%Y")
        salvar_transacao(
            data=data_hj,
            tipo="Despesa",
            categoria="Compra de Mercadoria / Matéria-Prima",
            descricao=f"Aquisição de estoque: {produto} x{qtd} (Custo un.: R$ {preco_custo:,.2f})",
            valor=total_gasto
        )


def dar_baixa_estoque(produto, qtd_saida):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, preco_custo, preco_unitario FROM estoque WHERE produto = ?", (produto,))
    item = cursor.fetchone()

    if item:
        qtd_atual = item[0]
        custo_unit = item[1]
        if qtd_atual >= qtd_saida:
            nova_qtd = qtd_atual - qtd_saida
            cursor.execute("UPDATE estoque SET quantidade = ? WHERE produto = ?", (nova_qtd, produto))
            conn.commit()
            conn.close()
            return True, f"Baixa de {qtd_saida} unidade(s) de '{produto}' realizada com sucesso!", custo_unit
        else:
            conn.close()
            return False, f"Estoque insuficiente! Quantidade atual disponível: {qtd_atual}", 0.0
    conn.close()
    return False, "Produto não encontrado no estoque.", 0.0


def deletar_item_estoque(produto_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estoque WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


def limpar_todo_estoque():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estoque")
    conn.commit()
    conn.close()


def carregar_estoque():
    conn = conectar_banco()
    df = pd.read_sql_query(
        "SELECT id, produto as Produto, categoria as Categoria, estado as [Estado (Novo/Usado)], quantidade as [Qtd em Estoque], preco_custo as [Preço Custo (R$)], preco_unitario as [Preço Venda (R$)] FROM estoque ORDER BY produto ASC",
        conn)
    conn.close()
    return df


# --- Funções de Vendas ---
def registrar_venda(data, cliente, produto, estado_movel, qtd, preco_venda, custo_frete, forma_pagamento):
    valor_total = qtd * preco_venda

    # 1. Dar baixa automática no estoque e recuperar o custo unitário cadastrado
    sucesso_baixa, msg_baixa, custo_unit = dar_baixa_estoque(produto, qtd)
    if not sucesso_baixa:
        return False, msg_baixa

    custo_total = qtd * custo_unit
    # Lucro Líquido = (Valor Total Venda) - (Custo Total das Peças) - (Custo do Frete / Entrega)
    lucro_total = valor_total - custo_total - custo_frete

    # 2. Registrar a venda na tabela de vendas
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO vendas (data, cliente, produto, estado_movel, quantidade, preco_custo, preco_unitario, custo_frete, valor_total, lucro_total, forma_pagamento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data, cliente if cliente else "Cliente Balcão", produto, estado_movel, qtd, custo_unit, preco_venda, custo_frete,
          valor_total, lucro_total, forma_pagamento))
    conn.commit()
    conn.close()

    # 3. Integrar automaticamente com o Financeiro (Receita da Venda)
    descricao_fin = f"Venda ({estado_movel}): {produto} x{qtd} - Cliente: {cliente if cliente else 'Balcão'} [{forma_pagamento}] | Lucro Líq: R$ {lucro_total:,.2f}"
    salvar_transacao(
        data=data,
        tipo="Receita",
        categoria="Venda de Produtos",
        descricao=descricao_fin,
        valor=valor_total
    )

    # 4. Se houve custo de frete/entrega associado à venda, registrar também como despesa de frete no caixa
    if custo_frete > 0:
        salvar_transacao(
            data=data,
            tipo="Despesa",
            categoria="Transporte / Frete / Combustível",
            descricao=f"Frete / Entrega ref. Venda: {produto} (Cliente: {cliente if cliente else 'Balcão'})",
            valor=custo_frete
        )

    return True, f"Venda registrada com sucesso! Faturamento: R$ {valor_total:,.2f} | Custo Mercadoria: R$ {custo_total:,.2f} | Frete: R$ {custo_frete:,.2f} | Lucro Líquido: R$ {lucro_total:,.2f}."


def carregar_vendas():
    conn = conectar_banco()
    df = pd.read_sql_query(
        "SELECT id, data as Data, cliente as Cliente, produto as Produto, estado_movel as [Novo / Usado], quantidade as Qtd, preco_custo as [Custo Unit. (R$)], preco_unitario as [Preço Venda (R$)], custo_frete as [Frete (R$)], valor_total as [Valor Total (R$)], lucro_total as [Lucro Líquido (R$)], forma_pagamento as [Forma de Pagamento] FROM vendas ORDER BY id DESC",
        conn)
    conn.close()
    return df


def deletar_venda(venda_id):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
    conn.commit()
    conn.close()


def limpar_todas_vendas():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas")
    conn.commit()
    conn.close()


# Inicializa o banco de dados
inicializar_banco()

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


def exibir_logo():
    st.subheader("🪵 Mário Móveis - Gestão Comercial e de Estoque")


def tela_login():
    exibir_logo()
    st.caption("🔒 Painel de Controle Exclusivo")

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

# Navegação por Abas
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
    st.subheader("🛍️ Nova Venda (Baixa Automática do Estoque)")

    df_est_vendas = carregar_estoque()

    if not df_est_vendas.empty:
        produtos_disponiveis = df_est_vendas[df_est_vendas["Qtd em Estoque"] > 0]

        if not produtos_disponiveis.empty:
            with st.form("form_venda", clear_on_submit=True):
                col_v1, col_v2 = st.columns(2)

                with col_v1:
                    lista_prod_nomes = produtos_disponiveis["Produto"].tolist()
                    prod_venda = st.selectbox("Selecione o Produto em Estoque", lista_prod_nomes)

                    item_info = produtos_disponiveis[produtos_disponiveis["Produto"] == prod_venda].iloc[0]
                    estado_sugerido = item_info.get("Estado (Novo/Usado)", "Móvel Novo ✨")
                    custo_sugerido = float(item_info["Preço Custo (R$)"])
                    preco_sugerido = float(item_info["Preço Venda (R$)"])
                    qtd_disponivel = int(item_info["Qtd em Estoque"])

                    st.info(
                        f"ℹ️ Estoque Disponível: **{qtd_disponivel} un.** | Custo Cadastrado: **R$ {custo_sugerido:,.2f}** | Preço Venda Sugerido: **R$ {preco_sugerido:,.2f}**")

                    cliente_venda = st.text_input("Nome do Cliente", placeholder="Ex: João da Silva")
                    estado_movel_venda = st.radio("Estado do Móvel", ["Móvel Novo ✨", "Móvel Usado ♻️"],
                                                  index=0 if "Novo" in str(estado_sugerido) else 1)

                with col_v2:
                    qtd_venda = st.number_input("Quantidade Vendida", min_value=1, max_value=max(1, qtd_disponivel), value=1, step=1)
                    preco_venda = st.number_input("Preço de Venda Unitário (R$)", min_value=0.0, value=preco_sugerido, step=10.0, format="%.2f")
                    custo_frete_venda = st.number_input("Custo de Transporte / Frete para Entrega (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f", help="Quanto gastou de combustível ou frete para entregar este móvel ao cliente.")
                    forma_pagto = st.selectbox("Forma de Pagamento", ["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Transferência / TED", "Fiado / Outro"])
                    data_venda = st.date_input("Data da Venda", datetime.now())

                val_total_venda = qtd_venda * preco_venda
                custo_total_venda = qtd_venda * custo_sugerido
                lucro_liquido = val_total_venda - custo_total_venda - custo_frete_venda

                st.markdown(
                    f"### 💰 **Faturamento: R$ {val_total_venda:,.2f}** | 📦 **Custo Peças: R$ {custo_total_venda:,.2f}** | 🚚 **Frete: R$ {custo_frete_venda:,.2f}** | ✨ **Lucro Líquido: R$ {lucro_liquido:,.2f}**")

                btn_finalizar_venda = st.form_submit_button("🛒 Finalizar Venda e Dar Baixa Automática", use_container_width=True)

                if btn_finalizar_venda:
                    ok, msg = registrar_venda(
                        data=data_venda.strftime("%d/%m/%Y"),
                        cliente=cliente_venda.strip(),
                        produto=prod_venda,
                        estado_movel=estado_movel_venda,
                        qtd=qtd_venda,
                        preco_venda=preco_venda,
                        custo_frete=custo_frete_venda,
                        forma_pagamento=forma_pagto
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.warning("Não há produtos com saldo em estoque no momento para realizar vendas.")
    else:
        st.info("Nenhum produto cadastrado no estoque no momento.")

    st.divider()
    st.subheader("📋 Histórico e Relatório Detalhado de Vendas")

    df_vendas = carregar_vendas()
    if not df_vendas.empty:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        total_faturado = df_vendas["Valor Total (R$)"].sum()
        total_lucro = df_vendas["Lucro Líquido (R$)"].sum()
        vendas_novos = df_vendas[df_vendas["Novo / Usado"] == "Móvel Novo ✨"]["Valor Total (R$)"].sum()
        vendas_usados = df_vendas[df_vendas["Novo / Usado"] == "Móvel Usado ♻️"]["Valor Total (R$)"].sum()

        col_m1.metric("Total Faturado", f"R$ {total_faturado:,.2f}")
        col_m2.metric("Lucro Líquido Total", f"R$ {total_lucro:,.2f}", delta=f"{(total_lucro / total_faturado * 100) if total_faturado > 0 else 0:.1f}% margem")
        col_m3.metric("Vendas de Novos", f"R$ {vendas_novos:,.2f}")
        col_m4.metric("Vendas de Usados", f"R$ {vendas_usados:,.2f}")

        # Exibição detalhada textual estilo relatório
        with st.expander("📄 Ver Resumo Detalhado das Vendas Realizadas"):
            for index, row in df_vendas.iterrows():
                st.markdown(f"• **Data:** {row['Data']} | **Cliente:** {row['Cliente']} | **Vendeu:** {row['Qtd']}x {row['Produto']} ({row['Novo / Usado']}) | **Preço Venda:** R$ {row['Valor Total (R$)']:,.2f} | **Custo Unitário:** R$ {row['Custo Unit. (R$)']:,.2f} | **Frete/Entrega:** R$ {row['Frete (R$)']:,.2f} | **Lucro Líquido:** **R$ {row['Lucro Líquido (R$)']:,.2f}**")

        st.dataframe(df_vendas.drop(columns=["id"]), use_container_width=True)

        # Seção de exclusão / correção ("errou, apagou")
        st.markdown("#### 🗑️ Gerenciamento / Exclusão de Vendas")
        col_del_v1, col_del_v2 = st.columns(2)
        with col_del_v1:
            venda_ids_disponiveis = df_vendas["id"].tolist()
            venda_para_apagar = st.selectbox("Selecione o ID da Venda para Excluir", venda_ids_disponiveis)
            if st.button("❌ Excluir Venda Selecionada"):
                deletar_venda(venda_para_apagar)
                st.success(f"Venda ID {venda_para_apagar} excluída com sucesso!")
                st.rerun()
        with col_del_v2:
            st.write("")
            st.write("")
            if st.button("⚠️ Apagar TODO o Histórico de Vendas"):
                limpar_todas_vendas()
                st.warning("Todo o histórico de vendas foi apagado.")
                st.rerun()
    else:
        st.info("Nenhuma venda registrada ainda.")

# =========================================================
# ABA 2: CONTROLE FINANCEIRO
# =========================================================
with aba_financeiro:
    st.title("📊 Gestão Financeira e Caixa")
    st.subheader("➕ Novo Lançamento Manual (Despesas / Custos / Receitas)")

    with st.form("form_lancamento", clear_on_submit=True):
        tipo_operacao = st.selectbox("Tipo de Operação", ["Despesa", "Receita"])

        if tipo_operacao == "Despesa":
            lista_categorias = [
                "Aluguel / Loja",
                "Água / Energia / Internet",
                "Transporte / Frete / Combustível",
                "Compra de Mercadoria / Matéria-Prima",
                "Ferragens / Ferramentas / Insumos",
                "Salários / Ajudantes",
                "Manutenção / Limpeza",
                "Outras Despesas"
            ]
        else:
            lista_categorias = [
                "Venda de Produtos",
                "Serviços e Manutenção",
                "Sinal / Encomendas",
                "Outras Receitas"
            ]

        categoria_sel = st.selectbox("Categoria", lista_categorias)
        descricao_obs = st.text_input("Descrição", placeholder="Ex: Pagamento de aluguel da oficina / Conta de luz / Frete entrega")
        valor_lancado = st.number_input("Valor (R$)", min_value=0.01, step=50.0, format="%.2f")
        data_reg = st.date_input("Data Lançamento", datetime.now())

        salvar_fin = st.form_submit_button("💾 Salvar Lançamento no Caixa", use_container_width=True)

    if salvar_fin:
        salvar_transacao(
            data=data_reg.strftime("%d/%m/%Y"),
            tipo=tipo_operacao,
            categoria=categoria_sel,
            descricao=descricao_obs,
            valor=valor_lancado
        )
        st.success("Lançamento financeiro registrado com sucesso!")
        st.rerun()

    st.divider()
    st.subheader("📈 Resumo e Indicadores do Caixa")

    df_caixa = carregar_transacoes()

    if not df_caixa.empty:
        total_entradas = df_caixa[df_caixa["Tipo"] == "Receita"]["Valor (R$)"].sum()
        total_saidas = df_caixa[df_caixa["Tipo"] == "Despesa"]["Valor (R$)"].sum()
        gastos_transporte = df_caixa[df_caixa["Categoria"].str.contains("Transporte|Frete|Combustível", case=False, na=False)]["Valor (R$)"].sum()
        gastos_fixos = df_caixa[df_caixa["Categoria"].str.contains("Aluguel|Água|Energia|Internet", case=False, na=False)]["Valor (R$)"].sum()
        saldo_caixa = total_entradas - total_saidas

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Entradas", f"R$ {total_entradas:,.2f}")
        col2.metric("Total Despesas", f"R$ {total_saidas:,.2f}")
        col3.metric("Custos com Transporte/Frete", f"R$ {gastos_transporte:,.2f}")
        col4.metric("Saldo Líquido em Caixa", f"R$ {saldo_caixa:,.2f}", delta="Saudável" if saldo_caixa >= 0 else "Negativo")

        st.write("---")
        st.subheader("📋 Histórico Completo de Lançamentos")
        st.dataframe(df_caixa.drop(columns=["id"]), use_container_width=True)

        # Seção de exclusão / correção ("errou, apagou")
        st.markdown("#### 🗑️ Gerenciamento / Exclusão de Lançamentos")
        col_del_f1, col_del_f2 = st.columns(2)
        with col_del_f1:
            trans_ids_disponiveis = df_caixa["id"].tolist()
            trans_para_apagar = st.selectbox("Selecione o ID do Lançamento para Excluir", trans_ids_disponiveis, key="sel_trans")
            if st.button("❌ Excluir Lançamento Selecionado"):
                deletar_transacao(trans_para_apagar)
                st.success(f"Lançamento ID {trans_para_apagar} excluído com sucesso!")
                st.rerun()
        with col_del_f2:
            st.write("")
            st.write("")
            if st.button("⚠️ Apagar TODO o Histórico Financeiro"):
                limpar_todas_transacoes()
                st.warning("Todo o histórico financeiro foi apagado.")
                st.rerun()
    else:
        st.info("Nenhum lançamento registrado no momento.")

# =========================================================
# ABA 3: GESTÃO DE ESTOQUE DE PRODUTOS
# =========================================================
with aba_estoque:
    st.title("📦 Controle de Estoque de Produtos e Insumos")
    st.subheader("➕ Entrada / Cadastro de Produto no Estoque")

    with st.form("form_add_estoque", clear_on_submit=True):
        nome_produto = st.text_input("Nome do Produto / Material", placeholder="Ex: Chapa MDF 18mm / Sofá Usado 3 Lugares")
        cat_produto = st.selectbox("Categoria", ["Produto Acabado", "Matéria-Prima", "Ferragem / Acessório", "Insumo / Ferramenta", "Outro"])
        estado_produto = st.selectbox("Estado do Móvel / Item", ["Móvel Novo ✨", "Móvel Usado ♻️", "Não aplicável (Insumo/Ferramenta)"])
        qtd_produto = st.number_input("Quantidade a Adicionar", min_value=1, step=1, value=1)

        preco_custo_unit = st.number_input("Preço de Custo Unitário (R$) [Quanto pagou no móvel/material]", min_value=0.0, step=10.0, format="%.2f")
        preco_venda_unit = st.number_input("Preço de Venda Unitário (R$) [Por quanto vai vender na loja]", min_value=0.0, step=50.0, format="%.2f")

        lancar_despesa_caixa = st.checkbox("Registrar custo de aquisição automaticamente no Caixa (Despesa)?", value=True)

        btn_add_est = st.form_submit_button("📥 Adicionar ao Estoque", use_container_width=True)

        if btn_add_est:
            if nome_produto.strip() != "":
                salvar_ou_atualizar_estoque(
                    produto=nome_produto.strip(),
                    categoria=cat_produto,
                    estado=estado_produto,
                    qtd=qtd_produto,
                    preco_custo=preco_custo_unit,
                    preco_venda=preco_venda_unit,
                    registrar_como_despesa=lancar_despesa_caixa
                )
                st.success(f"Estoque de '{nome_produto}' cadastrado / atualizado com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, digite o nome do produto.")

    st.divider()
    st.subheader("📋 Relatório do Estoque Atual & Valorização")

    df_estoque = carregar_estoque()
    if not df_estoque.empty:
        df_estoque["Valor Total Custo (R$)"] = df_estoque["Qtd em Estoque"] * df_estoque["Preço Custo (R$)"]
        df_estoque["Valor Total Venda (R$)"] = df_estoque["Qtd em Estoque"] * df_estoque["Preço Venda (R$)"]

        m1, m2, m3 = st.columns(3)
        m1.metric("Variedade de Itens", len(df_estoque))
        m2.metric("Capital Parado (Custo)", f"R$ {df_estoque['Valor Total Custo (R$)'].sum():,.2f}")
        m3.metric("Potencial de Faturamento", f"R$ {df_estoque['Valor Total Venda (R$)'].sum():,.2f}")

        st.dataframe(df_estoque.drop(columns=["id"]), use_container_width=True)

        # Seção de exclusão / correção ("errou, apagou")
        st.markdown("#### 🗑️ Gerenciamento / Exclusão de Itens do Estoque")
        col_del_e1, col_del_e2 = st.columns(2)
        with col_del_e1:
            est_ids_disponiveis = df_estoque["id"].tolist()
            est_para_apagar = st.selectbox("Selecione o ID do Produto para Excluir do Estoque", est_ids_disponiveis, key="sel_est")
            if st.button("❌ Excluir Item do Estoque"):
                deletar_item_estoque(est_para_apagar)
                st.success(f"Item ID {est_para_apagar} excluído do estoque com sucesso!")
                st.rerun()
        with col_del_e2:
            st.write("")
            st.write("")
            if st.button("⚠️ Apagar TODO o Estoque (Zerar Tabela)"):
                limpar_todo_estoque()
                st.warning("Todo o estoque foi apagado/zerado.")
                st.rerun()
    else:
        st.info("Nenhum item cadastrado no estoque no momento.")
































