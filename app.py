import streamlit as st
import pandas as pd
import io
import hmac
from datetime import datetime

st.set_page_config(
    page_title="Etapa 1 - Acompanhamento Moodle",
    page_icon="📚",
    layout="wide"
)

# 1. LOGIN SEGURO (Lê SENHA_PAINEL dos Secrets no Streamlit Cloud ou usa '1234' em teste local)
def autenticar():
    senha_sistema = st.secrets.get("SENHA_PAINEL", "1234")
    if st.session_state.get("logado", False):
        return True

    st.title("🔒 Central de Acompanhamento - Etapa 1 (Moodle)")
    senha_dig = st.text_input("Digite sua senha de acesso:", type="password")
    if senha_dig:
        if hmac.compare_digest(senha_dig, str(senha_sistema)):
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta.")
    return False

if not autenticar():
    st.stop()

if "base_moodle" not in st.session_state:
    st.session_state["base_moodle"] = pd.DataFrame()

st.title("📚 Etapa 1: Central de Acompanhamento de Atividades (Moodle)")
st.caption("Consolidação das 7 atividades, separação por Instrutor, Turno (Manhã M / Tarde V) e controle de cobrança por e-mail.")

# ==========================================
# ÁREA DE ENTRADA DE DADOS (COLAR OU ARQUIVO)
# ==========================================
with st.expander("📥 Adicionar Dados Extraídos do Moodle (Colar ou Enviar Arquivo)", expanded=st.session_state["base_moodle"].empty):
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        texto_colado = st.text_area(
            "Opção A: Cole (Ctrl+V) o relatório copiado pela Extensão:",
            height=130,
            placeholder="Instrutor\tTurno\tTurma\tAtividade\tStatus\tJovem\tEmail_Enviado"
        )
    with col_in2:
        arquivos_up = st.file_uploader(
            "Opção B: Ou arraste os arquivos (.tsv / .csv) baixados pela Extensão:",
            type=["tsv", "csv", "txt"],
            accept_multiple_files=True
        )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("➕ Processar e Acumular no Painel", type="primary", use_container_width=True):
            novos_dfs = []
            if texto_colado.strip():
                try:
                    novos_dfs.append(pd.read_csv(io.StringIO(texto_colado.strip()), sep="\t"))
                except Exception as e:
                    st.error(f"Erro ao ler texto colado: {e}")

            if arquivos_up:
                for arq in arquivos_up:
                    try:
                        novos_dfs.append(pd.read_csv(arq, sep="\t"))
                    except Exception as e:
                        st.error(f"Erro ao ler arquivo {arq.name}: {e}")

            if novos_dfs:
                df_novo = pd.concat([st.session_state["base_moodle"]] + novos_dfs, ignore_index=True)
                df_novo = df_novo.drop_duplicates(subset=["Turma", "Atividade", "Jovem"], keep="last")
                st.session_state["base_moodle"] = df_novo
                st.success(f"✅ Dados integrados! Total atual: {len(df_novo)} registros.")
                st.rerun()

    with col_btn2:
        if st.button("🗑️ Limpar Base Atual", use_container_width=True):
            st.session_state["base_moodle"] = pd.DataFrame()
            st.rerun()

# ==========================================
# PAINEL DE FILTROS E INDICADORES
# ==========================================
df = st.session_state["base_moodle"]

if not df.empty:
    st.divider()
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        instrutores = ["Todos"] + sorted(df["Instrutor"].dropna().astype(str).unique().tolist())
        sel_instrutor = st.selectbox("👤 Filtrar Instrutor(a):", instrutores)
    with f2:
        turnos = ["Todos"] + sorted(df["Turno"].dropna().astype(str).unique().tolist())
        sel_turno = st.selectbox("🕒 Filtrar Turno (M / V):", turnos)
    with f3:
        df_temp = df.copy()
        if sel_instrutor != "Todos":
            df_temp = df_temp[df_temp["Instrutor"] == sel_instrutor]
        if sel_turno != "Todos":
            df_temp = df_temp[df_temp["Turno"] == sel_turno]
        turmas_disp = ["Todas"] + sorted(df_temp["Turma"].dropna().astype(str).unique().tolist())
        sel_turma = st.selectbox("🏫 Filtrar Turma:", turmas_disp)
    with f4:
        atividades_disp = ["Todas"] + sorted(df_temp["Atividade"].dropna().astype(str).unique().tolist())
        sel_ativ = st.selectbox("📝 Filtrar Atividade:", atividades_disp)

    # Aplicando os filtros
    df_filtrado = df_temp.copy()
    if sel_turma != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Turma"] == sel_turma]
    if sel_ativ != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Atividade"] == sel_ativ]

    # Métricas principais
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Pendências", len(df_filtrado))
    m2.metric("Jovens Únicos Sem Acesso", df_filtrado["Jovem"].nunique())
    m3.metric("☀️ Manhã (M)", len(df_filtrado[df_filtrado["Turno"].astype(str).str.startswith("M")]))
    m4.metric("🌤️ Tarde (V)", len(df_filtrado[df_filtrado["Turno"].astype(str).str.startswith("V")]))

    aba_lista, aba_resumo_jovem = st.tabs(["📋 Lista Completa de Pendências", "⚠️ Ranking por Jovem (Quem deve mais atividades)"])

    with aba_lista:
        busca_nome = st.text_input("🔍 Pesquisar jovem específico pelo nome:")
        df_exibir = df_filtrado[df_filtrado["Jovem"].astype(str).str.contains(busca_nome, case=False, na=False)] if busca_nome else df_filtrado
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    with aba_resumo_jovem:
        resumo_jovens = (
            df_filtrado.groupby(["Jovem", "Turma", "Turno", "Instrutor"])
            .agg(
                Qtd_Atividades_Pendentes=("Atividade", "count"),
                Quais_Atividades=("Atividade", lambda x: " | ".join(x))
            )
            .reset_index()
            .sort_values(by="Qtd_Atividades_Pendentes", ascending=False)
        )
        st.dataframe(resumo_jovens, use_container_width=True, hide_index=True)

    # Botão para salvar em Excel no Google Drive / PC
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_filtrado.to_excel(writer, sheet_name="Pendencias_Detalhadas", index=False)
        resumo_jovens.to_excel(writer, sheet_name="Resumo_Por_Jovem", index=False)

    st.download_button(
        label="💾 Baixar Planilha Consolidada (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Acompanhamento_Moodle_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
