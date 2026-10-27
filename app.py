import streamlit as st
import pandas as pd
import io
import re
import zipfile
import hmac
from datetime import datetime, date

st.set_page_config(
    page_title="Central do Instrutor - Moodle & Faltas",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 1. BANCO DE TURMAS DOS 8 INSTRUTORES (M e V)
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

# Mapa reverso rápido: codigo_sem_zero -> Instrutor
MAPA_TURMA_INSTRUTOR = {}
for inst, turnos in BANCO_TURMAS.items():
    for cod in turnos["M"] + turnos["V"]:
        MAPA_TURMA_INSTRUTOR[cod.lstrip("0").upper()] = inst

def identificar_instrutor(cod_turma):
    limpo = str(cod_turma).strip().lstrip("0").upper()
    return MAPA_TURMA_INSTRUTOR.get(limpo, "Outro / Não Mapeado")

def identificar_turno(cod_turma, nome_arq=""):
    c = str(cod_turma).upper()
    if "M." in c:
        return "M - Manhã"
    if "V." in c:
        return "V - Tarde"
    n = str(nome_arq).upper()
    if "_M." in n or "/MAT/" in n:
        return "M - Manhã"
    if "_V." in n or "/VES/" in n:
        return "V - Tarde"
    return "Outro"

def identificar_unidade(texto_mod_arq):
    t = str(texto_mod_arq).upper()
    if "UB" in t:
        return "UB - Bojador"
    if "UA" in t:
        return "UA - Áurea"
    if "UC" in t:
        return "UC - Cerrado"
    if "UM" in t:
        return "UM - Missões"
    return "Outra Unidade"

def extrair_data_nome_arquivo(nome_arq, data_fallback):
    m = re.search(r"(\d{2})[-.](\d{2})[-.](\d{4})", str(nome_arq))
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return data_fallback

# ==========================================
# 2. LOGIN SEGURO
# ==========================================
def autenticar():
    senha_sistema = st.secrets.get("SENHA_PAINEL", "1234")
    if st.session_state.get("logado", False):
        return True
    st.title("🔒 Central de Acompanhamento Unificado")
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
if "base_faltas" not in st.session_state:
    st.session_state["base_faltas"] = pd.DataFrame()

# ==========================================
# 3. BARRA LATERAL: FILTRO GLOBAL + BACKUP UNIFICADO
# ==========================================
with st.sidebar:
    st.header("🎯 Filtros Globais")
    opcoes_inst = ["Todos"] + list(BANCO_TURMAS.keys()) + ["Outro / Não Mapeado"]
    filtro_global_inst = st.selectbox("👤 Instrutor(a):", opcoes_inst, index=1) # Padrão: Guilherme
    filtro_global_turno = st.selectbox("🕒 Turno (M / V):", ["Todos", "M - Manhã", "V - Tarde"])

    st.divider()
    st.header("🗄️ Base Histórica Unificada")
    st.caption("Salva e carrega tanto os dados do **Moodle (Etapa 1)** quanto as **Faltas (Etapa 2)** no mesmo arquivo Excel:")

    arq_hist = st.file_uploader("📂 Carregar Histórico Salvo (.xlsx):", type=["xlsx"])
    if arq_hist and st.button("🔄 Restaurar Histórico", use_container_width=True):
        try:
            xls = pd.ExcelFile(arq_hist)
            if "Historico_Moodle" in xls.sheet_names:
                df_m = pd.read_excel(xls, "Historico_Moodle")
                st.session_state["base_moodle"] = pd.concat([st.session_state["base_moodle"], df_m], ignore_index=True).drop_duplicates(
                    subset=["Data_Coleta", "Turma", "Atividade", "Jovem"], keep="last"
                )
            if "Historico_Faltas" in xls.sheet_names:
                df_f = pd.read_excel(xls, "Historico_Faltas")
                st.session_state["base_faltas"] = pd.concat([st.session_state["base_faltas"], df_f], ignore_index=True).drop_duplicates(
                    subset=["Data_Falta", "Turma", "ID_Jovem", "Jovem"], keep="last"
                )
            st.success("✅ Histórico restaurado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao restaurar arquivo: {e}")

    if not st.session_state["base_moodle"].empty or not st.session_state["base_faltas"].empty:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            if not st.session_state["base_moodle"].empty:
                st.session_state["base_moodle"].to_excel(writer, sheet_name="Historico_Moodle", index=False)
            if not st.session_state["base_faltas"].empty:
                st.session_state["base_faltas"].to_excel(writer, sheet_name="Historico_Faltas", index=False)

        st.download_button(
            label="💾 Salvar Histórico Completo (.xlsx)",
            data=buf.getvalue(),
            file_name=f"Historico_Central_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

# ==========================================
# 4. NAVEGAÇÃO PRINCIPAL: ETAPA 1 E ETAPA 2
# ==========================================
st.title("📊 Central de Acompanhamento e Automação")

modulo_principal = st.tabs([
    "📅 ETAPA 2: Controle de Faltas (SharePoint ➔ RM)",
    "📚 ETAPA 1: Atividades Não Realizadas (Moodle)"
])

# ==============================================================================
# MÓDULO ETAPA 2: CONTROLE DE FALTAS (SHAREPOINT -> RM)
# ==============================================================================
with modulo_principal[0]:
    st.subheader("📅 Etapa 2: Consolidador de Faltas Diárias, Semanais e Mensais")
    st.markdown(
        "No SharePoint (`FALTAS > 2026 > MÊS > DIA`), clique em **Baixar** para obter o `.zip` do dia "
        "(com as pastas `MAT` e `VES` completas) ou selecione várias planilhas `.xls`/`.xlsx`."
    )

    def ler_planilha_falta_segura(bytes_arq, nome_arq, data_padrao_str):
        # Ignora arquivos vazios de 810 bytes ou temporários do Excel
        if len(bytes_arq) < 900 or nome_arq.startswith("~$"):
            return pd.DataFrame()

        df_raw = None
        ext = nome_arq.lower().split(".")[-1]
        engines = ["xlrd", "openpyxl"] if ext == "xls" else ["openpyxl", "xlrd"]

        for eng in engines:
            try:
                df_raw = pd.read_excel(io.BytesIO(bytes_arq), header=None, engine=eng)
                break
            except Exception:
                continue

        if df_raw is None or df_raw.empty or df_raw.shape[1] < 10:
            return pd.DataFrame()

        # Mapeamento exato conforme imagem 1.6.png:
        # Col A (0): ID_Jovem | Col B (1): Jovem | Col C (2): Email | Col D (3): Modulo_Sigla
        # Col F (5): Cidade_UF | Col H (7): Encontro | Col J (9): Turma | Col L (11): Data_Cadastro
        mapa = {
            0: "ID_Jovem",
            1: "Jovem",
            2: "Email",
            3: "Modulo_Sigla",
            5: "Cidade_UF",
            7: "Encontro",
            9: "Turma",
            11: "Data_Col_L"
        }
        cols_presentes = [c for c in mapa.keys() if c < df_raw.shape[1]]
        df = df_raw[cols_presentes].rename(columns=mapa).copy()

        # Remove linhas em branco ou cabeçalhos eventuais (exige que Turma tenha '.' ou números e Jovem exista)
        df = df.dropna(subset=["Jovem", "Turma"], how="any")
        df["Turma"] = df["Turma"].astype(str).str.strip()
        df["Jovem"] = df["Jovem"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        df = df[df["Turma"].str.contains(r"\.|APC|\d", case=False, na=False)]
        df = df[~df["Turma"].str.upper().isin(["TURMA", "CODTURMA", "NAN"])]

        if df.empty:
            return pd.DataFrame()

        nome_limpo = nome_arq.split("/")[-1]
        data_falta = extrair_data_nome_arquivo(nome_limpo, data_padrao_str)

        df["Data_Falta"] = data_falta
        df["Mes_Ano"] = data_falta[:7]
        df["Turno"] = df["Turma"].apply(lambda t: identificar_turno(t, nome_arq))
        df["Instrutor"] = df["Turma"].apply(identificar_instrutor)
        df["Unidade"] = df["Modulo_Sigla"].fillna(nome_limpo).apply(identificar_unidade)
        df["Arquivo_Origem"] = nome_limpo
        df["Lancado_RM"] = False

        colunas_ordem = [
            "Lancado_RM", "Data_Falta", "Mes_Ano", "Instrutor", "Turno",
            "Unidade", "Turma", "ID_Jovem", "Jovem", "Email",
            "Encontro", "Modulo_Sigla", "Cidade_UF", "Arquivo_Origem"
        ]
        return df[[c for c in colunas_ordem if c in df.columns]]

    with st.expander("📥 Importar Pacote .ZIP de Faltas (MAT / VES) ou Planilhas (.xls / .xlsx)", expanded=st.session_state["base_faltas"].empty):
        c_up1, c_up2 = st.columns([1, 2])
        with c_up1:
            data_ref_falta = st.date_input(
                "📅 Data de referência (caso o arquivo não tenha data no nome):",
                value=date.today(),
                format="DD/MM/YYYY",
                key="dt_falta"
            )
        with c_up2:
            arqs_faltas = st.file_uploader(
                "Arraste o(s) arquivo(s) .ZIP do SharePoint ou as planilhas (.xls, .xlsx):",
                type=["zip", "xls", "xlsx"],
                accept_multiple_files=True,
                key="up_faltas"
            )

        bf1, bf2 = st.columns([2, 1])
        with bf1:
            if st.button("⚡ Processar Planilhas de Faltas", type="primary", use_container_width=True):
                if not arqs_faltas:
                    st.warning("Selecione pelo menos um arquivo .zip, .xls ou .xlsx.")
                else:
                    lote_faltas = []
                    total_arquivos_lidos = 0
                    data_padrao = data_ref_falta.strftime("%Y-%m-%d")

                    for arq in arqs_faltas:
                        if arq.name.lower().endswith(".zip"):
                            with zipfile.ZipFile(arq, "r") as z:
                                for item in z.namelist():
                                    if item.lower().endswith((".xls", ".xlsx")) and not item.startswith("__MACOSX"):
                                        total_arquivos_lidos += 1
                                        df_temp = ler_planilha_falta_segura(z.read(item), item, data_padrao)
                                        if not df_temp.empty:
                                            lote_faltas.append(df_temp)
                        else:
                            total_arquivos_lidos += 1
                            df_temp = ler_planilha_falta_segura(arq.read(), arq.name, data_padrao)
                            if not df_temp.empty:
                                lote_faltas.append(df_temp)

                    if lote_faltas:
                        df_novas = pd.concat(lote_faltas, ignore_index=True)
                        df_comb = pd.concat([st.session_state["base_faltas"], df_novas], ignore_index=True)
                        df_comb = df_comb.drop_duplicates(subset=["Data_Falta", "Turma", "ID_Jovem", "Jovem"], keep="first")
                        st.session_state["base_faltas"] = df_comb
                        st.success(f"✅ {total_arquivos_lidos} planilhas varridas! {len(df_novas)} ausências válidas extraídas.")
                        st.rerun()
                    else:
                        st.warning("Nenhuma ausência encontrada nas planilhas enviadas (arquivos vazios).")
        with bf2:
            if st.button("🗑️ Limpar Base de Faltas", use_container_width=True):
                st.session_state["base_faltas"] = pd.DataFrame()
                st.rerun()

    df_f = st.session_state["base_faltas"].copy()

    if not df_f.empty:
        # Aplicando os filtros globais da barra lateral
        if filtro_global_inst != "Todos":
            df_f = df_f[df_f["Instrutor"] == filtro_global_inst]
        if filtro_global_turno != "Todos":
            df_f = df_f[df_f["Turno"] == filtro_global_turno]

        st.divider()
        ff1, ff2, ff3, ff4 = st.columns(4)
        with ff1:
            datas_f = ["Todas"] + sorted(df_f["Data_Falta"].astype(str).unique().tolist(), reverse=True)
            sel_data_f = st.selectbox("📅 Filtrar Dia da Falta:", datas_f)
        with ff2:
            unidades_f = ["Todas"] + sorted(df_f["Unidade"].astype(str).unique().tolist())
            sel_unid_f = st.selectbox("🏢 Filtrar Unidade:", unidades_f)
        with ff3:
            df_f_temp = df_f.copy()
            if sel_data_f != "Todas":
                df_f_temp = df_f_temp[df_f_temp["Data_Falta"] == sel_data_f]
            if sel_unid_f != "Todas":
                df_f_temp = df_f_temp[df_f_temp["Unidade"] == sel_unid_f]
            turmas_f = ["Todas"] + sorted(df_f_temp["Turma"].astype(str).unique().tolist())
            sel_turma_f = st.selectbox("🏫 Selecionar Turma (Para Lançar no RM):", turmas_f)
        with ff4:
            busca_jovem_f = st.text_input("🔍 Buscar Jovem ou ID:")

        df_f_view = df_f_temp.copy()
        if sel_turma_f != "Todas":
            df_f_view = df_f_view[df_f_view["Turma"] == sel_turma_f]
        if busca_jovem_f:
            df_f_view = df_f_view[
                df_f_view["Jovem"].astype(str).str.contains(busca_jovem_f, case=False, na=False) |
                df_f_view["ID_Jovem"].astype(str).str.contains(busca_jovem_f, case=False, na=False)
            ]

        # Indicadores rápidos
        kf1, kf2, kf3, kf4 = st.columns(4)
        kf1.metric("Total de Faltas (Filtro)", len(df_f_view))
        kf2.metric("Jovens Ausentes Únicos", df_f_view["Jovem"].nunique())
        kf3.metric("☀️ Manhã (M)", len(df_f_view[df_f_view["Turno"] == "M - Manhã"]))
        kf4.metric("🌤️ Tarde (V)", len(df_f_view[df_f_view["Turno"] == "V - Tarde"]))

        sub_f1, sub_f2, sub_f3 = st.tabs([
            "📝 1. Lançamento no Diário de Classe (RM)",
            "🚨 2. Reincidência Semanal / Mensal (Quem mais falta)",
            "📊 3. Resumo por Unidade e Turno"
        ])

        with sub_f1:
            st.caption("💡 Selecione a Turma no filtro acima e marque a caixinha **Lancado_RM** à medida que registrar a falta no portal RM:")
            df_editado = st.data_editor(
                df_f_view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Lancado_RM": st.column_config.CheckboxColumn("✅ Lançado no RM?", default=False)
                }
            )
            # Atualiza o status de Lançado_RM na sessão
            if not df_editado.empty:
                st.session_state["base_faltas"].loc[df_editado.index, "Lancado_RM"] = df_editado["Lancado_RM"]

        with sub_f2:
            st.subheader("🚨 Ranking de Jovens com Mais Faltas Acumuladas")
            ranking_faltas = (
                df_f_temp.groupby(["ID_Jovem", "Jovem", "Email", "Turma", "Turno", "Instrutor", "Unidade"])
                .agg(
                    Total_Faltas=("Data_Falta", "count"),
                    Datas_Ausente=("Data_Falta", lambda x: ", ".join(sorted(set(x)))),
                    Encontros_Perdidos=("Encontro", lambda x: " | ".join(sorted(set(str(v) for v in x))))
                )
                .reset_index()
                .sort_values(by="Total_Faltas", ascending=False)
            )
            st.dataframe(ranking_faltas, use_container_width=True, hide_index=True)

        with sub_f3:
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("**🏢 Faltas por Unidade (Bojador, Áurea, Cerrado, Missões):**")
                st.bar_chart(df_f_temp.groupby("Unidade")["Jovem"].count())
            with g2:
                st.markdown("**📅 Evolução de Faltas por Dia:**")
                st.bar_chart(df_f_temp.groupby("Data_Falta")["Jovem"].count())

# ==============================================================================
# MÓDULO ETAPA 1: ATIVIDADES MOODLE (DEMÀ DIGITAL)
# ==============================================================================
with modulo_principal[1]:
    st.subheader("📚 Etapa 1: Acompanhamento de Atividades e Evolução (Moodle)")

    with st.expander("📥 Registrar Nova Coleta do Moodle", expanded=st.session_state["base_moodle"].empty):
        cm1, cm2 = st.columns(2)
        with cm1:
            dt_moodle = st.date_input("📅 Data da Coleta Moodle:", value=date.today(), format="DD/MM/YYYY", key="dt_moodle")
        with cm2:
            enc_moodle = st.text_input("📘 Nome do Módulo / Encontro:", value="Encontro da Semana")

        ci1, ci2 = st.columns(2)
        with ci1:
            txt_moodle = st.text_area("Cole (Ctrl+V) o relatório da Extensão do Moodle:", height=110)
        with ci2:
            arqs_moodle = st.file_uploader("Ou envie arquivos (.tsv / .csv):", type=["tsv", "csv", "txt"], accept_multiple_files=True)

        if st.button("➕ Adicionar Coleta do Moodle", type="primary"):
            dfs_m = []
            if txt_moodle.strip():
                dfs_m.append(pd.read_csv(io.StringIO(txt_moodle.strip()), sep="\t"))
            if arqs_moodle:
                for a in arqs_moodle:
                    dfs_m.append(pd.read_csv(a, sep="\t"))
            if dfs_m:
                df_lote_m = pd.concat(dfs_m, ignore_index=True)
                dt_str = dt_moodle.strftime("%Y-%m-%d")
                if "Data_Coleta" not in df_lote_m.columns:
                    df_lote_m.insert(0, "Data_Coleta", dt_str)
                if "Mes_Ano" not in df_lote_m.columns:
                    df_lote_m.insert(1, "Mes_Ano", dt_str[:7])
                if "Encontro" not in df_lote_m.columns:
                    df_lote_m.insert(2, "Encontro", enc_moodle)

                st.session_state["base_moodle"] = pd.concat([st.session_state["base_moodle"], df_lote_m], ignore_index=True).drop_duplicates(
                    subset=["Data_Coleta", "Turma", "Atividade", "Jovem"], keep="last"
                )
                st.success("✅ Coleta do Moodle adicionada!")
                st.rerun()

    df_m = st.session_state["base_moodle"].copy()
    if not df_m.empty:
        if filtro_global_inst != "Todos":
            df_m = df_m[df_m["Instrutor"] == filtro_global_inst]
        if filtro_global_turno != "Todos":
            df_m = df_m[df_m["Turno"] == filtro_global_turno]

        st.dataframe(df_m, use_container_width=True, hide_index=True)
