import pandas as pd
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="R - Gestão Comercial", page_icon="📦", layout="wide"
)

# Inicialização do Banco de Dados na Sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if "estoque" not in st.session_state:
    st.session_state["estoque"] = pd.DataFrame(
        columns=[
            "ID",
            "Modelo",
            "Produto",
            "Custo (R$)",
            "Venda (R$)",
            "Quantidade",
        ]
    )

if "despesas" not in st.session_state:
    st.session_state["despesas"] = pd.DataFrame(
        columns=["Descrição", "Categoria", "Valor (R$)", "Mês/Ano"]
    )

if "vendas" not in st.session_state:
    st.session_state["vendas"] = pd.DataFrame(
        columns=[
            "Produto",
            "Quantidade",
            "Valor Total",
            "Lucro Bruto",
            "Data/Mês",
        ]
    )


# Função para exibir o Logotipo da Marca 'R'
def exibir_logo():
    st.markdown(
        """
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #FF4B2B, #FF416C); border-radius: 16px; margin-bottom: 25px; box-shadow: 0 6px 15px rgba(255,75,43,0.3);">
            <h1 style="color: white; margin: 0; font-size: 50px; font-weight: 900; letter-spacing: 2px;">R</h1>
            <p style="color: white; margin: 0; font-size: 13px; font-weight: bold; letter-spacing: 3px;">GESTÃO COMERCIAL INTELIGENTE</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- TELA DE LOGIN ---
if not st.session_state["autenticado"]:
    exibir_logo()
    st.markdown(
        "<h3 style='text-align: center;'>Acesse o seu Comércio</h3>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        usuario = st.text_input("Usuário", key="txt_usuario")
        senha = st.text_input("Senha", type="password", key="txt_senha")
        if st.button("Entrar no Aplicativo", use_container_width=True):
            if usuario == "admin" and senha == "1234":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos! (Use admin / 1234)")
    st.stop()


# --- APLICAÇÃO PRINCIPAL (PÓS-LOGIN) ---
exibir_logo()

st.sidebar.markdown(
    "<h3 style='text-align: center;'>Menu Principal</h3>", unsafe_allow_html=True
)
menu = st.sidebar.selectbox(
    "Navegação",
    [
        "📊 Painel Geral",
        "🛋️ Controle de Estoque",
        "💸 Despesas & Custos",
        "💰 Registrar Venda",
        "📈 Fechamento & Relatório",
        "🔄 Fechar Mês / Zerar",
    ],
    label_visibility="collapsed",
)

# --- PAINEL GERAL ---
if menu == "📊 Painel Geral":
    st.title("📊 Painel de Controle da Loja")
    st.write(
        "Visão rápida e colorida de tudo o que está acontecendo no seu comércio."
    )

    total_produtos = (
        st.session_state["estoque"]["Quantidade"].sum()
        if not st.session_state["estoque"].empty
        else 0
    )
    valor_estoque_custo = (
        (
            st.session_state["estoque"]["Custo (R$)"]
            * st.session_state["estoque"]["Quantidade"]
        ).sum()
        if not st.session_state["estoque"].empty
        else 0
    )
    total_despesas = (
        st.session_state["despesas"]["Valor (R$)"].sum()
        if not st.session_state["despesas"].empty
        else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        label="📦 Total de Itens no Estoque",
        value=int(total_produtos),
        delta="Disponível",
    )
    c2.metric(
        label="💵 Capital em Produtos (Custo)",
        value=f"R$ {valor_estoque_custo:.2f}",
    )
    c3.metric(
        label="📉 Despesas Totais Registradas", value=f"R$ {total_despesas:.2f}"
    )

    st.markdown("---")
    st.subheader("🛋️ Produtos Ativos no Estoque")
    if not st.session_state["estoque"].empty:
        st.dataframe(
            st.session_state["estoque"], use_container_width=True, hide_index=True
        )
    else:
        st.info(
            "Nenhum móvel cadastrado ainda. Vá no menu ao lado e selecione '🛋️ Controle de Estoque'."
        )

# --- CONTROLE DE ESTOQUE ---
elif menu == "🛋️ Controle de Estoque":
    st.title("🛋️ Cadastro e Gestão de Móveis")
    st.write(
        "Adicione novos móveis informando o modelo, produto, custo e valor de venda."
    )

    col1, col2 = st.columns(2)
    with col1:
        modelo = st.text_input(
            "Modelo do Móvel (Ex: Retrô, Rústico)", key="cad_modelo"
        )
        produto = st.text_input(
            "Nome do Produto (Ex: Guarda-Roupa)", key="cad_produto"
        )
        quantidade = st.number_input(
            "Quantidade", min_value=1, step=1, value=1, key="cad_qtd"
        )
    with col2:
        custo = st.number_input(
            "Valor de Custo (R$)", min_value=0.0, format="%.2f", key="cad_custo"
        )
        venda = st.number_input(
            "Valor de Venda (R$)", min_value=0.0, format="%.2f", key="cad_venda"
        )

    if st.button(
        "💾 Cadastrar Móvel no Estoque",
        use_container_width=True,
        type="primary",
    ):
        if modelo.strip() and produto.strip():
            novo_id = len(st.session_state["estoque"]) + 1
            novo_item = pd.DataFrame(
                [
                    {
                        "ID": novo_id,
                        "Modelo": modelo,
                        "Produto": produto,
                        "Custo (R$)": custo,
                        "Venda (R$)": venda,
                        "Quantidade": quantidade,
                    }
                ]
            )
            st.session_state["estoque"] = pd.concat(
                [st.session_state["estoque"], novo_item], ignore_index=True
            )
            st.success(
                f"Móvel '{produto}' cadastrado com sucesso no estoque! 🎉"
            )
        else:
            st.warning(
                "Por favor, preencha o Modelo e o Nome do Produto antes de cadastrar."
            )

    st.markdown("---")
    st.subheader("Lista Completa do Estoque")
    if not st.session_state["estoque"].empty:
        st.dataframe(
            st.session_state["estoque"], use_container_width=True, hide_index=True
        )
    else:
        st.info("O estoque está vazio no momento.")

# --- DESPESAS & CUSTOS ---
elif menu == "💸 Despesas & Custos":
    st.title("💸 Controle de Despesas e Gastos")
    st.write(
        "Registre custos do comércio (Aluguel, Água, Combustível para entregas, etc)."
    )

    col1, col2 = st.columns(2)
    with col1:
        descricao = st.text_input(
            "Descrição do Gasto (Ex: Aluguel da Loja)", key="gasto_desc"
        )
        categoria = st.selectbox(
            "Categoria",
            [
                "Aluguel",
                "Água / Luz / Internet",
                "Combustível / Frete",
                "Manutenção",
                "Outros",
            ],
            key="gasto_cat",
        )
    with col2:
        valor = st.number_input(
            "Valor do Gasto (R$)", min_value=0.0, format="%.2f", key="gasto_val"
        )
        mes_ano = st.text_input(
            "Mês/Ano (Ex: 03/2026)", value="03/2026", key="gasto_mes"
        )

    if st.button(
        "💾 Registrar Despesa", use_container_width=True, type="primary"
    ):
        if descricao.strip() and mes_ano.strip():
            nova_despesa = pd.DataFrame(
                [
                    {
                        "Descrição": descricao,
                        "Categoria": categoria,
                        "Valor (R$)": valor,
                        "Mês/Ano": mes_ano,
                    }
                ]
            )
            st.session_state["despesas"] = pd.concat(
                [st.session_state["despesas"], nova_despesa], ignore_index=True
            )
            st.success("Despesa salva com sucesso! 💸")
        else:
            st.warning(
                "Preencha a descrição e o mês/ano para registrar a despesa."
            )

    st.markdown("---")
    st.subheader("Histórico de Despesas")
    if not st.session_state["despesas"].empty:
        st.dataframe(
            st.session_state["despesas"], use_container_width=True, hide_index=True
        )

# --- REGISTRAR VENDA ---
elif menu == "💰 Registrar Venda":
    st.title("💰 Registrar Saída / Venda")

    if st.session_state["estoque"].empty:
        st.warning("Cadastre produtos no estoque antes de registrar vendas.")
    else:
        produtos_disponiveis = st.session_state["estoque"]["Produto"].tolist()
        produto_escolhido = st.selectbox(
            "Selecione o Móvel Vendido", produtos_disponiveis, key="venda_prod"
        )
        qtd_vendida = st.number_input(
            "Quantidade Vendida", min_value=1, step=1, value=1, key="venda_qtd"
        )
        data_venda = st.text_input(
            "Mês/Ano da Venda (Ex: 03/2026)", value="03/2026", key="venda_data"
        )

        if st.button(
            "💾 Concluir Venda", use_container_width=True, type="primary"
        ):
            item_idx = st.session_state["estoque"][
                st.session_state["estoque"]["Produto"] == produto_escolhido
            ].index[0]
            estoque_atual = st.session_state["estoque"].loc[
                item_idx, "Quantidade"
            ]

            if qtd_vendida <= estoque_atual:
                preco_venda = st.session_state["estoque"].loc[
                    item_idx, "Venda (R$)"
                ]
                preco_custo = st.session_state["estoque"].loc[
                    item_idx, "Custo (R$)"
                ]

                val_total = preco_venda * qtd_vendida
                lucro_bruto = (preco_venda - preco_custo) * qtd_vendida

                st.session_state["estoque"].loc[item_idx, "Quantidade"] = (
                    estoque_atual - qtd_vendida
                )

                nova_venda = pd.DataFrame(
                    [
                        {
                            "Produto": produto_escolhido,
                            "Quantidade": qtd_vendida,
                            "Valor Total": val_total,
                            "Lucro Bruto": lucro_bruto,
                            "Data/Mês": data_venda,
                        }
                    ]
                )
                st.session_state["vendas"] = pd.concat(
                    [st.session_state["vendas"], nova_venda], ignore_index=True
                )
                st.success(
                    f"Venda efetuada com sucesso! Lucro bruto: R$ {lucro_bruto:.2f} 🚀"
                )
            else:
                st.error("Quantidade vendida maior do que o estoque atual!")

    st.markdown("---")
    st.subheader("Histórico de Vendas")
    if not st.session_state["vendas"].empty:
        st.dataframe(
            st.session_state["vendas"], use_container_width=True, hide_index=True
        )

# --- FECHAMENTO & RELATÓRIO ---
elif menu == "📈 Fechamento & Relatório":
    st.title("📈 Fechamento e Resultado Líquido do Mês")
    st.write(
        "Saiba exatamente quanto entrou, quanto gastou e qual foi o **lucro líquido real** no seu bolso."
    )

    mes_filtro = st.text_input(
        "Digite o Mês/Ano para Fechamento (Ex: 03/2026)",
        value="03/2026",
        key="fech_mes",
    )

    if st.button("📊 Calcular Fechamento Mensal", use_container_width=True):
        vendas_mes = st.session_state["vendas"]
        if not vendas_mes.empty and "Data/Mês" in vendas_mes.columns:
            vendas_filtradas = vendas_mes[vendas_mes["Data/Mês"] == mes_filtro]
            total_faturamento = (
                vendas_filtradas["Valor Total"].sum()
                if not vendas_filtradas.empty
                else 0
            )
            total_lucro_bruto = (
                vendas_filtradas["Lucro Bruto"].sum()
                if not vendas_filtradas.empty
                else 0
            )
        else:
            total_faturamento = 0
            total_lucro_bruto = 0
            vendas_filtradas = pd.DataFrame()

        despesas_mes = st.session_state["despesas"]
        if not despesas_mes.empty and "Mês/Ano" in despesas_mes.columns:
            despesas_filtradas = despesas_mes[
                despesas_mes["Mês/Ano"] == mes_filtro
            ]
            total_despesas_mes = (
                despesas_filtradas["Valor (R$)"].sum()
                if not despesas_filtradas.empty
                else 0
            )
        else:
            total_despesas_mes = 0
            despesas_filtradas = pd.DataFrame()

        lucro_liquido = total_lucro_bruto - total_despesas_mes

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {total_faturamento:.2f}")
        col2.metric("📉 Total de Despesas", f"R$ {total_despesas_mes:.2f}")

        if lucro_liquido >= 0:
            col3.metric(
                "🚀 Lucro Líquido Real",
                f"R$ {lucro_liquido:.2f}",
                delta="No Bolso",
            )
            st.success(
                f"Parabéns! No mês **{mes_filtro}**, a loja fechou no **AZUL** com um lucro líquido de **R$ {lucro_liquido:.2f}**."
            )
        else:
            col3.metric(
                "⚠️ Prejuízo do Mês",
                f"R$ {lucro_liquido:.2f}",
                delta="Atenção",
                delta_color="inverse",
            )
            st.error(
                f"Atenção! No mês **{mes_filtro}**, as despesas superaram o ganho. Prejuízo de **R$ {lucro_liquido:.2f}**."
            )

        if not vendas_filtradas.empty or not despesas_filtradas.empty:
            st.markdown("---")
            st.subheader("📥 Baixar Relatório do Mês")
            relatorio_texto = f"RELATÓRIO FINANCEIRO - R GESTÃO COMERCIAL\nMês: {mes_filtro}\nFaturamento: R$ {total_faturamento:.2f}\nDespesas: R$ {total_despesas_mes:.2f}\nLucro Líquido: R$ {lucro_liquido:.2f}"
            st.download_button(
                label="Baixar Resumo em Arquivo de Texto",
                data=relatorio_texto,
                file_name=f"relatorio_{mes_filtro.replace('/', '-')}.txt",
                mime="text/plain",
            )

# --- FECHAR MÊS / ZERAR ---
elif menu == "🔄 Fechar Mês / Zerar":
    st.title("🔄 Reiniciar Ciclo / Fechar Mês")
    st.warning(
        "Atenção: Use esta opção no final do mês para limpar as vendas e despesas antigas e começar o novo mês com o caixa limpo!"
    )

    confirmar = st.checkbox("Estou ciente e quero zerar os registros do mês")
    if st.button("🔄 Zerar Vendas e Despesas", use_container_width=True):
        if confirmar:
            st.session_state["vendas"] = pd.DataFrame(
                columns=[
                    "Produto",
                    "Quantidade",
                    "Valor Total",
                    "Lucro Bruto",
                    "Data/Mês",
                ]
            )
            st.session_state["despesas"] = pd.DataFrame(
                columns=["Descrição", "Categoria", "Valor (R$)", "Mês/Ano"]
            )
            st.success(
                "Registros mensais zerados com sucesso! Pronto para começar um novo mês."
            )
        else:
            st.error(
                "Marque a caixa de confirmação acima para autorizar a limpeza dos dados."
            )

# --- RODAPÉ DA MARCA ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray; font-size: 13px; padding-bottom: 20px;">
        <b>R - Gestão Comercial</b> | Desenvolvido para Pequenos Comércios e Lojas
    </div>
    """,
    unsafe_allow_html=True,
)
