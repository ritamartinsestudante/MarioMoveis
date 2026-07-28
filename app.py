import os
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mário Móveis - Gestão Completa", page_icon="🪵", layout="wide"
)

# ---------------------------------------------------------
# SUPORTE A PWA (TRANSFORMA EM ÍCONE / APP NO CELULAR)
# ---------------------------------------------------------
pwa_code = """
<script>
    (function() {
        const manifest = {
            "name": "Mário Móveis - Gestão",
            "short_name": "Mário Móveis",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#3E2723",
            "theme_color": "#3E2723",
            "icons": [
                {
                    "src": "https://img.icons8.com/color/512/hardwood.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        };

        // Aplica o manifesto no documento principal (fora do iframe do Streamlit)
        const targetDoc = window.top.document;
        if (!targetDoc.querySelector('link[rel="manifest"]')) {
            const stringManifest = JSON.stringify(manifest);
            const blob = new Blob([stringManifest], {type: 'application/json'});
            const manifestURL = URL.createObjectURL(blob);
            const link = targetDoc.createElement('link');
            link.rel = 'manifest';
            link.href = manifestURL;
            targetDoc.head.appendChild(link);
        }
    })();
</script>
"""
components.html(pwa_code, height=0)

# Arquivos de persistência de dados
FILE_MOVEIS = "moveis.csv"
FILE_VENDAS = "vendas.csv"
FILE_DESPESAS = "despesas.csv"

# ---------------------------------------------------------
# SISTEMA DE LOGIN E AUTENTICAÇÃO
# ---------------------------------------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

USUARIO_CORRETO = "mario"
SENHA_CORRETA = "mario2026"


def tela_login():
    st.title("🔒 Mário Móveis - Acesso Restrito")
    st.write("Insira suas credenciais para acessar o sistema de gestão.")

    col_login, _ = st.columns([1, 1])
    with col_login:
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")

        if st.button("Entrar no Sistema", use_container_width=True):
            if (
                    usuario_input == USUARIO_CORRETO
                    and senha_input == SENHA_CORRETA
            ):
                st.session_state.logado = True
                st.success("Acesso liberado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")


if not st.session_state.logado:
    tela_login()
    st.stop()

# ---------------------------------------------------------
# INICIALIZAÇÃO DOS BANCOS DE DADOS EM MEMÓRIA / CSV
# ---------------------------------------------------------
if "moveis" not in st.session_state:
    if os.path.exists(FILE_MOVEIS):
        st.session_state.moveis = pd.read_csv(FILE_MOVEIS)
    else:
        st.session_state.moveis = pd.DataFrame(
            columns=[
                "Código",
                "Nome do Móvel",
                "Categoria",
                "Preço de Custo (R$)",
                "Preço de Venda (R$)",
                "Estoque",
            ]
        )

if "vendas" not in st.session_state:
    if os.path.exists(FILE_VENDAS):
        st.session_state.vendas = pd.read_csv(FILE_VENDAS)
    else:
        st.session_state.vendas = pd.DataFrame(
            columns=["Data", "Móvel", "Quantidade", "Valor Total (R$)", "Cliente"]
        )

if "despesas" not in st.session_state:
    if os.path.exists(FILE_DESPESAS):
        st.session_state.despesas = pd.read_csv(FILE_DESPESAS)
    else:
        st.session_state.despesas = pd.DataFrame(
            columns=["Data", "Categoria", "Descrição", "Valor (R$)"]
        )


def salvar_dados():
    st.session_state.moveis.to_csv(FILE_MOVEIS, index=False)
    st.session_state.vendas.to_csv(FILE_VENDAS, index=False)
    st.session_state.despesas.to_csv(FILE_DESPESAS, index=False)


# ---------------------------------------------------------
# BARRA LATERAL (MENU DE NAVEGAÇÃO E LOGOUT)
# ---------------------------------------------------------
with st.sidebar:
    st.title("🪵 Mário Móveis")
    st.write("Sistema de Controle")

    menu = st.radio(
        "Navegação",
        [
            "📦 Cadastrar Móvel / Estoque",
            "🛒 Registrar Venda",
            "💸 Despesas e Combustível",
            "📊 Relatórios e Caixa",
        ],
    )

    st.divider()
    if st.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

# ---------------------------------------------------------
# PÁGINA 1: CADASTRO DE MÓVEIS E ESTOQUE
# ---------------------------------------------------------
if menu == "📦 Cadastrar Móvel / Estoque":
    st.title("📦 Cadastro de Móveis e Controle de Estoque")

    with st.form("form_cadastrar_movel", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input(
                "Código do Móvel", f"MOV-{len(st.session_state.moveis) + 1:03d}"
            )
            nome = st.text_input(
                "Nome do Móvel (ex: Armário Planejado, Mesa de Jantar)"
            )
            categoria_movel = st.selectbox(
                "Tipo de Móvel",
                [
                    "Móvel Sob Medida",
                    "Restauração",
                    "Móvel de Pronta Entrega",
                    "Outros",
                ],
            )
        with col2:
            custo = st.number_input(
                "Preço de Custo (R$)", min_value=0.0, format="%.2f"
            )
            venda = st.number_input(
                "Preço de Venda (R$)", min_value=0.0, format="%.2f"
            )
            qtd = st.number_input("Quantidade em Estoque", min_value=1, step=1)

        salvar_movel = st.form_submit_button("➕ Salvar Móvel no Estoque")

        if salvar_movel:
            if nome:
                novo_movel = {
                    "Código": codigo,
                    "Nome do Móvel": nome,
                    "Categoria": categoria_movel,
                    "Preço de Custo (R$)": custo,
                    "Preço de Venda (R$)": venda,
                    "Estoque": qtd,
                }
                st.session_state.moveis = pd.concat(
                    [st.session_state.moveis, pd.DataFrame([novo_movel])],
                    ignore_index=True,
                )
                salvar_dados()
                st.success(f"Móvel '{nome}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("Por favor, preencha o nome do móvel.")

    st.divider()
    st.subheader("📋 Estoque Atual")
    if not st.session_state.moveis.empty:
        st.dataframe(st.session_state.moveis, use_container_width=True)
    else:
        st.info("Nenhum móvel cadastrado até o momento.")

# ---------------------------------------------------------
# PÁGINA 2: REGISTRO DE VENDAS
# ---------------------------------------------------------
elif menu == "🛒 Registrar Venda":
    st.title("🛒 Registro de Vendas")

    if st.session_state.moveis.empty:
        st.warning(
            "Cadastre móveis na aba de 'Estoque' antes de realizar uma venda."
        )
    else:
        lista_moveis = st.session_state.moveis["Nome do Móvel"].tolist()

        with st.form("form_venda", clear_on_submit=True):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                movel_selecionado = st.selectbox(
                    "Selecione o Móvel Vendido", lista_moveis
                )
                cliente = st.text_input("Nome do Cliente")
            with col_v2:
                qtd_venda = st.number_input(
                    "Quantidade Vendida", min_value=1, step=1
                )
                data_venda = st.date_input("Data da Venda", datetime.now())

            row_busca = st.session_state.moveis.loc[
                st.session_state.moveis["Nome do Móvel"] == movel_selecionado,
                "Preço de Venda (R$)",
            ]
            preco_unitario = (
                row_busca.values[0] if not row_busca.empty else 0.0
            )

            valor_total_venda = preco_unitario * qtd_venda
            st.info(f"Valor Total Estimado da Venda: R$ {valor_total_venda:,.2f}")

            confirmar_venda = st.form_submit_button("✅ Registrar Venda")

            if confirmar_venda:
                idx_list = st.session_state.moveis.index[
                    st.session_state.moveis["Nome do Móvel"] == movel_selecionado
                    ].tolist()
                if idx_list:
                    idx = idx_list[0]
                    estoque_atual = st.session_state.moveis.at[idx, "Estoque"]

                    if estoque_atual >= qtd_venda:
                        st.session_state.moveis.at[idx, "Estoque"] -= qtd_venda

                        nova_venda = {
                            "Data": data_venda.strftime("%d/%m/%Y"),
                            "Móvel": movel_selecionado,
                            "Quantidade": qtd_venda,
                            "Valor Total (R$)": valor_total_venda,
                            "Cliente": cliente,
                        }
                        st.session_state.vendas = pd.concat(
                            [
                                st.session_state.vendas,
                                pd.DataFrame([nova_venda]),
                            ],
                            ignore_index=True,
                        )
                        salvar_dados()
                        st.success(
                            f"Venda de '{movel_selecionado}' registrada com sucesso!"
                        )
                        st.rerun()
                    else:
                        st.error(
                            f"Estoque insuficiente! Há apenas {estoque_atual} unidade(s) disponível(is)."
                        )

        st.divider()
        st.subheader("🛍️ Histórico de Vendas")
        if not st.session_state.vendas.empty:
            st.dataframe(st.session_state.vendas, use_container_width=True)
        else:
            st.info("Nenhuma venda registrada ainda.")

# ---------------------------------------------------------
# PÁGINA 3: DESPESAS E CUSTOS DE TRANSPORTE/COMBUSTÍVEL
# ---------------------------------------------------------
elif menu == "💸 Despesas e Combustível":
    st.title("💸 Lançamento de Despesas e Custos Operacionais")

    with st.form("form_despesa", clear_on_submit=True):
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            categoria_despesa = st.selectbox(
                "Categoria do Gasto",
                [
                    "Combustível / Uber",
                    "Transporte / Frete",
                    "Matéria-Prima / Madeira",
                    "Ferragens / Insumos",
                    "Aluguel da Oficina",
                    "Energia / Água",
                    "Salários / Ajudantes",
                    "Manutenção de Ferramentas",
                    "Outras Despesas",
                ],
            )
            descricao_d = st.text_input(
                "Descrição do Gasto (ex: Gasolina para entrega, Frete de tábuas)"
            )
        with c_d2:
            valor_d = st.number_input(
                "Valor do Gasto (R$)", min_value=0.01, format="%.2f"
            )
            data_d = st.date_input("Data do Gasto", datetime.now())

        salvar_despesa = st.form_submit_button("💸 Registrar Despesa")

        if salvar_despesa:
            nova_desp = {
                "Data": data_d.strftime("%d/%m/%Y"),
                "Categoria": categoria_despesa,
                "Descrição": descricao_d,
                "Valor (R$)": valor_d,
            }
            st.session_state.despesas = pd.concat(
                [st.session_state.despesas, pd.DataFrame([nova_desp])],
                ignore_index=True,
            )
            salvar_dados()
            st.success(f"Despesa de '{categoria_despesa}' gravada com sucesso!")
            st.rerun()

    st.divider()
    st.subheader("📋 Lista de Despesas")
    if not st.session_state.despesas.empty:
        st.dataframe(st.session_state.despesas, use_container_width=True)
    else:
        st.info("Nenhuma despesa lançada no momento.")

# ---------------------------------------------------------
# PÁGINA 4: RELATÓRIOS E BALANÇO DE CAIXA
# ---------------------------------------------------------
elif menu == "📊 Relatórios e Caixa":
    st.title("📊 Resumo Financeiro e Indicadores")

    total_faturamento = (
        st.session_state.vendas["Valor Total (R$)"].sum()
        if not st.session_state.vendas.empty
        else 0.0
    )
    total_saidas = (
        st.session_state.despesas["Valor (R$)"].sum()
        if not st.session_state.despesas.empty
        else 0.0
    )

    if not st.session_state.despesas.empty:
        gastos_transporte = st.session_state.despesas[
            st.session_state.despesas["Categoria"].isin(
                ["Transporte / Frete", "Combustível / Uber"]
            )
        ]["Valor (R$)"].sum()
    else:
        gastos_transporte = 0.0

    saldo_liquido = total_faturamento - total_saidas

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Faturamento Total (Vendas)", f"R$ {total_faturamento:,.2f}")
    col_m2.metric("Total de Despesas", f"R$ {total_saidas:,.2f}")
    col_m3.metric(
        "Gasto c/ Transporte e Combustível", f"R$ {gastos_transporte:,.2f}"
    )
    col_m4.metric("Saldo Líquido em Caixa", f"R$ {saldo_liquido:,.2f}")

    st.divider()
    st.subheader("🔍 Resumo Geral")
    st.write(f"Móveis Cadastrados: **{len(st.session_state.moveis)}**")
    st.write(
        f"Total de Vendas Realizadas: **{len(st.session_state.vendas)}**"
    )
    st.write(
        f"Total de Lançamentos de Despesas: **{len(st.session_state.despesas)}**"
    )





