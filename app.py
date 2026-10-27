import io
import re
import hmac
import zipfile
from datetime import datetime, date
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS VISUAIS
# ==============================================================================
st.set_page_config(
    page_title="Central de Acompanhamento Unificado",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.banner-modulo {
    padding: 16px 22px;
    border-radius: 10px;
    margin-bottom: 18px;
    color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. MAPEAMENTO DE INSTRUTORES E FUNÇÕES DE INTELIGÊNCIA / EXTRAÇÃO
# ==============================================================================
BANCO_TURMAS_PADRAO = {
    "Guilherme": ["APC", "TI"],
}
BANCO_TURMAS = st.secrets.get("BANCO_TURMAS", BANCO_TURMAS_PADRAO)
if not isinstance(BANCO_TURMAS, dict):
    BANCO_TURMAS = dict(BANCO_TURMAS)


def calcular_semana_ano(data_str):
    try:
        dt = pd.to_datetime(str(data_str), errors="coerce")
        if pd.isna(dt):
            return "Sem Data"
        iso = dt.isocalendar()
        return f"{iso.year}-S{int(iso.week):02d}"
    except Exception:
        return "Sem Data"


def identificar_instrutor(turma_str):
    t_up = str(turma_str).upper().strip()
    if not t_up:
        return "Não Mapeado / Outros"
    for instrutor, lista_codigos in BANCO_TURMAS.items():
        for cod in lista_codigos:
            if str(cod).upper().strip() in t_up:
                return instrutor
    return "Não Mapeado / Outros"


def identificar_turno(turma_str, nome_arq=""):
    texto = f"{turma_str} {nome_arq}".upper()
    if re.search(r"(\.\d+M\.|\bMAT\b|MANH[ÃA]|_M_|-M-)", texto):
        return "M - Manhã"
    if re.search(r"(\.\d+V\.|\bVES\b|VESPERTINO|TARDE|_V_|-V-)", texto):
        return "V - Tarde"
    return "Não Identificado"


def identificar_unidade(texto_ref):
    t = str(texto_ref).upper()
    if "DF" in t or "BRASILIA" in t or "BRASÍLIA" in t:
        return "DF"
    if "GO" in t or "GOIAS" in t or "GOIÁS" in t:
        return "GO"
    return "Geral"


def extrair_data_nome_arquivo(nome_limpo, data_padrao_str):
    # Procura padrões DD-MM-YYYY ou DD_MM_YYYY
    m_dmy = re.search(r"(\d{2})[-_.](\d{2})[-_.](\d{4})", nome_limpo)
    if m_dmy:
        return f"{m_dmy.group(3)}-{m_dmy.group(2)}-{m_dmy.group(1)}"
    # Procura padrões YYYY-MM-DD
    m_ymd = re.search(r"(\d{4})[-_.](\d{2})[-_.](\d{2})", nome_limpo)
    if m_ymd:
        return f"{m_ymd.group(1)}-{m_ymd.group(2)}-{m_ymd.group(3)}"
    return data_padrao_str


def extrair_disciplina_nome_arquivo(nome_limpo):
    """Extrai o código ou sigla da disciplina a partir do nome do arquivo/pasta."""
    base = nome_limpo.split("/")[-1]
    base_sem_ext = re.sub(r"\.(xls|xlsx|csv|tsv|zip)$", "", base, flags=re.I).strip()
    # Remove datas do nome para não confundir com código de disciplina
    base_sem_data = re.sub(r"\d{2,4}[-_.]\d{2}[-_.]\d{2,4}", "", base_sem_ext).strip(" -_")
    if "-" in base_sem_data:
        cand = base_sem_data.split("-")[0].strip()
        if cand and cand.upper() not in ["MAT", "VES", "FALTAS", "RELATORIO"]:
            return cand
    return base_sem_data if base_sem_data else "Não Informada"


def garantir_colunas_padrao(df, tipo="FALTAS"):
    """Garante retrocompatibilidade de colunas (incluindo Disciplina, Semana_Ano e Mes_Ano)."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()

    # Normaliza coluna de Disciplina (migra de Modulo_Sigla ou Cod_Disciplina se existir)
    if "Disciplina" not in df.columns:
        if "Codigo_Disciplina" in df.columns:
            df["Disciplina"] = df["Codigo_Disciplina"].fillna("Não Informada").astype(str)
        elif "Modulo_Sigla" in df.columns:
            df["Disciplina"] = df["Modulo_Sigla"].fillna("Não Informada").astype(str)
        else:
            df["Disciplina"] = "Não Informada"
    else:
        df["Disciplina"] = df["Disciplina"].fillna("Não Informada").astype(str).replace("", "Não Informada")

    col_data = "Data_Falta" if tipo == "FALTAS" else "Data_Coleta"
    if col_data in df.columns:
        df[col_data] = df[col_data].astype(str)
        if "Mes_Ano" not in df.columns:
            df["Mes_Ano"] = df[col_data].str.slice(0, 7)
        if "Semana_Ano" not in df.columns:
            df["Semana_Ano"] = df[col_data].apply(calcular_semana_ano)

    if "Turma" in df.columns and "Instrutor" not in df.columns:
        df["Instrutor"] = df["Turma"].apply(identificar_instrutor)

    if "Turno" not in df.columns and "Turma" in df.columns:
        df["Turno"] = df["Turma"].apply(lambda t: identificar_turno(t, ""))

    return df


def filtrar_df_por_instrutor(df, instrutor_sel):
    if df.empty or instrutor_sel.startswith("🌟"):
        return df
    if "Instrutor" not in df.columns and "Turma" in df.columns:
        df = df.copy()
        df["Instrutor"] = df["Turma"].apply(identificar_instrutor)
    if instrutor_sel in ["Outro Instrutor / Geral", "Não Mapeado / Outros"]:
        return df[df["Instrutor"] == "Não Mapeado / Outros"]
    return df[df["Instrutor"] == instrutor_sel]


def converter_bytes_em_dataframe(b_arq, nome_item):
    nome_l = nome_item.lower()
    try:
        if nome_l.endswith(".csv"):
            return pd.read_csv(io.BytesIO(b_arq), sep=None, engine="python", header=None), "ok"
        elif nome_l.endswith(".tsv"):
            return pd.read_csv(io.BytesIO(b_arq), sep="\t", header=None), "ok"
        else:
            try:
                return pd.read_excel(io.BytesIO(b_arq), header=None), "ok"
            except Exception:
                # Fallback caso o .xls seja um HTML/TSV exportado pelo RM/SharePoint
                tabelas = pd.read_html(io.BytesIO(b_arq))
                if tabelas:
                    return tabelas[0], "ok"
    except Exception as e:
        return None, str(e)
    return None, "vazio"


def extrair_alunos_do_dataframe(df_raw, nome_arq, data_padrao_str, disc_forcar=""):
    nome_limpo = nome_arq.split("/")[-1]
    data_falta = extrair_data_nome_arquivo(nome_limpo, data_padrao_str)
    modulo_padrao_arq = extrair_disciplina_nome_arquivo(nome_limpo)

    registros = []
    mapa_cabecalho = {}

    for _, row in df_raw.iterrows():
        valores_brutos = [str(v).strip() if pd.notna(v) else "" for v in row.values]
        valores = [v for v in valores_brutos if v != "" and v.lower() != "nan"]
        if len(valores) < 3:
            continue

        linha_concat = " ".join(valores).upper()

        # Detecta se a linha é um cabeçalho e mapeia a coluna de Disciplina caso exista
        if "CODTURMA" in linha_concat or ("NOME" in linha_concat and ("EMAIL" in linha_concat or "MATRICULA" in linha_concat)):
            for idx_col, val_col in enumerate(valores_brutos):
                v_up = val_col.upper()
                if any(k in v_up for k in ["CODDISC", "DISCIPLINA", "MODULO", "MÓDULO", "SIGLA", "COMPONENTE"]):
                    mapa_cabecalho["idx_disc"] = idx_col
            continue

        email = next((v for v in valores if "@" in v), "")
        turma = next((v for v in valores if re.search(r"(APC|\.\d+[MV]\.)", v, re.I)), "")

        if not turma:
            if 9 < len(row) and pd.notna(row.iloc[9]) and str(row.iloc[9]).strip():
                turma = str(row.iloc[9]).strip()
            elif len(valores) >= 7:
                turma = valores[6]

        if not turma and not email:
            continue

        id_jovem = valores[0] if len(valores) > 0 else ""
        nome_jovem = valores[1] if len(valores) > 1 else ""
        modulo_sigla = valores[3] if len(valores) > 3 else modulo_padrao_arq
        cidade_uf = valores[4] if len(valores) > 4 else ""
        encontro = valores[5] if len(valores) > 5 else ""

        if email and email in valores:
            idx_email = valores.index(email)
            if idx_email >= 1:
                nome_jovem = valores[idx_email - 1]
            if idx_email >= 2:
                id_jovem = valores[idx_email - 2]
            restantes = [v for v in valores[idx_email + 1:] if v != turma]
            if len(restantes) >= 1:
                modulo_sigla = restantes[0]
            if len(restantes) >= 2:
                cidade_uf = restantes[1]
            if len(restantes) >= 3:
                encontro = restantes[2]

        # Se a planilha tinha coluna explícita de Código da Disciplina mapeada no cabeçalho
        if "idx_disc" in mapa_cabecalho:
            idx_d = mapa_cabecalho["idx_disc"]
            if idx_d < len(valores_brutos) and valores_brutos[idx_d]:
                modulo_sigla = valores_brutos[idx_d]

        # Se o usuário informou um código de disciplina padrão no upload, aplica se necessário
        disciplina_final = disc_forcar.strip() if disc_forcar.strip() else (modulo_sigla if modulo_sigla else modulo_padrao_arq)

        nome_limpo_jovem = re.sub(r"\s+", " ", nome_jovem).strip()

        registros.append({
            "Lancado_RM": False,
            "Data_Falta": data_falta,
            "Semana_Ano": calcular_semana_ano(data_falta),
            "Mes_Ano": data_falta[:7],
            "Instrutor": identificar_instrutor(turma),
            "Turno": identificar_turno(turma, nome_arq),
            "Unidade": identificar_unidade(f"{disciplina_final} {nome_limpo}"),
            "Disciplina": disciplina_final,
            "Turma": turma,
            "Matricula": id_jovem,
            "ID_Jovem": id_jovem,
            "Nome": nome_limpo_jovem,
            "Jovem": nome_limpo_jovem,
            "Email": email,
            "Encontro": encontro,
            "Modulo_Sigla": disciplina_final,
            "Cidade_UF": cidade_uf,
            "Arquivo_Origem": nome_limpo
        })

    return pd.DataFrame(registros)


def processar_arquivos_enviados(lista_arquivos, data_padrao_str, disc_forcar=""):
    """Varre arquivos soltos (.xls, .xlsx) e pacotes .zip (inclusive subpastas MAT e VES)."""
    dfs_extraidos = []
    stats = {"total_arquivos": 0, "com_faltas": 0, "em_branco": 0, "erros": []}

    def processar_item_bytes(b_arq, nome_item):
        stats["total_arquivos"] += 1
        df_bruto, _ = converter_bytes_em_dataframe(b_arq, nome_item)
        if df_bruto is not None:
            df_limpo = extrair_alunos_do_dataframe(df_bruto, nome_item, data_padrao_str, disc_forcar)
            if not df_limpo.empty:
                dfs_extraidos.append(df_limpo)
                stats["com_faltas"] += 1
            else:
                stats["em_branco"] += 1
        else:
            stats["em_branco"] += 1

    def abrir_zip_recursivo(bytes_zip):
        try:
            with zipfile.ZipFile(io.BytesIO(bytes_zip), "r") as z:
                for item in z.namelist():
                    if item.endswith("/") or "__MACOSX" in item or item.split("/")[-1].startswith("~$"):
                        continue
                    item_lower = item.lower()
                    if item_lower.endswith(".zip"):
                        abrir_zip_recursivo(z.read(item))
                    elif item_lower.endswith((".xls", ".xlsx", ".csv", ".tsv")):
                        processar_item_bytes(z.read(item), item)
        except Exception as e:
            stats["erros"].append(str(e))

    for arq in lista_arquivos:
        nome_lower = arq.name.lower()
        conteudo = arq.getvalue()
        if nome_lower.endswith(".zip"):
            abrir_zip_recursivo(conteudo)
        else:
            processar_item_bytes(conteudo, arq.name)

    df_final = pd.concat(dfs_extraidos, ignore_index=True) if dfs_extraidos else pd.DataFrame()
    return df_final, stats


# ==============================================================================
# 3. LOGIN SEGURO
# ==============================================================================
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
if "modulo_ativo" not in st.session_state:
    st.session_state["modulo_ativo"] = "FALTAS"

# Garante que as colunas de Disciplina e Semana_Ano sempre existam
st.session_state["base_faltas"] = garantir_colunas_padrao(st.session_state["base_faltas"], "FALTAS")
st.session_state["base_moodle"] = garantir_colunas_padrao(st.session_state["base_moodle"], "MOODLE")

# ==============================================================================
# 4. BARRA LATERAL: FILTROS GLOBAIS E BACKUP
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎯 FILTROS DE VISUALIZAÇÃO")
    opcoes_inst = ["🌟 Todos os Instrutores (Visão Geral)"] + list(BANCO_TURMAS.keys()) + ["Outro Instrutor / Geral"]
    filtro_global_inst = st.selectbox("👤 Filtrar por Instrutor(a):", opcoes_inst, index=0)
    filtro_global_turno = st.selectbox("🕒 Filtrar por Turno (M / V):", ["Todos (M + V)", "M - Manhã", "V - Tarde"])

    # Lista global de códigos de disciplinas disponíveis nas duas bases
    discs_f = st.session_state["base_faltas"]["Disciplina"].dropna().unique().tolist() if not st.session_state["base_faltas"].empty else []
    discs_m = st.session_state["base_moodle"]["Disciplina"].dropna().unique().tolist() if not st.session_state["base_moodle"].empty else []
    opcoes_global_disc = ["📚 Todas as Disciplinas"] + sorted(list(set(discs_f + discs_m)))
    filtro_global_disc = st.selectbox("📚 Filtrar por Cód. Disciplina (Global):", opcoes_global_disc, index=0)

    st.divider()
    st.markdown("### 🗄️ BACKUP HISTÓRICO (.XLSX)")
    arq_hist = st.file_uploader("📂 Restaurar Histórico Salvo:", type=["xlsx"])
    if arq_hist and st.button("🔄 Carregar Histórico", use_container_width=True):
        xls = pd.ExcelFile(arq_hist)
        if "Historico_Moodle" in xls.sheet_names:
            st.session_state["base_moodle"] = garantir_colunas_padrao(pd.read_excel(xls, "Historico_Moodle"), "MOODLE")
        if "Historico_Faltas" in xls.sheet_names:
            st.session_state["base_faltas"] = garantir_colunas_padrao(pd.read_excel(xls, "Historico_Faltas"), "FALTAS")
        st.success("✅ Histórico restaurado!")
        st.rerun()

    if not st.session_state["base_moodle"].empty or not st.session_state["base_faltas"].empty:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            if not st.session_state["base_moodle"].empty:
                st.session_state["base_moodle"].to_excel(writer, sheet_name="Historico_Moodle", index=False)
            if not st.session_state["base_faltas"].empty:
                st.session_state["base_faltas"].to_excel(writer, sheet_name="Historico_Faltas", index=False)
        st.download_button(
            label="💾 Baixar Base Histórica (.xlsx)",
            data=buf.getvalue(),
            file_name=f"Base_Central_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

# ==============================================================================
# 5. MENU PRINCIPAL COM ALTO DESTAQUE VISUAL (CARDS DE NAVEGAÇÃO)
# ==============================================================================
st.markdown("## 🧭 Menu Principal de Módulos")
qtd_faltas = len(st.session_state["base_faltas"])
qtd_moodle = len(st.session_state["base_moodle"])

nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button(f"🟧 1. CONTROLE DE FALTAS ({qtd_faltas} registros)", use_container_width=True, type="primary" if st.session_state["modulo_ativo"] == "FALTAS" else "secondary"):
        st.session_state["modulo_ativo"] = "FALTAS"
        st.rerun()
with nav2:
    if st.button(f"🟦 2. ATIVIDADES MOODLE ({qtd_moodle} registros)", use_container_width=True, type="primary" if st.session_state["modulo_ativo"] == "MOODLE" else "secondary"):
        st.session_state["modulo_ativo"] = "MOODLE"
        st.rerun()
with nav3:
    if st.button("🟩 3. VISÃO 360º (FALTAS + MOODLE)", use_container_width=True, type="primary" if st.session_state["modulo_ativo"] == "VISAO360" else "secondary"):
        st.session_state["modulo_ativo"] = "VISAO360"
        st.rerun()

st.write("")

# ==============================================================================
# MÓDULO 1: CONTROLE DE FALTAS (SHAREPOINT -> RM)
# ==============================================================================
if st.session_state["modulo_ativo"] == "FALTAS":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #ea580c 0%, #c2410c 100%); border-left: 8px solid #fed7aa;">
        <h2 style="margin:0;color:white;">🟧 MÓDULO: Controle de Faltas (SharePoint ➔ Diário de Classe RM)</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Reconhecimento automático de arquivos <b>.ZIP</b> (pastas MAT e VES inteiras), planilhas <b>.XLS / .XLSX</b> e filtro dinâmico por <b>Código da Disciplina</b> (diário e semanal).
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR PLANILHAS OU PACOTE .ZIP DE FALTAS (Processamento Automático ao Soltar)", expanded=True):
        c_dt, c_up = st.columns([1.2, 2.5])
        with c_dt:
            data_ref = st.date_input("📅 Data padrão (se não houver no nome):", value=date.today(), format="DD/MM/YYYY")
            disc_padrao_up = st.text_input("📚 Cód. Disciplina padrão (opcional):", placeholder="Ex: Extraído auto da planilha/arquivo")
            if st.button("🗑️ Limpar Todas as Faltas", use_container_width=True):
                st.session_state["base_faltas"] = pd.DataFrame()
                st.session_state["ultimos_arquivos_lidos"] = []
                st.rerun()
        with c_up:
            arquivos_up = st.file_uploader(
                "Solte aqui o arquivo .ZIP (da pasta do dia ou MAT/VES) OU várias planilhas (.xls / .xlsx):",
                type=["zip", "xls", "xlsx", "csv", "tsv"],
                accept_multiple_files=True,
                key="uploader_faltas_auto"
            )

        if arquivos_up:
            assinatura_atual = [f"{a.name}_{a.size}_{data_ref}_{disc_padrao_up}" for a in arquivos_up]
            if st.session_state.get("ultimos_arquivos_lidos") != assinatura_atual:
                with st.spinner("Lendo planilhas, identificando disciplinas e extraindo jovens ausentes..."):
                    df_novos, stats = processar_arquivos_enviados(arquivos_up, data_ref.strftime("%Y-%m-%d"), disc_padrao_up)
                    st.session_state["ultimos_arquivos_lidos"] = assinatura_atual
                    if not df_novos.empty:
                        st.session_state["base_faltas"] = pd.concat([st.session_state["base_faltas"], df_novos], ignore_index=True).drop_duplicates(
                            subset=["Data_Falta", "Turma", "Disciplina", "Jovem"], keep="last"
                        )
                        st.success(f"✅ {len(df_novos)} registos de faltas importados ({stats['com_faltas']} planilhas com ausências, {stats['em_branco']} sem faltas).")
                    else:
                        st.warning("⚠️ Nenhum jovem ausente encontrado nos arquivos enviados.")

    df_f = st.session_state["base_faltas"].copy()
    if not df_f.empty:
        st.markdown("#### 🎯 Filtrar Faltas por Instrutor, Período (Dia/Semana/Mês) e Código da Disciplina")
        fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.5, 1.0, 1.1, 1.3, 0.9, 1.4])

        with fc1:
            opcoes_inst_f = ["🌟 Todos os Instrutores"] + list(BANCO_TURMAS.keys()) + ["Não Mapeado / Outros"]
            sel_inst_f = st.selectbox("👤 1. Instrutor(a):", opcoes_inst_f, index=0, key="f_inst")
        with fc2:
            modo_f = st.selectbox("🗓️ 2. Trabalhar por:", ["📅 Dia", "📆 Semana", "🗓️ Mês", "♾️ Tudo"], index=0, key="f_modo")
        with fc3:
            if modo_f == "📅 Dia":
                op_pf = ["Todos os Dias"] + sorted(df_f["Data_Falta"].astype(str).unique().tolist(), reverse=True)
                sel_per_f = st.selectbox("Escolher Dia:", op_pf, key="f_dia")
            elif modo_f == "📆 Semana":
                op_pf = ["Todas as Semanas"] + sorted(df_f["Semana_Ano"].astype(str).unique().tolist(), reverse=True)
                sel_per_f = st.selectbox("Escolher Semana:", op_pf, key="f_sem")
            elif modo_f == "🗓️ Mês":
                op_pf = ["Todos os Meses"] + sorted(df_f["Mes_Ano"].astype(str).unique().tolist(), reverse=True)
                sel_per_f = st.selectbox("Escolher Mês:", op_pf, key="f_mes")
            else:
                sel_per_f = "Tudo"
                st.text_input("Período:", value="Todo o Histórico", disabled=True, key="f_tudo")

        # Filtra primeiro por Instrutor e Período para montar a lista dinâmica de Disciplinas daquele Dia/Semana
        df_f_sub = filtrar_df_por_instrutor(df_f, sel_inst_f)
        if not filtro_global_inst.startswith("🌟"):
            df_f_sub = filtrar_df_por_instrutor(df_f_sub, filtro_global_inst)

        if modo_f == "📅 Dia" and sel_per_f != "Todos os Dias":
            df_f_sub = df_f_sub[df_f_sub["Data_Falta"] == sel_per_f]
        elif modo_f == "📆 Semana" and sel_per_f != "Todas as Semanas":
            df_f_sub = df_f_sub[df_f_sub["Semana_Ano"] == sel_per_f]
        elif modo_f == "🗓️ Mês" and sel_per_f != "Todos os Meses":
            df_f_sub = df_f_sub[df_f_sub["Mes_Ano"] == sel_per_f]

        with fc4:
            discs_disponiveis_f = sorted(df_f_sub["Disciplina"].dropna().astype(str).unique().tolist())
            op_disc_f = ["📚 Todas as Disciplinas"] + discs_disponiveis_f
            sel_disc_f = st.selectbox("📚 3. Disciplina (Código):", op_disc_f, key="f_disc")
        with fc5:
            sel_turno_f = st.selectbox("🕒 4. Turno:", ["Todos (M + V)", "M - Manhã", "V - Tarde"], key="f_turno")
        with fc6:
            busca_f = st.text_input("🔍 5. Buscar Jovem / Turma / Cód. Disc.:", key="f_busca")

        # Aplica Filtro de Disciplina (Módulo + Global)
        if sel_disc_f != "📚 Todas as Disciplinas":
            df_f_sub = df_f_sub[df_f_sub["Disciplina"] == sel_disc_f]
        if filtro_global_disc != "📚 Todas as Disciplinas":
            df_f_sub = df_f_sub[df_f_sub["Disciplina"] == filtro_global_disc]

        # Aplica Filtro de Turno (Módulo + Global)
        if sel_turno_f != "Todos (M + V)":
            df_f_sub = df_f_sub[df_f_sub["Turno"] == sel_turno_f]
        if filtro_global_turno != "Todos (M + V)":
            df_f_sub = df_f_sub[df_f_sub["Turno"] == filtro_global_turno]

        # Aplica Busca Textual (inclui Código da Disciplina, Nome, Matrícula e Turma)
        if busca_f:
            col_nome_f = "Nome" if "Nome" in df_f_sub.columns else "Jovem"
            col_mat_f = "Matricula" if "Matricula" in df_f_sub.columns else "ID_Jovem"
            df_f_sub = df_f_sub[
                df_f_sub[col_nome_f].astype(str).str.contains(busca_f, case=False, na=False) |
                df_f_sub[col_mat_f].astype(str).str.contains(busca_f, case=False, na=False) |
                df_f_sub["Turma"].astype(str).str.contains(busca_f, case=False, na=False) |
                df_f_sub["Disciplina"].astype(str).str.contains(busca_f, case=False, na=False)
            ]

        kf1, kf2, kf3, kf4, kf5 = st.columns(5)
        kf1.metric("Faltas Listadas", len(df_f_sub))
        kf2.metric("Turmas no Filtro", df_f_sub["Turma"].nunique())
        kf3.metric("📚 Disciplinas no Período", df_f_sub["Disciplina"].nunique())
        kf4.metric("☀️ Manhã (M)", len(df_f_sub[df_f_sub["Turno"] == "M - Manhã"]))
        kf5.metric("🌤️ Tarde (V)", len(df_f_sub[df_f_sub["Turno"] == "V - Tarde"]))

        cols_exibir_f = [c for c in ["Lancado_RM", "Data_Falta", "Semana_Ano", "Disciplina", "Turno", "Turma", "ID_Jovem", "Jovem", "Email", "Encontro", "Cidade_UF"] if c in df_f_sub.columns]
        st.dataframe(df_f_sub[cols_exibir_f], use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 2: ATIVIDADES MOODLE
# ==============================================================================
elif st.session_state["modulo_ativo"] == "MOODLE":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%); border-left: 8px solid #bfdbfe;">
        <h2 style="margin:0;color:white;">🟦 MÓDULO: Acompanhamento de Atividades Moodle</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Controle de pendências por <b>Dia, Semana, Mês e Código da Disciplina</b> com comparativo automático de regularização.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR RELATÓRIO DE PENDÊNCIAS DO MOODLE (.XLSX / .CSV / COLAGEM)", expanded=st.session_state["base_moodle"].empty):
        bm1, bm2 = st.columns([3, 1])
        with bm1:
            arqs_moodle = st.file_uploader("Solte planilhas ou CSV extraídos do Moodle:", type=["xlsx", "xls", "csv"], accept_multiple_files=True, key="up_moodle")
            if arqs_moodle and st.button("📥 Processar Arquivos do Moodle", type="primary"):
                dfs_m = []
                for am in arqs_moodle:
                    df_temp, _ = converter_bytes_em_dataframe(am.getvalue(), am.name)
                    if df_temp is not None and not df_temp.empty:
                        # Usa primeira linha como cabeçalho se contiver nomes padrão
                        prim_linha = [str(x).strip() for x in df_temp.iloc[0].values]
                        if any(k in " ".join(prim_linha).upper() for k in ["JOVEM", "TURMA", "ATIVIDADE", "ALUNO", "NOME"]):
                            df_temp.columns = prim_linha
                            df_temp = df_temp.iloc[1:].reset_index(drop=True)
                        if "Data_Coleta" not in df_temp.columns:
                            df_temp["Data_Coleta"] = date.today().strftime("%Y-%m-%d")
                        if "Disciplina" not in df_temp.columns:
                            df_temp["Disciplina"] = extrair_disciplina_nome_arquivo(am.name)
                        dfs_m.append(garantir_colunas_padrao(df_temp, "MOODLE"))
                if dfs_m:
                    st.session_state["base_moodle"] = pd.concat([st.session_state["base_moodle"]] + dfs_m, ignore_index=True)
                    st.success("✅ Base do Moodle atualizada!")
                    st.rerun()
        with bm2:
            if st.button("🗑️ Limpar Base do Moodle", use_container_width=True):
                st.session_state["base_moodle"] = pd.DataFrame()
                st.rerun()

    df_m = st.session_state["base_moodle"].copy()
    if not df_m.empty:
        if "Semana_Ano" not in df_m.columns:
            df_m["Semana_Ano"] = df_m["Data_Coleta"].apply(calcular_semana_ano)
        if "Turma" in df_m.columns:
            df_m["Instrutor"] = df_m["Turma"].apply(identificar_instrutor)
        df_m = garantir_colunas_padrao(df_m, "MOODLE")

        st.markdown("#### 🎯 Filtrar Atividades por Instrutor, Período (Dia, Semana ou Mês) e Código da Disciplina")
        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns([1.5, 1.0, 1.1, 1.3, 0.9, 1.4])

        with mc1:
            opcoes_inst_m = ["🌟 Todos os Instrutores"] + list(BANCO_TURMAS.keys()) + ["Não Mapeado / Outros"]
            sel_inst_m = st.selectbox("👤 1. Instrutor(a) (Puxa todas as turmas):", opcoes_inst_m, index=0, key="m_inst")
        with mc2:
            modo_m = st.selectbox("🗓️ 2. Trabalhar por:", ["📅 Dia", "📆 Semana", "🗓️ Mês", "♾️ Tudo"], index=0, key="m_modo")
        with mc3:
            if modo_m == "📅 Dia":
                op_pm = ["Todos os Dias"] + sorted(df_m["Data_Coleta"].astype(str).unique().tolist(), reverse=True)
                sel_per_m = st.selectbox("Escolher Dia:", op_pm, key="m_dia")
            elif modo_m == "📆 Semana":
                op_pm = ["Todas as Semanas"] + sorted(df_m["Semana_Ano"].astype(str).unique().tolist(), reverse=True)
                sel_per_m = st.selectbox("Escolher Semana:", op_pm, key="m_sem")
            elif modo_m == "🗓️ Mês":
                op_pm = ["Todos os Meses"] + sorted(df_m["Mes_Ano"].astype(str).unique().tolist(), reverse=True)
                sel_per_m = st.selectbox("Escolher Mês:", op_pm, key="m_mes")
            else:
                sel_per_m = "Tudo"
                st.text_input("Período:", value="Todo o Histórico", disabled=True, key="m_tudo")

        df_m_sub = filtrar_df_por_instrutor(df_m, sel_inst_m)
        if not filtro_global_inst.startswith("🌟"):
            df_m_sub = filtrar_df_por_instrutor(df_m_sub, filtro_global_inst)

        if modo_m == "📅 Dia" and sel_per_m != "Todos os Dias":
            df_m_sub = df_m_sub[df_m_sub["Data_Coleta"] == sel_per_m]
        elif modo_m == "📆 Semana" and sel_per_m != "Todas as Semanas":
            df_m_sub = df_m_sub[df_m_sub["Semana_Ano"] == sel_per_m]
        elif modo_m == "🗓️ Mês" and sel_per_m != "Todos os Meses":
            df_m_sub = df_m_sub[df_m_sub["Mes_Ano"] == sel_per_m]

        with mc4:
            discs_disponiveis_m = sorted(df_m_sub["Disciplina"].dropna().astype(str).unique().tolist())
            op_disc_m = ["📚 Todas as Disciplinas"] + discs_disponiveis_m
            sel_disc_m = st.selectbox("📚 3. Disciplina (Código):", op_disc_m, key="m_disc")
        with mc5:
            sel_turno_m = st.selectbox("🕒 4. Turno (M / V):", ["Todos (M + V)", "M - Manhã", "V - Tarde"], key="m_turno")
        with mc6:
            busca_m = st.text_input("🔍 5. Buscar Jovem / Ativ. / Cód. Disc.:", key="m_busca")

        if sel_disc_m != "📚 Todas as Disciplinas":
            df_m_sub = df_m_sub[df_m_sub["Disciplina"] == sel_disc_m]
        if filtro_global_disc != "📚 Todas as Disciplinas":
            df_m_sub = df_m_sub[df_m_sub["Disciplina"] == filtro_global_disc]

        if sel_turno_m != "Todos (M + V)":
            df_m_sub = df_m_sub[df_m_sub["Turno"] == sel_turno_m]
        if filtro_global_turno != "Todos (M + V)":
            df_m_sub = df_m_sub[df_m_sub["Turno"] == filtro_global_turno]

        if busca_m:
            df_m_sub = df_m_sub[
                df_m_sub["Jovem"].astype(str).str.contains(busca_m, case=False, na=False) |
                df_m_sub["Turma"].astype(str).str.contains(busca_m, case=False, na=False) |
                df_m_sub["Atividade"].astype(str).str.contains(busca_m, case=False, na=False) |
                df_m_sub["Disciplina"].astype(str).str.contains(busca_m, case=False, na=False)
            ]

        km1, km2, km3, km4, km5 = st.columns(5)
        km1.metric("Pendências Listadas", len(df_m_sub))
        km2.metric("Turmas do Instrutor", df_m_sub["Turma"].nunique())
        km3.metric("📚 Disciplinas no Período", df_m_sub["Disciplina"].nunique())
        km4.metric("☀️ Manhã (M)", len(df_m_sub[df_m_sub["Turno"] == "M - Manhã"]))
        km5.metric("🌤️ Tarde (V)", len(df_m_sub[df_m_sub["Turno"] == "V - Tarde"]))

        sub_m1, sub_m2 = st.tabs([
            "📋 1. PENDÊNCIAS DAS TURMAS DO INSTRUTOR",
            "📈 2. COMPARATIVO SEMANAL / MENSAL (QUEM REGULARIZOU)"
        ])
        with sub_m1:
            st.dataframe(df_m_sub, use_container_width=True, hide_index=True)
        with sub_m2:
            datas_m = sorted(df_m["Data_Coleta"].astype(str).unique().tolist())
            if len(datas_m) < 2:
                st.info("Registe pelo menos 2 datas diferentes de coleta para comparar quem regularizou na semana.")
            else:
                cd1, cd2 = st.columns(2)
                with cd1:
                    d_ant = st.selectbox("1ª Coleta (Cobrança Inicial):", datas_m, index=0)
                with cd2:
                    d_nov = st.selectbox("2ª Coleta (Conferência):", datas_m, index=len(datas_m) - 1)
                df_a = filtrar_df_por_instrutor(df_m[df_m["Data_Coleta"] == d_ant], sel_inst_m)
                df_n = filtrar_df_por_instrutor(df_m[df_m["Data_Coleta"] == d_nov], sel_inst_m)
                if sel_disc_m != "📚 Todas as Disciplinas":
                    df_a = df_a[df_a["Disciplina"] == sel_disc_m]
                    df_n = df_n[df_n["Disciplina"] == sel_disc_m]
                chaves_merge = [c for c in ["Disciplina", "Turma", "Atividade", "Jovem"] if c in df_a.columns and c in df_n.columns]
                comp = pd.merge(df_a, df_n, on=chaves_merge, how="outer", indicator=True)
                st.metric("✅ Jovens que Regularizaram após o E-mail", len(comp[comp["_merge"] == "left_only"]))
                st.dataframe(comp[comp["_merge"] == "left_only"][chaves_merge], use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 3: VISÃO 360º (CRUZAMENTO FALTAS + MOODLE)
# ==============================================================================
elif st.session_state["modulo_ativo"] == "VISAO360":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #059669 0%, #047857 100%); border-left: 8px solid #a7f3d0;">
        <h2 style="margin:0;color:white;">🟩 MÓDULO: Visão 360º do Jovem (Cruzamento Faltas + Atividades)</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Pesquise qualquer jovem, matrícula, código da turma ou <b>código da disciplina</b> para cruzar faltas e atividades pendentes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    v1, v2 = st.columns([2.2, 1.2])
    with v1:
        termo_360 = st.text_input("🔍 Digite o Nome do Jovem, Matrícula, Código da Turma ou Código da Disciplina:")
    with v2:
        sel_disc_360 = st.selectbox("📚 Filtrar por Disciplina Específica:", opcoes_global_disc, index=0, key="disc_360")

    if termo_360 or sel_disc_360 != "📚 Todas as Disciplinas":
        c360_1, c360_2 = st.columns(2)
        with c360_1:
            st.markdown("### 🟧 Faltas Registadas")
            df_f = st.session_state["base_faltas"]
            if not df_f.empty:
                col_n = "Nome" if "Nome" in df_f.columns else "Jovem"
                col_m = "Matricula" if "Matricula" in df_f.columns else "ID_Jovem"
                res_f = df_f.copy()
                if sel_disc_360 != "📚 Todas as Disciplinas":
                    res_f = res_f[res_f["Disciplina"] == sel_disc_360]
                if termo_360:
                    res_f = res_f[
                        res_f[col_n].astype(str).str.contains(termo_360, case=False, na=False) |
                        res_f[col_m].astype(str).str.contains(termo_360, case=False, na=False) |
                        res_f["Turma"].astype(str).str.contains(termo_360, case=False, na=False) |
                        res_f["Disciplina"].astype(str).str.contains(termo_360, case=False, na=False)
                    ]
                cols_360_f = [c for c in ["Data_Falta", "Semana_Ano", "Disciplina", "Matricula", "ID_Jovem", "Nome", "Jovem", "Cidade_UF", "Turma", "Turno"] if c in res_f.columns]
                # Remove duplicatas visuais de colunas equivalentes (Nome/Jovem, Matricula/ID_Jovem)
                if "Nome" in cols_360_f and "Jovem" in cols_360_f:
                    cols_360_f.remove("Jovem")
                if "Matricula" in cols_360_f and "ID_Jovem" in cols_360_f:
                    cols_360_f.remove("ID_Jovem")
                st.dataframe(res_f[cols_360_f], use_container_width=True, hide_index=True)

        with c360_2:
            st.markdown("### 🟦 Atividades Pendentes (Moodle)")
            df_m = st.session_state["base_moodle"]
            if not df_m.empty:
                res_m = df_m.copy()
                if sel_disc_360 != "📚 Todas as Disciplinas":
                    res_m = res_m[res_m["Disciplina"] == sel_disc_360]
                if termo_360:
                    res_m = res_m[
                        res_m["Jovem"].astype(str).str.contains(termo_360, case=False, na=False) |
                        res_m["Turma"].astype(str).str.contains(termo_360, case=False, na=False) |
                        res_m["Disciplina"].astype(str).str.contains(termo_360, case=False, na=False) |
                        res_m["Atividade"].astype(str).str.contains(termo_360, case=False, na=False)
                    ]
                cols_360_m = [c for c in ["Data_Coleta", "Semana_Ano", "Disciplina", "Turno", "Turma", "Jovem", "Atividade"] if c in res_m.columns]
                st.dataframe(res_m[cols_360_m], use_container_width=True, hide_index=True)
