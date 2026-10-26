import streamlit as st
import pandas as pd
import io
import zipfile
import hmac
from datetime import datetime

st.set_page_config(
    page_title="Central do Instrutor - Painel Unificado",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 1. TRAVA DE SEGURANÇA (AUTENTICAÇÃO)
# ==========================================
def verificar_senha():
    """Bloqueia o acesso até que a senha configurada em st.secrets seja validada."""
    def validar():
        senha_correta = st.secrets.get("SENHA_PAINEL", "admin123")
        if hmac.compare_digest(st.session_state["senha_digitada"], senha_correta):
            st.session_state["autenticado"] = True
            del st.session_state["senha_digitada"]
        else:
            st.session_state["autenticado"] = False

    if st.session_state.get("autenticado", False):
        return True

    st.title("🔒 Acesso Restrito - Central de Acompanhamento")
    st.markdown("Insira sua credencial de acesso para carregar os módulos de Faltas, Moodle e RM.")
    st.text_input("Senha de Acesso:", type="password", on_change=validar, key="senha_digitada")
    if "autenticado" in st.session_state and not st.session_state["autenticado"]:
        st.error("❌ Senha incorreta.")
    return False

if not verificar_senha():
    st.stop()

# ==========================================
# 2. BARRA LATERAL: TURMAS E GOOGLE DRIVE
# ==========================================
with st.sidebar:
    st.header("⚙️ Minhas Turmas")
    st.caption("Informe os códigos das suas turmas (um por linha):")
    
    turmas_padrao = (
        "3872.APC01.2M.104\n"
        "3872.APC09.0M.106\n"
        "671.APC09.0M.106\n"
        "3872.APC09.0M.85\n"
        "3872.APC09.0M.104\n"
        "3872.APC09.0M.100\n"
        "03872.APC09.0M.54"
    )
    turmas_texto = st.text_area("Turmas Monitoradas:", value=turmas_padrao, height=180)
    minhas_turmas = [t.strip() for t in turmas_texto.split("\n") if t.strip()]
    filtrar_minhas = st.checkbox("Filtrar apenas minhas turmas", value=True)
    
    st.divider()
    st.subheader("☁️ Backup Google Drive")
    st.caption("Exporte ou recarregue a base consolidada na sua pasta do Google Drive:")
    
    # Botão para exportar tudo em um único Excel para salvar no Google Drive
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
            label="💾 Baixar Base Unificada (.xlsx)",
            data=buffer_excel.getvalue(),
            file_name=f"Base_Unificada_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    arquivo_backup = st.file_uploader("Carregar Base salva do Google Drive (.xlsx):", type=["xlsx"])
    if arquivo_backup:
        xls = pd.ExcelFile(arquivo_backup)
        if "Faltas" in xls.sheet_names:
            st.session_state["df_faltas"] = pd.read_excel(xls, "Faltas")
        if "Moodle" in xls.sheet_names:
            st.session_state["df_moodle"] = pd.read_excel(xls, "Moodle")
        if "Avaliacao_RM" in xls.sheet_names:
            st.session_state["df_rm"] = pd.read_excel(xls, "Avaliacao_RM")
        st.success("Base restaurada com sucesso!")

# ==========================================
# 3. INTERFACE PRINCIPAL (4 ABAS)
# ==========================================
st.title("📊 Central de Acompanhamento Unificado")

tab1, tab2, tab3, tab4 = st.tabs([
    "📅 1. Faltas (SharePoint ➔ RM)",
    "📚 2. Atividades (Moodle Demà)",
    "📝 3. Avaliação de Desempenho (RM)",
    "🎯 4. Visão 360º do Jovem"
])

# ------------------------------------------
# ABA 1: FALTAS (SHAREPOINT -> DIÁRIO DE CLASSE RM)
# ------------------------------------------
with tab1:
    st.subheader("📅 Consolidador de Faltas Diárias (MAT / VES)")
    st.markdown(
        "No SharePoint (`FALTAS > 2026 > MÊS > DIA`), clique em **Baixar** na pasta `MAT` ou `VES` "
        "e arraste o arquivo `.zip` (ou as planilhas `.xls`/`.xlsx` soltas) para o campo abaixo:"
    )

    arquivos_faltas = st.file_uploader(
        "Upload de Planilhas ou Pacote .ZIP do Turno:",
        type=["xls", "xlsx", "zip"],
        accept_multiple_files=True
    )

    def processar_planilha_falta(bytes_arq, nome_arq):
        try:
            ext = nome_arq.lower().split(".")[-1]
            engine = "xlrd" if ext == "xls" else "openpyxl"
            df_bruto = pd.read_excel(io.BytesIO(bytes_arq), header=None, engine=engine)
            
            # Colunas padrão da planilha (Ex: EMP_UB02 - 23-10-2026_M)
            mapa_colunas = {
                0: "ID_Jovem",
                1: "Nome",
                2: "Email",
                3: "Modulo_Unidade",
                5: "Cidade_UF",
                7: "Encontro",
                9: "Turma",
                11: "Data"
            }
            cols_validas = [c for c in mapa_colunas.keys() if c < df_bruto.shape[1]]
            df = df_bruto[cols_validas].rename(columns=mapa_colunas)
            df = df.dropna(subset=["Nome", "Turma"], how="any")
            df["Planilha_Origem"] = nome_arq
            return df
        except Exception:
            return pd.DataFrame()

    if arquivos_faltas:
        dfs = []
        for arq in arquivos_faltas:
            if arq.name.lower().endswith(".zip"):
                with zipfile.ZipFile(arq, "r") as z:
                    for item in z.namelist():
                        if item.lower().endswith((".xls", ".xlsx")) and not item.startswith("__MACOSX"):
                            df_t = processar_planilha_falta(z.read(item), item.split("/")[-1])
                            if not df_t.empty:
                                dfs.append(df_t)
            else:
                df_t = processar_planilha_falta(arq.read(), arq.name)
                if not df_t.empty:
                    dfs.append(df_t)

        if dfs:
            df_total = pd.concat(dfs, ignore_index=True)
            df_total["Turma"] = df_total["Turma"].astype(str).str.strip()

            if filtrar_minhas and minhas_turmas:
                padrao = "|".join([t.lstrip("0") for t in minhas_turmas])
                df_total = df_total[df_total["Turma"].str.contains(padrao, case=False, na=False)]

            st.session_state["df_faltas"] = df_total

    if "df_faltas" in st.session_state and not st.session_state["df_faltas"].empty:
        df_f = st.session_state["df_faltas"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Jovens Ausentes (Filtro)", len(df_f))
        c2.metric("Turmas Afetadas", df_f["Turma"].nunique())
        c3.metric("Planilhas Lidas", df_f["Planilha_Origem"].nunique())

        turma_sel = st.selectbox(
            "Selecione a Turma para lançar no Diário de Classe do RM:",
            options=["Todas"] + sorted(df_f["Turma"].unique().tolist())
        )
        df_view = df_f if turma_sel == "Todas" else df_f[df_f["Turma"] == turma_sel].copy()
        df_view.insert(0, "Lançado_no_RM", False)
        
        st.caption("💡 Marque a caixa 'Lançado_no_RM' conforme for registrando a falta no portal Corpore.Net:")
        st.data_editor(
            df_view[["Lançado_no_RM", "Turma", "ID_Jovem", "Nome", "Email", "Encontro", "Modulo_Unidade", "Data"]],
            use_container_width=True,
            hide_index=True
        )

# ------------------------------------------
# ABA 2: ATIVIDADES MOODLE (GRÁFICO DE ANÁLISE)
# ------------------------------------------
with tab2:
    st.subheader("📚 Atividades Não Realizadas (Moodle Demà Digital)")
    st.markdown(
        "Cole abaixo o resultado gerado pelo **Script Extrator do Moodle** (Etapa 3) na tela `graphresourceurl.php`:"
    )

    entrada_moodle = st.text_area(
        "Dados extraídos do Moodle (Formato Tabulado: Turma | Atividade | Status | Nome | Email):",
        height=130,
        placeholder="Turma\tAtividade\tStatus\tNome"
    )

    if entrada_moodle:
        try:
            df_m = pd.read_csv(io.StringIO(entrada_moodle), sep="\t")
            if filtrar_minhas and minhas_turmas and "Turma" in df_m.columns:
                padrao = "|".join([t.lstrip("0") for t in minhas_turmas])
                df_m = df_m[df_m["Turma"].astype(str).str.contains(padrao, case=False, na=False)]
            st.session_state["df_moodle"] = df_m
        except Exception as e:
            st.error(f"Erro ao ler dados do Moodle: {e}")

    if "df_moodle" in st.session_state and not st.session_state["df_moodle"].empty:
        df_m = st.session_state["df_moodle"]
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ativ_sel = st.multiselect("Filtrar Atividade:", options=df_m["Atividade"].unique(), default=df_m["Atividade"].unique())
        with col_f2:
            turma_m_sel = st.selectbox("Filtrar Turma:", options=["Todas"] + sorted(df_m["Turma"].unique().tolist()))

        df_m_view = df_m[df_m["Atividade"].isin(ativ_sel)]
        if turma_m_sel != "Todas":
            df_m_view = df_m_view[df_m_view["Turma"] == turma_m_sel]

        st.dataframe(df_m_view, use_container_width=True, hide_index=True)

        nomes_pendentes = ", ".join(df_m_view["Nome"].unique().tolist())
        st.text_area("📋 Lista de Nomes Pronta para Cobrança:", value=nomes_pendentes, height=80)

# ------------------------------------------
# ABA 3: AVALIAÇÃO DE DESEMPENHO (CONSULTA SQL RM)
# ------------------------------------------
with tab3:
    st.subheader("📝 Curadoria da Avaliação de Desempenho (AvaliacaoGeral)")
    st.markdown(
        "Cole abaixo os dados acumulados pelo **Script Extrator do RM** (Etapa 4) para filtrar automaticamente quem não concluiu:"
    )

    entrada_rm = st.text_area(
        "Cole aqui os dados da Consulta SQL (AvaliacaoGeral):",
        height=130,
        placeholder="STATUS_PROVA\tSTATUS_PERIODO\tCODPESSOA\tCODPROVA\tCODPERIODO\tNOMEPROVA\tNOMEPERIODO\tDATAINICIAL\tDATAFINAL\tCODIGO_ACESSO\tNOME\tCIDADE"
    )

    if entrada_rm:
        try:
            df_r = pd.read_csv(io.StringIO(entrada_rm), sep="\t")
            st.session_state["df_rm"] = df_r
        except Exception as e:
            st.error(f"Erro ao processar tabela do RM: {e}")

    if "df_rm" in st.session_state and not st.session_state["df_rm"].empty:
        df_r = st.session_state["df_rm"]
        col_status = df_r.columns[0]  # STATUS_PROVA

        c_rm1, c_rm2 = st.columns(2)
        with c_rm1:
            opcoes_status = df_r[col_status].dropna().unique().tolist()
            padrao_status = [s for s in opcoes_status if str(s).upper() != "FINALIZADO"]
            filtro_st = st.multiselect("Filtrar STATUS_PROVA:", options=opcoes_status, default=padrao_status)
        with c_rm2:
            if "NOMEPERIODO" in df_r.columns:
                opcoes_per = df_r["NOMEPERIODO"].dropna().unique().tolist()
                filtro_per = st.multiselect("Filtrar Período Avaliativo:", options=opcoes_per, default=opcoes_per)
            else:
                filtro_per = None

        df_r_view = df_r[df_r[col_status].isin(filtro_st)]
        if filtro_per is not None and "NOMEPERIODO" in df_r_view.columns:
            df_r_view = df_r_view[df_r_view["NOMEPERIODO"].isin(filtro_per)]

        k1, k2, k3 = st.columns(3)
        k1.metric("Total de Registros Lidos", len(df_r))
        k2.metric("Jovens Pendentes / Em Andamento", len(df_r_view))
        k3.metric("Concluídos (FINALIZADO)", len(df_r[df_r[col_status].astype(str).str.upper() == "FINALIZADO"]))

        st.dataframe(df_r_view, use_container_width=True, hide_index=True)

# ------------------------------------------
# ABA 4: VISÃO 360º DO JOVEM
# ------------------------------------------
with tab4:
    st.subheader("🎯 Busca Unificada por Jovem ou Turma")
    termo = st.text_input("🔍 Digite parte do Nome do Jovem ou Código da Turma:")

    if termo:
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("#### 📅 Faltas")
            if "df_faltas" in st.session_state:
                df_f = st.session_state["df_faltas"]
                res_f = df_f[
                    df_f["Nome"].astype(str).str.contains(termo, case=False, na=False) |
                    df_f["Turma"].astype(str).str.contains(termo, case=False, na=False)
                ]
                st.dataframe(res_f[["Nome", "Turma", "Data", "Encontro"]], hide_index=True)
            else:
                st.caption("Sem dados carregados na Aba 1.")

        with col_b:
            st.markdown("#### 📚 Pendências Moodle")
            if "df_moodle" in st.session_state:
                df_m = st.session_state["df_moodle"]
                res_m = df_m[
                    df_m["Nome"].astype(str).str.contains(termo, case=False, na=False) |
                    df_m["Turma"].astype(str).str.contains(termo, case=False, na=False)
                ]
                st.dataframe(res_m[["Nome", "Turma", "Atividade", "Status"]], hide_index=True)
            else:
                st.caption("Sem dados carregados na Aba 2.")

        with col_c:
            st.markdown("#### 📝 Avaliação RM")
            if "df_rm" in st.session_state:
                df_r = st.session_state["df_rm"]
                col_nome = "NOME" if "NOME" in df_r.columns else df_r.columns[-2]
                res_r = df_r[df_r[col_nome].astype(str).str.contains(termo, case=False, na=False)]
                cols_mostrar = [c for c in ["NOME", "STATUS_PROVA", "NOMEPERIODO", "DATAFINAL", "CODIGO_ACESSO"] if c in df_r.columns]
                st.dataframe(res_r[cols_mostrar] if cols_mostrar else res_r, hide_index=True)
            else:
                st.caption("Sem dados carregados na Aba 3.")