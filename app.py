import streamlit as st
import pandas as pd
import datetime
import io
import altair as alt

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E TEMA (ACADEMIA)
# ==========================================
st.set_page_config(
    page_title="FitStock | Gestão de Estoque",
    page_icon="🏋️‍♂️",
    layout="wide"
)

st.markdown("""
    <style>
    :root { --primary: #10B981; --dark: #1F2937; --light: #F3F4F6; }
    .stApp { background-color: #FAFAFA; }
    h1,h2,h3 { color: var(--dark) !important; font-weight:800 !important; text-transform:uppercase; }
    div[data-testid="metric-container"] { background:#fff; border-radius:10px; padding:12px; box-shadow:0 4px 6px rgba(0,0,0,0.06); border-left:5px solid var(--primary); }
    .gap-alert { padding:12px; background:#FFF4E5; border-left:5px solid #FB923C; color:#92400E; border-radius:6px; font-weight:700; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# COLUNAS BASE E FUNÇÕES
# ==========================================
BASE_COLS = ['Produto', 'Estoque atual (sistema)', 'Estoque Quartinho', 'Recepção']

def init_sample_data():
    data = {
        'Produto': ['Camiseta Roxa P', 'Garrafa Squeeze 500ml', 'Toalha de Rosto', 'Whey Protein Refil', 'Luva de Treino M'],
        'Estoque atual (sistema)': [50, 120, 80, 30, 45],
        'Estoque Quartinho': [40, 100, 60, 20, 35],
        'Recepção': [10, 20, 20, 10, 10],
        '09/06/2026': [2, 0, 5, 0, 1],
        '10/06/2026': [0, 5, 2, 2, 0]
    }
    return pd.DataFrame(data)

def detect_date_columns(df):
    return [col for col in df.columns if col not in BASE_COLS]

def reconcile_and_process(df):
    df = df.copy()
    date_cols = detect_date_columns(df)
    for col in date_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Total movimentado (da soma das datas) -> representa transferências Quartinho -> Recepção
    df['Total Saídas (Datas)'] = df[date_cols].sum(axis=1) if date_cols else 0

    # Reconciliar: o 'Estoque atual (sistema)' deve representar o total físico.
    # Se quisermos derivar Quartinho inicial a partir do sistema: Quartinho_inicial = Estoque_sistema - Recepção
    df['Quartinho (Derivado do Sistema)'] = df['Estoque atual (sistema)'] - df['Recepção']

    # Se existir coluna 'Estoque Quartinho' no arquivo, mostramos diferença entre ela e o valor derivado
    df['Quartinho Diferença'] = df['Estoque Quartinho'] - df['Quartinho (Derivado do Sistema)']

    # Aplicar movimentações: tirar do quartinho derivado e somar na recepção
    df['Quartinho Atual (Calculado)'] = df['Quartinho (Derivado do Sistema)'] - df['Total Saídas (Datas)']
    df['Recepção Atual (Calculada)'] = df['Recepção'] + df['Total Saídas (Datas)']

    # Verificação de consistência final: somas deveriam bater com 'Estoque atual (sistema)'
    df['Soma Pós Movimentação'] = df['Quartinho Atual (Calculado)'] + df['Recepção Atual (Calculada)']
    df['Inconsistência com Sistema'] = df['Estoque atual (sistema)'] - df['Soma Pós Movimentação']

    # Classificar produtos com gaps (quartinho negativo) ou inconsistências
    df['Gap Quartinho'] = df['Quartinho Atual (Calculado)'].apply(lambda x: x if x < 0 else 0)
    df['Gap Sistema'] = df['Inconsistência com Sistema'].apply(lambda x: x if x != 0 else 0)

    return df, date_cols

def export_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Estoque')
    return output.getvalue()

# ==========================================
# UI PRINCIPAL
# ==========================================
st.markdown("<h1>🏋️‍♂️ FitStock | Controle Operacional</h1>", unsafe_allow_html=True)
st.markdown("Reconciliador Quartinho ↔ Recepção — o quartinho é derivado do Estoque do Sistema menos o que já existe na Recepção. As baixas são registradas por data e transferem do Quartinho para a Recepção automaticamente.")

if 'df' not in st.session_state:
    st.session_state.df = None

with st.sidebar:
    st.header("📥 Base de Dados")
    uploaded_file = st.file_uploader("Suba sua planilha Excel (.xlsx)", type=['xlsx'])
    if uploaded_file is not None:
        try:
            st.session_state.df = pd.read_excel(uploaded_file)
            st.success("Planilha carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

    if st.session_state.df is None:
        st.info("Faça o upload do seu arquivo Excel para começar.")
        if st.button("Usar Dados de Exemplo (Academia)"):
            st.session_state.df = init_sample_data()
            st.rerun()

    if st.session_state.df is not None:
        st.markdown("---")
        st.header("💾 Exportar / Reset")
        excel_data = export_excel(st.session_state.df)
        st.download_button("Baixar Planilha Atualizada ⬇️", data=excel_data, file_name=f"estoque_atualizado_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if st.button("Limpar Dados / Resetar"):
            st.session_state.df = None
            st.rerun()

if st.session_state.df is not None:
    df, date_cols = reconcile_and_process(st.session_state.df)

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔄 Registrar Baixa", "⚠️ Auditoria / Gaps", "📋 Base de Dados"])

    # --- DASHBOARD ---
    with tab1:
        st.markdown("### Visão Geral e Reconciliação")
        total_produtos = len(df)
        total_quartinho = int(df['Quartinho Atual (Calculado)'].clip(lower=0).sum())
        total_recepcao = int(df['Recepção Atual (Calculada)'].clip(lower=0).sum())
        total_movimentado = int(df['Total Saídas (Datas)'].sum())

        c1, c2, c3, c4 = st.columns([1.4,1,1,1])
        c1.metric("Itens Cadastrados", total_produtos)
        c2.metric("📦 Saldo Quartinho (Reconciliado)", total_quartinho)
        c3.metric("🛒 Saldo Recepção (Reconciliado)", total_recepcao)
        c4.metric("🔄 Total Movimentado", total_movimentado)

        st.markdown("---")
        st.markdown("#### Top Produtos Movimentados (Últimas datas)")
        top = df[['Produto','Total Saídas (Datas)']].sort_values('Total Saídas (Datas)', ascending=False).head(10)
        chart = alt.Chart(top).mark_bar().encode(
            x=alt.X('Total Saídas (Datas):Q', title='Total Movimentado'),
            y=alt.Y('Produto:N', sort='-x', title=None),
            tooltip=['Produto','Total Saídas (Datas)']
        ).properties(height=350)
        st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Produtos com maior diferença entre Quartinho histórico e Quartinho derivado")
        diffs = df[['Produto','Estoque Quartinho','Quartinho (Derivado do Sistema)','Quartinho Diferença']].sort_values('Quartinho Diferença', key=abs, ascending=False).head(8)
        st.table(diffs.style.format({"Quartinho Diferença": "{:+}"}))

    # --- REGISTRAR BAIXA ---
    with tab2:
        st.markdown("### Registrar Movimentação (Quartinho -> Recepção)")
        with st.form("form_baixa"):
            prod_list = df['Produto'].tolist()
            produto = st.selectbox("Produto", prod_list)
            data_hoje = datetime.date.today()
            data_sel = st.date_input("Data da Movimentação", value=data_hoje, format="DD/MM/YYYY")
            data_str = data_sel.strftime('%d/%m/%Y')
            quantidade = st.number_input("Quantidade a transferir", min_value=1, value=1, step=1)

            idx = df.index[df['Produto'] == produto][0]
            saldo_quartinho = int(df.loc[idx,'Quartinho Atual (Calculado)'])
            st.info(f"Saldo atual no Quartinho (reconciliado) para {produto}: {saldo_quartinho} unidades.")

            submit = st.form_submit_button("Confirmar Baixa")
            if submit:
                if data_str not in st.session_state.df.columns:
                    st.session_state.df[data_str] = 0
                st.session_state.df.loc[idx, data_str] = int(st.session_state.df.loc[idx, data_str]) + int(quantidade)
                if quantidade > saldo_quartinho:
                    st.warning(f"A operação excede o saldo reconciliado do Quartinho ({saldo_quartinho}). A baixa foi registrada e isso gerará um GAP.")
                st.success(f"Baixa registrada: {quantidade} x {produto} em {data_str}")
                st.rerun()

    # --- AUDITORIA / GAPS ---
    with tab3:
        st.markdown("### Auditoria e Gaps")
        gaps_quartinho = df[df['Quartinho Atual (Calculado)'] < 0].copy()
        gaps_sistema = df[df['Inconsistência com Sistema'] != 0].copy()

        if gaps_quartinho.empty and gaps_sistema.empty:
            st.success("Tudo consistente: não foram encontrados gaps críticos.")
        else:
            if not gaps_quartinho.empty:
                st.markdown("#### 🚨 Quartinho ficou negativo (baixas > disponível no quartinho derivado):")
                for _, r in gaps_quartinho.iterrows():
                    st.markdown(f"""<div class="gap-alert"> 
                        <b>{r['Produto']}</b><br>
                        Quartinho derivado: {r['Quartinho (Derivado do Sistema)']} | Total baixado: {r['Total Saídas (Datas)']}<br>
                        <b>Faltam {int(abs(r['Quartinho Atual (Calculado)']))} itens no Quartinho.</b>
                        </div>""", unsafe_allow_html=True)
                st.dataframe(gaps_quartinho[['Produto','Quartinho (Derivado do Sistema)','Total Saídas (Datas)','Quartinho Atual (Calculado)']].reset_index(drop=True), hide_index=True)

            if not gaps_sistema.empty:
                st.markdown("#### ⚠️ Inconsistências com o Estoque do Sistema (soma pós-movimentação difere do total do sistema):")
                st.dataframe(gaps_sistema[['Produto','Estoque atual (sistema)','Soma Pós Movimentação','Inconsistência com Sistema']].reset_index(drop=True), hide_index=True)

    # --- BASE DE DADOS ---
    with tab4:
        st.markdown("### Base de Dados Completa (com campos calculados)")
        cols_display = BASE_COLS + date_cols + ['Total Saídas (Datas)','Quartinho (Derivado do Sistema)','Quartinho Atual (Calculado)','Recepção Atual (Calculada)','Inconsistência com Sistema']
        styled = df[cols_display].copy()
        # Formatação simples: colorir quartinho negativo
        def color_quartinho(val):
            try:
                val = float(val)
                if val < 0:
                    return 'background-color: #FEE2E2'
                elif val == 0:
                    return 'background-color: #FEF3C7'
                else:
                    return ''
            except:
                return ''
        st.dataframe(styled.style.applymap(color_quartinho, subset=['Quartinho Atual (Calculado)']), use_container_width=True)
