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
    conn.commit()
    conn.close()


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


# Inicializa o banco ao carregar o aplicativo
inicializar_banco()

# ---------------------------------------------------------
# CARREGAMENTO SEGURO DA LOGO (PIL / Pillow)
# ---------------------------------------------------------
CAMINHO_LOGO = os.path.join("static", "logo.png")


def exibir_logo():
    """Exibe o logo da pasta static se existir; caso contrário, exibe o título em texto."""
    if os.path.exists(CAMINHO_LOGO):
        img = Image.open(CAMINHO_LOGO)
        st.image(img, width=180)
    else:
        st.title("🪵 Mário Móveis")


# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (OTIMIZADA PARA CELULAR)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mário Móveis - Gestão Financeira",
    page_icon="🪵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# AUTENTICAÇÃO E LOGIN DE ACESSO
# ---------------------------------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

USUARIO_SISTEMA = "mario"
SENHA_SISTEMA = "mario2026"


def tela_login():
    exibir_logo()  # <-- LOGO NA TELA DE LOGIN
    st.caption("🔒 Acesso Restrito - Gestão Financeira")

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
# PAINEL PRINCIPAL (ÁREA LOGADA)
# ---------------------------------------------------------

# Menu Lateral (Sidebar)
with st.sidebar:
    exibir_logo()  # <-- LOGO NO MENU LATERAL
    st.write("Painel de Controle")
    st.divider()
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.logado = False
        st.rerun()

# Topo da página principal
exibir_logo()  # <-- LOGO NO TOPO DO PAINEL PRINCIPAL
st.title("📊 Gestão Financeira e Controle de Caixa")

# ---------------------------------------------------------
# FORMULÁRIO DE CADASTRO DE LANÇAMENTOS
# ---------------------------------------------------------
st.subheader("➕ Novo Lançamento")

with st.form("form_lancamento", clear_on_submit=True):
    tipo_operacao = st.selectbox("Tipo", ["Despesa", "Receita"])

    if tipo_operacao == "Despesa":
        lista_categorias = [
            "Transporte / Frete",
            "Combustível / Uber",
            "Matéria-Prima / Madeira",
            "Ferragens / Insumos",
            "Aluguel / Oficina",
            "Energia / Água",
            "Salários / Ajudantes",
            "Manutenção de Ferramentas",
            "Outras Despesas"
        ]
    else:
        lista_categorias = [
            "Venda de Móveis Sob Medida",
            "Serviços de Restauração",
            "Entradas de Encomendas (Sinal)",
            "Outras Receitas"
        ]

    categoria_sel = st.selectbox("Categoria", lista_categorias)
    descricao_obs = st.text_input("Descrição", placeholder="Ex: Entrega do armário na cliente Maria")
    valor_lancado = st.number_input("Valor (R$)", min_value=0.01, step=50.0, format="%.2f")
    data_reg = st.date_input("Data", datetime.now())

    salvar = st.form_submit_button("💾 Salvar Registro", use_container_width=True)

if salvar:
    # Salva diretamente no Banco de Dados
    salvar_transacao(
        data=data_reg.strftime("%d/%m/%Y"),
        tipo=tipo_operacao,
        categoria=categoria_sel,
        descricao=descricao_obs,
        valor=valor_lancado
    )
    st.success("Lançamento salvo com sucesso no Banco de Dados!")

st.divider()

# ---------------------------------------------------------
# DASHBOARD DE RESULTADOS E RESUMO FINANCEIRO
# ---------------------------------------------------------
st.subheader("📈 Resumo do Mês")

# Busca sempre do Banco de Dados
df_caixa = carregar_transacoes()

if not df_caixa.empty:
    total_entradas = df_caixa[df_caixa["Tipo"] == "Receita"]["Valor (R$)"].sum()
    total_saidas = df_caixa[df_caixa["Tipo"] == "Despesa"]["Valor (R$)"].sum()
    gastos_transporte = df_caixa[df_caixa["Categoria"].isin(["Transporte / Frete", "Combustível / Uber"])][
        "Valor (R$)"].sum()
    saldo_caixa = total_entradas - total_saidas

    # Exibição adaptada para telas menores
    col1, col2 = st.columns(2)
    col1.metric("Vendas / Receitas", f"R$ {total_entradas:,.2f}")
    col2.metric("Total Despesas", f"R$ {total_saidas:,.2f}")

    col3, col4 = st.columns(2)
    col3.metric("Frete / Transporte", f"R$ {gastos_transporte:,.2f}")
    col4.metric("Saldo Em Caixa", f"R$ {saldo_caixa:,.2f}")

    st.write("---")
    st.subheader("📋 Histórico de Transações Salvas")
    st.dataframe(df_caixa, use_container_width=True)
else:
    st.info("Nenhum lançamento cadastrado no momento.")




