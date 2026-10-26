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
# 1. BANCO DE TURMAS POR INSTRUTOR E TURNO (M / V)
# ==========================================
BANCO_TURMAS = {
    "Guilherme Gomes Bezerra": {
        "M": ["03872.APC09.0M.54", "3872.APC09.0M.100", "3872.APC09.0M.104", "3872.APC09.0M.105", "3872.APC09.0M.106", "3872.APC09.0M.108", "3872.APC09.0M.115", "3872.APC09.0M.52", "3872.APC09.0M.55", "3872.APC09.0M.57", "3872.APC09.0M.71", "3872.APC09.0M.74", "3872.APC09.0M.76", "3872.APC09.0M.78", "3872.APC09.0M.85", "3872.APC09.0M.89", "3872.APC09.0M.91", "3872.APC09.0M.92", "3872.APC09.0M.94", "3872.APC09.0M.96", "3872.APC09.0M.97", "3872.APC09.0M.98", "3872.APC09.1M.71", "4.0.APC02.2M.91", "4.0.APC02.3M.91", "4.0.APC02.4M.91", "4.0.APC02.5M.91", "4.0.APC09.0M.91", "4.APC02.2M.54", "4.APC02.2M.71", "4.APC02.2M.85", "4.APC02.3M.100", "4.APC02.3M.74", "4.APC02.3M.78", "4.APC02.3M.79", "4.APC02.3M.89", "4.APC02.4M.100", "4.APC02.4M.103", "4.APC02.4M.71", "4.APC02.4M.98", "4.APC02.5M.100", "4.APC09.0M.71", "671.APC09.0M.105", "671.APC09.0M.106", "671.APC09.0M.54", "671.APC09.0M.71", "671.APC09.0M.74", "671.APC09.0M.78", "671.APC09.0M.85", "671.APC09.0M.91", "671.APC09.0M.97"],
        "V": ["3872.APC09.0V.01", "3872.APC09.0V.100", "3872.APC09.0V.104", "3872.APC09.0V.105", "3872.APC09.0V.106", "3872.APC09.0V.108", "3872.APC09.0V.115", "3872.APC09.0V.52", "3872.APC09.0V.54", "3872.APC09.0V.55", "3872.APC09.0V.57", "3872.APC09.0V.71", "3872.APC09.0V.74", "3872.APC09.0V.76", "3872.APC09.0V.78", "3872.APC09.0V.85", "3872.APC09.0V.89", "3872.APC09.0V.91", "3872.APC09.0V.94", "3872.APC09.0V.96", "3872.APC09.0V.97", "3872.APC09.0V.98", "4.0.APC02.2V.91", "4.0.APC02.3V.91", "4.0.APC02.4V.91", "4.0.APC02.5V.91", "4.0.APC09.0V.91", "4.APC02.2V.100", "4.APC02.2V.71", "4.APC02.2V.85", "4.APC02.2V.94", "4.APC02.3V.100", "4.APC02.3V.103", "4.APC02.3V.78", "4.APC02.4V.100", "4.APC02.4V.103", "4.APC02.4V.71", "4.APC02.4V.74", "4.APC02.4V.96", "4.APC09.0V.78", "671.APC09.0V.106", "671.APC09.0V.54", "671.APC09.0V.71", "671.APC09.0V.74", "671.APC09.0V.78", "671.APC09.0V.85", "671.APC09.0V.91", "671.APC09.0V.96"]
    },
    "Cleonice Algarves": {
        "M": ["3872.APC02.2M.100", "3872.APC02.2M.103", "3872.APC02.2M.108", "3872.APC02.2M.113", "3872.APC02.2M.52", "3872.APC02.2M.54", "3872.APC02.2M.71", "3872.APC02.2M.85", "3872.APC02.2M.89", "3872.APC02.2M.91", "3872.APC02.2M.96", "3872.APC02.2M.98", "3872.APC02.3M.104", "3872.APC02.3M.96", "3872.APC02.4M.100", "3872.APC02.4M.113", "3872.APC02.4M.52", "3872.APC02.4M.54", "3872.APC02.4M.57", "3872.APC02.4M.85", "3872.APC02.4M.94", "3872.APC02.4M.96", "3872.APC02.6M.106"],
        "V": ["3872.APC02.2V.100", "3872.APC02.2V.104", "3872.APC02.2V.106", "3872.APC02.2V.108", "3872.APC02.2V.71", "3872.APC02.2V.78", "3872.APC02.2V.85", "3872.APC02.2V.89", "3872.APC02.2V.91", "3872.APC02.2V.98", "3872.APC02.3V.104", "3872.APC02.3V.52", "3872.APC02.3V.54", "3872.APC02.3V.96", "3872.APC02.4V.100", "3872.APC02.4V.103", "3872.APC02.4V.113", "3872.APC02.4V.54", "3872.APC02.4V.85", "3872.APC02.4V.96", "3872.APC02.4V.98", "3872.APC02.6V.106"]
    },
    "Fernanda Altino": {
        "M": ["3872.APC00.0M.103", "3872.APC00.0M.107", "3872.APC00.0M.109", "3872.APC00.0M.114", "3872.APC00.0M.53", "3872.APC00.0M.55", "3872.APC00.0M.58", "3872.APC00.0M.72", "3872.APC00.0M.75", "3872.APC00.0M.79", "3872.APC00.0M.86", "3872.APC00.0M.90", "3872.APC00.0M.93", "3872.APC00.0M.95", "3872.APC00.0M.96", "3872.APC00.0M.99"],
        "V": ["3872.APC00.0V.103", "3872.APC00.0V.107", "3872.APC00.0V.109", "3872.APC00.0V.113", "3872.APC00.0V.53", "3872.APC00.0V.55", "3872.APC00.0V.58", "3872.APC00.0V.72", "3872.APC00.0V.75", "3872.APC00.0V.79", "3872.APC00.0V.86", "3872.APC00.0V.90", "3872.APC00.0V.93", "3872.APC00.0V.96", "3872.APC00.0V.99"]
    },
    "Glaucineia Santos": {
        "M": ["3872.APC00.0M.105", "3872.APC00.0M.106", "3872.APC00.0M.52", "3872.APC00.0M.57", "3872.APC00.0M.73", "3872.APC00.0M.74", "3872.APC00.0M.76", "3872.APC00.0M.78", "3872.APC00.0M.89", "3872.APC00.0M.91", "3872.APC00.0M.97", "3872.APC00.0M.98"],
        "V": ["3872.APC00.0V.100", "3872.APC00.0V.104", "3872.APC00.0V.105", "3872.APC00.0V.116", "3872.APC00.0V.52", "3872.APC00.0V.54", "3872.APC00.0V.78", "3872.APC00.0V.89", "3872.APC00.0V.98"]
    },
    "Kleyton Figueiredo": {
        "M": ["3872.APC01.2M.101", "3872.APC01.2M.105", "3872.APC01.2M.107", "3872.APC01.2M.108", "3872.APC01.2M.54", "3872.APC01.2M.57", "3872.APC01.2M.71", "3872.APC01.2M.85", "3872.APC01.2M.91", "3872.APC01.2M.94", "3872.APC01.2M.97", "3872.APC01.4M.110", "3872.APC01.4M.113", "3872.APC01.4M.55", "3872.APC01.4M.86", "3872.APC01.5M.101", "3872.APC01.5M.85", "3872.APC01.5M.98", "671.APC01.2M.74", "671.APC01.4M.72"],
        "V": ["3872.APC01.2V.101", "3872.APC01.2V.108", "3872.APC01.2V.113", "3872.APC01.2V.54", "3872.APC01.2V.71", "3872.APC01.2V.78", "3872.APC01.2V.85", "3872.APC01.2V.89", "3872.APC01.2V.91", "3872.APC01.2V.97", "3872.APC01.4V.108", "3872.APC01.4V.110", "3872.APC01.4V.113", "3872.APC01.4V.55", "3872.APC01.4V.86", "3872.APC01.5V.101", "3872.APC01.5V.106", "3872.APC01.5V.85", "3872.APC01.5V.98"]
    },
    "Luciana Medrado": {
        "M": ["3872.APC01.2M.104", "3872.APC01.2M.52", "3872.APC01.2M.55", "3872.APC01.2M.90", "3872.APC01.4M.104", "3872.APC01.4M.106", "3872.APC01.4M.109", "3872.APC01.4M.115", "3872.APC01.4M.54", "3872.APC01.4M.72", "3872.APC01.4M.76", "3872.APC01.4M.85", "3872.APC01.4M.89", "3872.APC01.4M.92", "3872.APC01.4M.94", "3872.APC01.4M.97", "671.APC01.4M.113"],
        "V": ["3872.APC01.2V.104", "3872.APC01.2V.106", "3872.APC01.2V.96", "3872.APC01.4V.101", "3872.APC01.4V.103", "3872.APC01.4V.104", "3872.APC01.4V.109", "3872.APC01.4V.85", "3872.APC01.4V.89", "3872.APC01.4V.92", "3872.APC01.4V.96", "671.APC01.4V.101"]
    },
    "Marla Barbosa": {
        "M": ["3872.APC00.0M.100", "3872.APC00.0M.108", "3872.APC00.0M.114", "3872.APC00.0M.115", "3872.APC00.0M.116", "3872.APC00.0M.54", "3872.APC00.0M.85", "3872.APC00.0M.94"],
        "V": ["3872.APC00.0V.106", "3872.APC00.0V.108", "3872.APC00.0V.57", "3872.APC00.0V.71", "3872.APC00.0V.74", "3872.APC00.0V.76", "3872.APC00.0V.85", "3872.APC00.0V.91", "3872.APC00.0V.94", "3872.APC00.0V.97"]
    },
    "Nibson Lima": {
        "M": ["4.0.APC02.2M.91", "4.0.APC02.3M.91", "4.0.APC02.4M.91", "4.APC02.2M.71", "4.APC02.2M.85", "4.APC02.4M.100", "4.APC02.4M.103", "4.APC02.4M.71", "671.APC.02.4M.100", "671.APC02.2M.54", "671.APC02.2M.71", "671.APC02.2M.91", "671.APC02.2M.96", "671.APC02.2M.98", "671.APC02.3M.100", "671.APC02.3M.78", "671.APC02.4M.104", "671.APC02.4M.106", "671.APC02.4M.108", "671.APC02.4M.54", "671.APC02.4M.71", "671.APC02.4M.74", "671.APC02.4M.76", "671.APC02.4M.85", "671.APC02.4M.92", "671.APC02.4M.97"],
        "V": ["4.0.APC02.2V.91", "4.0.APC02.3V.91", "4.0.APC02.4V.91", "4.APC02.2V.100", "4.APC02.2V.85", "4.APC02.2V.94", "4.APC02.3V.78", "4.APC02.4V.100", "4.APC02.4V.71", "4.APC02.4V.96", "671.APC.02.4V.100", "671.APC02.2V.100", "671.APC02.2V.104", "671.APC02.2V.106", "671.APC02.2V.71", "671.APC02.2V.78", "671.APC02.2V.91", "671.APC02.2V.96", "671.APC02.2V.98", "671.APC02.3V.106", "671.APC02.3V.71", "671.APC02.3V.78", "671.APC02.3V.96", "671.APC02.4V.104", "671.APC02.4V.54", "671.APC02.4V.71", "671.APC02.4V.78", "671.APC02.4V.85", "671.APC02.4V.97", "671.APC02.4V.98", "671.APC02.5V.71"]
    }
}

def extrair_turno(cod_turma):
    c = str(cod_turma).upper()
    if "M." in c:
        return "M - Manhã"
    if "V." in c:
        return "V - Tarde"
    return "Outro"

# ==========================================
# 2. AUTENTICAÇÃO SEGURA (VIA SECRETS)
# ==========================================
def verificar_senha():
    if "SENHA_PAINEL" not in st.secrets:
        st.error("⚠️ Configure 'SENHA_PAINEL' em Settings > Secrets no Streamlit Cloud.")
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
# 3. BARRA LATERAL: INSTRUTOR + TURNO (M/V)
# ==========================================
with st.sidebar:
    st.header("⚙️ Filtro de Instrutor e Turno")
    opcoes_instrutor = list(BANCO_TURMAS.keys()) + ["Todos os Instrutores"]
    instrutor_sel = st.selectbox("Instrutor(a):", options=opcoes_instrutor, index=0)
    turno_sel = st.radio("Turno:", options=["Todos (M + V)", "☀️ Manhã (M)", "🌤️ Tarde (V)"], horizontal=True)

    turmas_base = []
    if instrutor_sel == "Todos os Instrutores":
        for d in BANCO_TURMAS.values():
            if turno_sel in ["Todos (M + V)", "☀️ Manhã (M)"]:
                turmas_base.extend(d["M"])
            if turno_sel in ["Todos (M + V)", "🌤️ Tarde (V)"]:
                turmas_base.extend(d["V"])
    else:
        if turno_sel in ["Todos (M + V)", "☀️ Manhã (M)"]:
            turmas_base.extend(BANCO_TURMAS[instrutor_sel]["M"])
        if turno_sel in ["Todos (M + V)", "🌤️ Tarde (V)"]:
            turmas_base.extend(BANCO_TURMAS[instrutor_sel]["V"])

    turmas_texto = st.text_area(
        f"Turmas Ativas ({len(turmas_base)} selecionadas):",
        value="\n".join(turmas_base),
        height=150
    )
    minhas_turmas = [t.strip() for t in turmas_texto.split("\n") if t.strip()]
    filtrar_minhas = st.checkbox("Filtrar apenas as turmas listadas acima", value=True)

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
# 4. ABAS PRINCIPAIS
# ==========================================
st.title("📊 Central de Acompanhamento Unificado")
st.caption(f"Filtro Ativo: **{instrutor_sel}** | Turno: **{turno_sel}** ({len(minhas_turmas)} turmas monitoradas)")

tab1, tab2, tab3, tab4 = st.tabs([
    "📅 1. Faltas (SharePoint ➔ RM)",
    "📚 2. Atividades (Moodle Demà)",
    "📝 3. Avaliação de Desempenho (RM)",
    "🎯 4. Visão 360º do Jovem"
])

# ABA 1: FALTAS
with tab1:
    st.subheader("📅 Consolidador de Faltas Diárias (Separado por M / V)")
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
            df["Turma"] = df["Turma"].astype(str).str.strip()
            df["Turno"] = df["Turma"].apply(extrair_turno)
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
            if filtrar_minhas and minhas_turmas:
                padrao = "|".join([t.lstrip("0") for t in minhas_turmas])
                df_f_total = df_f_total[df_f_total["Turma"].str.contains(padrao, case=False, na=False)]
            st.session_state["df_faltas"] = df_f_total

    if "df_faltas" in st.session_state and not st.session_state["df_faltas"].empty:
        df_f = st.session_state["df_faltas"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Ausentes", len(df_f))
        c2.metric("☀️ Manhã (M)", len(df_f[df_f["Turno"] == "M - Manhã"]))
        c3.metric("🌤️ Tarde (V)", len(df_f[df_f["Turno"] == "V - Tarde"]))
        c4.metric("Turmas c/ Faltas", df_f["Turma"].nunique())

        turma_f = st.selectbox("Selecione a Turma para lançar no Diário de Classe RM:", ["Todas"] + sorted(df_f["Turma"].unique().tolist()))
        df_v = df_f if turma_f == "Todas" else df_f[df_f["Turma"] == turma_f].copy()
        if "Lançado_RM" not in df_v.columns:
            df_v.insert(0, "Lançado_RM", False)
        st.data_editor(
            df_v[["Lançado_RM", "Turno", "Turma", "ID_Jovem", "Nome", "Email", "Encontro", "Modulo_Unidade", "Data"]],
            use_container_width=True,
            hide_index=True
        )

# ABA 2: MOODLE
with tab2:
    st.subheader("📚 Relatório de Pendências e Envios do Moodle (Com Turno M / V)")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        entrada_moodle = st.text_area(
            "Cole aqui o relatório copiado pela Extensão do Moodle:",
            height=110,
            placeholder="Instrutor\tTurno\tTurma\tAtividade\tStatus\tNome\tEmail_Enviado"
        )
    with col_m2:
        arq_moodle = st.file_uploader("Ou envie o arquivo relatorio_moodle.tsv baixado:", type=["tsv", "csv", "txt"])

    if arq_moodle:
        st.session_state["df_moodle"] = pd.read_csv(arq_moodle, sep="\t")
    elif entrada_moodle:
        try:
            st.session_state["df_moodle"] = pd.read_csv(io.StringIO(entrada_moodle), sep="\t")
        except Exception as e:
            st.error(f"Erro ao ler relatório: {e}")

    if "df_moodle" in st.session_state and not st.session_state["df_moodle"].empty:
        df_m = st.session_state["df_moodle"].copy()
        if "Turno" not in df_m.columns and "Turma" in df_m.columns:
            df_m["Turno"] = df_m["Turma"].apply(extrair_turno)

        cm1, cm2, cm3, cm4 = st.columns(4)
        cm1.metric("Total de Pendências", len(df_m))
        cm2.metric("☀️ Pendências Manhã (M)", len(df_m[df_m["Turno"].astype(str).str.startswith("M")]))
        cm3.metric("🌤️ Pendências Tarde (V)", len(df_m[df_m["Turno"].astype(str).str.startswith("V")]))
        cm4.metric("Jovens Únicos Sem Acesso", df_m["Nome"].nunique())

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f_turno_m = st.selectbox("Filtrar Turno (Moodle):", ["Todos", "M - Manhã", "V - Tarde"])
        with f_col2:
            f_turma_m = st.selectbox("Filtrar Turma (Moodle):", ["Todas"] + sorted(df_m["Turma"].astype(str).unique().tolist()))

        df_m_show = df_m.copy()
        if f_turno_m != "Todos":
            df_m_show = df_m_show[df_m_show["Turno"] == f_turno_m]
        if f_turma_m != "Todas":
            df_m_show = df_m_show[df_m_show["Turma"] == f_turma_m]

        st.dataframe(df_m_show, use_container_width=True, hide_index=True)

# ABA 3: AVALIAÇÃO RM
with tab3:
    st.subheader("📝 Curadoria da Avaliação de Desempenho (RM)")
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        entrada_rm = st.text_area("Cole os dados do Coletor RM:", height=110, placeholder="STATUS_PROVA\tSTATUS_PERIODO...")
    with col_up2:
        arq_rm = st.file_uploader("Ou envie o arquivo avaliacao_rm.tsv baixado:", type=["tsv", "csv", "txt"])

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
                st.dataframe(d[d["Nome"].astype(str).str.contains(busca, case=False, na=False) | d["Turma"].astype(str).str.contains(busca, case=False, na=False)][["Turno", "Nome", "Turma", "Data"]], hide_index=True)
        with cb:
            st.markdown("#### 📚 Moodle")
            if "df_moodle" in st.session_state:
                d = st.session_state["df_moodle"]
                st.dataframe(d[d["Nome"].astype(str).str.contains(busca, case=False, na=False) | d["Turma"].astype(str).str.contains(busca, case=False, na=False)][["Turno", "Nome", "Turma", "Atividade"]], hide_index=True)
        with cc:
            st.markdown("#### 📝 Avaliação RM")
            if "df_rm" in st.session_state:
                d = st.session_state["df_rm"]
                c_nome = "NOME" if "NOME" in d.columns else d.columns[-2]
                st.dataframe(d[d[c_nome].astype(str).str.contains(busca, case=False, na=False)][[c_nome, d.columns[0], "NOMEPERIODO", "CODIGO_ACESSO"]], hide_index=True)
