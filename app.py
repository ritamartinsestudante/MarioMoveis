import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (SISTEMA DE GESTÃO - MÁRIO MÓVEIS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mário Móveis - Gestão Financeira",
    page_icon="🪵",
    layout="wide"
)

# ---------------------------------------------------------
# AUTENTICAÇÃO E LOGIN DE ACESSO
# ---------------------------------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

# Credenciais de acesso
USUARIO_SISTEMA = "mario"
SENHA_SISTEMA = "mario2026"


def tela_login():
    st.title("🔒 Mário Móveis - Acesso Restrito")
    st.write("Digite o usuário e senha para acessar o painel financeiro.")

    col_login, _ = st.columns([1, 1])
    with col_login:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar no Sistema"):
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

# Menu Lateral
with st.sidebar:
    st.title("🪵 Mário Móveis")
    st.write("Painel de Controle")
    st.divider()
    if st.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

st.title("📊 Gestão Financeira e Controle de Caixa")

# Inicialização do Banco de Dados Temporário
if "transacoes" not in st.session_state:
    st.session_state.transacoes = pd.DataFrame(columns=[
        "Data", "Tipo", "Categoria", "Descrição", "Valor (R$)"
    ])

# ---------------------------------------------------------
# FORMULÁRIO DE CADASTRO DE LANÇAMENTOS
# ---------------------------------------------------------
st.subheader("➕ Novo Lançamento")

c_tipo, c_cat, c_desc, c_val, c_data = st.columns([1.5, 2, 2.5, 1.5, 1.5])

with c_tipo:
    tipo_operacao = st.selectbox("Tipo", ["Despesa", "Receita"])

with c_cat:
    if tipo_operacao == "Despesa":
        lista_categorias = [
            "Transporte / Frete",  # Custo de transporte incluído
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

with c_desc:
    descricao_obs = st.text_input("Descrição", placeholder="Ex: Entrega do armário na cliente Maria")

with c_val:
    valor_lancado = st.number_input("Valor (R$)", min_value=0.01, step=50.0, format="%.2f")

with c_data:
    data_reg = st.date_input("Data", datetime.now())

if st.button("💾 Salvar Registro", use_container_width=True):
    novo_dado = {
        "Data": data_reg.strftime("%d/%m/%Y"),
        "Tipo": tipo_operacao,
        "Categoria": categoria_sel,
        "Descrição": descricao_obs,
        "Valor (R$)": valor_lancado
    }
    st.session_state.transacoes = pd.concat([
        st.session_state.transacoes,
        pd.DataFrame([novo_dado])
    ], ignore_index=True)
    st.success("Lançamento adicionado com sucesso!")

st.divider()

# ---------------------------------------------------------
# DASHBOARD DE RESULTADOS E RESUMO FINANCEIRO
# ---------------------------------------------------------
st.subheader("📈 Resumo do Mês")

df_caixa = st.session_state.transacoes

if not df_caixa.empty:
    total_entradas = df_caixa[df_caixa["Tipo"] == "Receita"]["Valor (R$)"].sum()
    total_saidas = df_caixa[df_caixa["Tipo"] == "Despesa"]["Valor (R$)"].sum()

    # Soma exclusiva dos custos com frete/transporte
    gastos_transporte = df_caixa[df_caixa["Categoria"].isin(["Transporte / Frete", "Combustível / Uber"])][
        "Valor (R$)"].sum()

    saldo_caixa = total_entradas - total_saidas

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Vendas / Receitas", f"R$ {total_entradas:,.2f}")
    col2.metric("Total de Despesas", f"R$ {total_saidas:,.2f}")
    col3.metric("Custos c/ Transporte/Frete", f"R$ {gastos_transporte:,.2f}")
    col4.metric("Saldo Em Caixa", f"R$ {saldo_caixa:,.2f}")

    st.write("---")
    st.subheader("📋 Historico de Transações")
    st.dataframe(df_caixa, use_container_width=True)
else:
    st.info("Nenhum lançamento cadastrado no momento.")



