import streamlit as st
import pandas as pd
import io
import zipfile
import hmac
from datetime import datetime

st.set_page_config(
    page_title="Central de Acompanhamento - Painel Unificado",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 1. AUTENTICAÇÃO SEGURA (SEM SENHA NO CÓDIGO)
# ==========================================
def verificar_senha():
    if "SENHA_PAINEL" not in st.secrets:
        st.error("⚠️ Configure a variável 'SENHA_PAINEL' em Settings > Secrets no Streamlit Cloud.")
        st.stop()

    def validar():
        if hmac.compare_digest(st.session_state.get("senha_digitada", ""), st.secrets["SENHA_PAINEL"]):
            st.session_state["autenticado"] = True
            del st.session_state["senha_digitada"]
        else:
            st.session_state["autenticado"] = False

    if st.session_state.get("autenticado", False):
        return True

    st.title("🔒 Acesso Restrito - Central de Acompanhamento")
    st.text_input("Digite sua chave de acesso:", type="password", on_change=validar, key="senha_digitada")
    if "autenticado" in st.session_state and not st.session_state["autenticado"]:
        st.error("❌ Senha incorreta.")
    return False

if not verificar_senha():
    st.stop()

# ==========================================
# 2. BARRA LATERAL: TURMAS VIA SECRETS + BACKUP
# ==========================================
with st.sidebar:
    st.header("⚙️ Minhas Turmas")
    turmas_secret = st.secrets.get("MINHAS_TURMAS", "")
    turmas_texto = st.text_area(
        "Códigos das suas turmas (1 por linha):",
        value=turmas_secret,
        height=170,
        placeholder="Cole os códigos das suas turmas aqui..."
    )
    minhas_turmas = [t.strip() for t in turmas_texto.split("\n") if t.strip()]
    filtrar_minhas = st.checkbox("Filtrar apenas minhas turmas", value=True)

    st.divider()
    st.subheader("☁️ Sincronização Google Drive")

    if any(k in st.session_state for k in ["df_faltas", "df_moodle", "df_rm"]):
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
            if "df_faltas" in st.session_state:
                st.session_state["df_faltas"].to_excel(writer, sheet_name="Faltas", index=False)
            if "df_moodle" in st.session_state:
                st.session_state["df_moodle"].to_excel(writer, sheet_name="Moodle", index=False)
            if "df_rm" in st.session_state:
                st.session_state["df_rm"].to_excel(writer, sheet_name="Avaliacao_RM", index=False)

        st.download_button(
            label="💾 Salvar Base Unificada (.xlsx)",
            data=buffer_excel.getvalue(),
            file_name=f"Painel_Unificado_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    backup_up = st.file_uploader("Restaurar Base do Google Drive (.xlsx):", type=["xlsx"])
    if backup_up:
        xls = pd.ExcelFile(backup_up)
        if "Faltas" in xls.sheet_names:
            st.session_state["df_faltas"] = pd.read_excel(xls, "Faltas")
        if "Moodle" in xls.sheet_names:
            st.session_state["df_moodle"] = pd.read_excel(xls, "Moodle")
        if "Avaliacao_RM" in xls.sheet_names:
            st.session_state["df_rm"] = pd.read_excel(xls, "Avaliacao_RM")
        st.success("Histórico carregado!")

# ==========================================
# 3. PAINEL PRINCIPAL
# ==========================================
st.title("📊 Central de Acompanhamento Unificado")

tab1, tab2, tab3, tab4 = st.tabs([
    "📅 1. Faltas (SharePoint ➔ RM)",
    "📚 2. Atividades (Moodle Demà)",
    "📝 3. Avaliação de Desempenho (RM)",
    "🎯 4. Visão 360º do Jovem"
])

# ABA 1: FALTAS
with tab1:
    st.subheader("📅 Consolidador de Faltas Diárias (MAT / VES)")
    arquivos_faltas = st.file_uploader(
        "Arraste o pacote .ZIP baixado da pasta MAT/VES do SharePoint ou as planilhas (.xls / .xlsx):",
        type=["xls", "xlsx", "zip"],
        accept_multiple_files=True
    )

    def ler_falta(bytes_arq, nome_arq):
        try:
            ext = nome_arq.lower().split(".")[-1]
            engine = "xlrd" if ext == "xls" else "openpyxl"
            df_b = pd.read_excel(io.BytesIO(bytes_arq), header=None, engine=engine)
            mapa = {
                0: "ID_Jovem", 1: "Nome", 2: "Email", 3: "Modulo_Unidade",
                5: "Cidade_UF", 7: "Encontro", 9: "Turma", 11: "Data"
            }
            cols = [c for c in mapa.keys() if c < df_b.shape[1]]
            df = df_b[cols].rename(columns=mapa).dropna(subset=["Nome", "Turma"], how="any")
            df["Planilha_Origem"] = nome_arq
            return df
        except Exception:
            return pd.DataFrame()

    if arquivos_faltas:
        lista = []
        for arq in arquivos_faltas:
            if arq.name.lower().endswith(".zip"):
                with zipfile.ZipFile(arq, "r") as z:
                    for item in z.namelist():
                        if item.lower().endswith((".xls", ".xlsx")) and not item.startswith("__MACOSX"):
                            df_t = ler_falta(z.read(item), item.split("/")[-1])
                            if not df_t.empty:
                                lista.append(df_t)
            else:
                df_t = ler_falta(arq.read(), arq.name)
                if not df_t.empty:
                    lista.append(df_t)

        if lista:
            df_f_total = pd.concat(lista, ignore_index=True)
            df_f_total["Turma"] = df_f_total["Turma"].astype(str).str.strip()
            if filtrar_minhas and minhas_turmas:
                padrao = "|".join([t.lstrip("0") for t in minhas_turmas])
                df_f_total = df_f_total[df_f_total["Turma"].str.contains(padrao, case=False, na=False)]
            st.session_state["df_faltas"] = df_f_total

    if "df_faltas" in st.session_state and not st.session_state["df_faltas"].empty:
        df_f = st.session_state["df_faltas"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Jovens Ausentes", len(df_f))
        c2.metric("Suas Turmas com Ausências", df_f["Turma"].nunique())
        c3.metric("Planilhas c/ Ocorrências", df_f["Planilha_Origem"].nunique())

        turma_f = st.selectbox("Filtrar Turma para lançar no Diário de Classe RM:", ["Todas"] + sorted(df_f["Turma"].unique().tolist()))
        df_v = df_f if turma_f == "Todas" else df_f[df_f["Turma"] == turma_f].copy()
        if "Lançado_RM" not in df_v.columns:
            df_v.insert(0, "Lançado_RM", False)
        st.data_editor(df_v, use_container_width=True, hide_index=True)

# ABA 2: MOODLE
with tab2:
    st.subheader("📚 Relatório de Pendências e Envios do Moodle")
    entrada_moodle = st.text_area(
        "Cole aqui o relatório copiado pelo botão da Extensão do Moodle:",
        height=120,
        placeholder="Turma\tAtividade\tStatus\tNome\tEmail_Enviado"
    )
    if entrada_moodle:
        try:
            st.session_state["df_moodle"] = pd.read_csv(io.StringIO(entrada_moodle), sep="\t")
        except Exception as e:
            st.error(f"Formato inválido: {e}")

    if "df_moodle" in st.session_state and not st.session_state["df_moodle"].empty:
        df_m = st.session_state["df_moodle"]
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric("Total de Pendências", len(df_m))
        cm2.metric("Jovens Únicos Sem Acesso", df_m["Nome"].nunique())
        cm3.metric("Turmas Monitoradas", df_m["Turma"].nunique())

        t_moodle = st.selectbox("Filtrar Turma (Moodle):", ["Todas"] + sorted(df_m["Turma"].unique().tolist()))
        df_m_show = df_m if t_moodle == "Todas" else df_m[df_m["Turma"] == t_moodle]
        st.dataframe(df_m_show, use_container_width=True, hide_index=True)

# ABA 3: AVALIAÇÃO RM
with tab3:
    st.subheader("📝 Curadoria da Avaliação de Desempenho (RM)")
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        entrada_rm = st.text_area("Cole os dados do Coletor RM:", height=110, placeholder="STATUS_PROVA\tSTATUS_PERIODO...")
    with col_up2:
        arq_rm = st.file_uploader("Ou envie o arquivo avaliacao_rm.tsv baixado pelo Coletor:", type=["tsv", "csv", "txt"])

    if arq_rm:
        st.session_state["df_rm"] = pd.read_csv(arq_rm, sep="\t")
    elif entrada_rm:
        try:
            st.session_state["df_rm"] = pd.read_csv(io.StringIO(entrada_rm), sep="\t")
        except Exception as e:
            st.error(f"Erro ao ler dados: {e}")

    if "df_rm" in st.session_state and not st.session_state["df_rm"].empty:
        df_r = st.session_state["df_rm"]
        col_st = df_r.columns[0]
        status_disp = df_r[col_st].dropna().unique().tolist()
        padrao_st = [s for s in status_disp if str(s).upper() != "FINALIZADO"]

        f_st = st.multiselect("Filtrar STATUS_PROVA:", options=status_disp, default=padrao_st)
        df_r_show = df_r[df_r[col_st].isin(f_st)]

        cr1, cr2, cr3 = st.columns(3)
        cr1.metric("Total na Consulta", len(df_r))
        cr2.metric("Pendentes / Em Andamento", len(df_r_show))
        cr3.metric("Finalizados", len(df_r) - len(df_r_show))

        st.dataframe(df_r_show, use_container_width=True, hide_index=True)

# ABA 4: VISÃO 360º
with tab4:
    st.subheader("🎯 Cruzamento 360º por Jovem ou Turma")
    busca = st.text_input("🔍 Digite o nome do jovem ou código da turma:")
    if busca:
        ca, cb, cc = st.columns(3)
        with ca:
            st.markdown("#### 📅 Faltas")
            if "df_faltas" in st.session_state:
                d = st.session_state["df_faltas"]
                st.dataframe(d[d["Nome"].astype(str).str.contains(busca, case=False, na=False) | d["Turma"].astype(str).str.contains(busca, case=False, na=False)][["Nome", "Turma", "Data"]], hide_index=True)
        with cb:
            st.markdown("#### 📚 Moodle")
            if "df_moodle" in st.session_state:
                d = st.session_state["df_moodle"]
                st.dataframe(d[d["Nome"].astype(str).str.contains(busca, case=False, na=False) | d["Turma"].astype(str).str.contains(busca, case=False, na=False)][["Nome", "Turma", "Atividade"]], hide_index=True)
        with cc:
            st.markdown("#### 📝 Avaliação RM")
            if "df_rm" in st.session_state:
                d = st.session_state["df_rm"]
                c_nome = "NOME" if "NOME" in d.columns else d.columns[-2]
                st.dataframe(d[d[c_nome].astype(str).str.contains(busca, case=False, na=False)][[c_nome, d.columns[0], "NOMEPERIODO", "CODIGO_ACESSO"]], hide_index=True)