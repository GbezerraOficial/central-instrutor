import streamlit as st
import pandas as pd
import io
import hmac
from datetime import datetime, date

st.set_page_config(
    page_title="Etapa 1 - Acompanhamento & Histórico Moodle",
    page_icon="📚",
    layout="wide"
)

# 1. LOGIN SEGURO
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

# ==========================================
# BARRA LATERAL: GESTÃO DO HISTÓRICO (SEMANAL / MENSAL)
# ==========================================
with st.sidebar:
    st.header("🗄️ Histórico Semanal / Mensal")
    st.caption("Carregue sua planilha histórica (.xlsx) para comparar com a coleta de hoje:")

    arq_historico = st.file_uploader("📂 Carregar Base Histórica (.xlsx):", type=["xlsx"])
    if arq_historico and st.button("🔄 Restaurar Histórico no Painel", use_container_width=True):
        try:
            xls = pd.ExcelFile(arq_historico)
            aba_alvo = "Historico_Completo" if "Historico_Completo" in xls.sheet_names else xls.sheet_names[0]
            df_hist = pd.read_excel(xls, sheet_name=aba_alvo)
            st.session_state["base_moodle"] = pd.concat([st.session_state["base_moodle"], df_hist], ignore_index=True).drop_duplicates(
                subset=["Data_Coleta", "Turma", "Atividade", "Jovem"], keep="last"
            )
            st.success(f"Histórico carregado! ({len(st.session_state['base_moodle'])} registros)")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")

    st.divider()
    if not st.session_state["base_moodle"].empty:
        df_salvar = st.session_state["base_moodle"]
        buffer_hist = io.BytesIO()
        with pd.ExcelWriter(buffer_hist, engine="openpyxl") as writer:
            df_salvar.to_excel(writer, sheet_name="Historico_Completo", index=False)

        st.download_button(
            label="💾 Salvar Base Histórica Atualizada (.xlsx)",
            data=buffer_hist.getvalue(),
            file_name=f"Historico_Moodle_{datetime.now().strftime('%Y-%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

st.title("📚 Etapa 1: Acompanhamento de Atividades e Evolução (Moodle)")

# ==========================================
# ENTRADA DE NOVA COLETA (COM DATA E SEMANA)
# ==========================================
with st.expander("📥 Registrar Nova Coleta do Moodle (Hoje ou Data Específica)", expanded=st.session_state["base_moodle"].empty):
    c_meta1, c_meta2 = st.columns(2)
    with c_meta1:
        data_coleta_input = st.date_input("📅 Data desta Coleta:", value=date.today(), format="DD/MM/YYYY")
    with c_meta2:
        encontro_input = st.text_input("📘 Nome do Módulo / Encontro (Opcional):", value="Encontro da Semana")

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        texto_colado = st.text_area(
            "Opção A: Cole (Ctrl+V) o relatório copiado pela Extensão:",
            height=120,
            placeholder="Instrutor\tTurno\tTurma\tAtividade\tStatus\tJovem\tEmail_Enviado"
        )
    with col_in2:
        arquivos_up = st.file_uploader(
            "Opção B: Ou envie os arquivos (.tsv / .csv) baixados pela Extensão:",
            type=["tsv", "csv", "txt"],
            accept_multiple_files=True
        )

    b1, b2 = st.columns([2, 1])
    with b1:
        if st.button("➕ Adicionar Coleta ao Histórico", type="primary", use_container_width=True):
            novos_dfs = []
            if texto_colado.strip():
                try:
                    novos_dfs.append(pd.read_csv(io.StringIO(texto_colado.strip()), sep="\t"))
                except Exception as e:
                    st.error(f"Erro ao ler texto: {e}")

            if arquivos_up:
                for arq in arquivos_up:
                    try:
                        novos_dfs.append(pd.read_csv(arq, sep="\t"))
                    except Exception as e:
                        st.error(f"Erro no arquivo {arq.name}: {e}")

            if novos_dfs:
                df_lote = pd.concat(novos_dfs, ignore_index=True)
                data_str = data_coleta_input.strftime("%Y-%m-%d")
                semana_str = f"{data_coleta_input.year}-S{data_coleta_input.isocalendar()[1]:02d}"
                mes_str = data_coleta_input.strftime("%Y-%m")

                if "Data_Coleta" not in df_lote.columns:
                    df_lote.insert(0, "Data_Coleta", data_str)
                if "Semana_Ano" not in df_lote.columns:
                    df_lote.insert(1, "Semana_Ano", semana_str)
                if "Mes_Ano" not in df_lote.columns:
                    df_lote.insert(2, "Mes_Ano", mes_str)
                if "Encontro" not in df_lote.columns:
                    df_lote.insert(3, "Encontro", encontro_input)

                df_combinado = pd.concat([st.session_state["base_moodle"], df_lote], ignore_index=True)
                df_combinado = df_combinado.drop_duplicates(
                    subset=["Data_Coleta", "Turma", "Atividade", "Jovem"], keep="last"
                )
                st.session_state["base_moodle"] = df_combinado
                st.success(f"✅ Coleta de {data_coleta_input.strftime('%d/%m/%Y')} adicionada! Total no histórico: {len(df_combinado)} linhas.")
                st.rerun()
    with b2:
        if st.button("🗑️ Limpar Memória da Sessão", use_container_width=True):
            st.session_state["base_moodle"] = pd.DataFrame()
            st.rerun()

# ==========================================
# ABAS DE ANÁLISE (FOTO ATUAL vs EVOLUÇÃO SEMANAL/MENSAL)
# ==========================================
df = st.session_state["base_moodle"].copy()

if not df.empty:
    # Garante que colunas de tempo existam mesmo para arquivos antigos
    if "Data_Coleta" not in df.columns:
        df["Data_Coleta"] = date.today().strftime("%Y-%m-%d")
    df["Data_Coleta"] = df["Data_Coleta"].astype(str)
    if "Mes_Ano" not in df.columns:
        df["Mes_Ano"] = df["Data_Coleta"].str.slice(0, 7)

    st.divider()
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_instrutor = st.selectbox("👤 Instrutor(a):", ["Todos"] + sorted(df["Instrutor"].dropna().astype(str).unique().tolist()))
    with f2:
        sel_turno = st.selectbox("🕒 Turno (M / V):", ["Todos"] + sorted(df["Turno"].dropna().astype(str).unique().tolist()))
    with f3:
        datas_disp = sorted(df["Data_Coleta"].unique().tolist(), reverse=True)
        sel_data = st.selectbox("📅 Filtrar Data da Coleta:", ["Todas as Datas"] + datas_disp)
    with f4:
        turmas_disp = ["Todas"] + sorted(df["Turma"].dropna().astype(str).unique().tolist())
        sel_turma = st.selectbox("🏫 Filtrar Turma:", turmas_disp)

    df_base_filtro = df.copy()
    if sel_instrutor != "Todos":
        df_base_filtro = df_base_filtro[df_base_filtro["Instrutor"] == sel_instrutor]
    if sel_turno != "Todos":
        df_base_filtro = df_base_filtro[df_base_filtro["Turno"] == sel_turno]
    if sel_turma != "Todas":
        df_base_filtro = df_base_filtro[df_base_filtro["Turma"] == sel_turma]

    df_visao = df_base_filtro if sel_data == "Todas as Datas" else df_base_filtro[df_base_filtro["Data_Coleta"] == sel_data]

    aba1, aba2, aba3 = st.tabs([
        "📋 1. Pendências da Coleta",
        "📈 2. Comparativo Semanal (Quem Regularizou vs. Pendente)",
        "🗓️ 3. Fechamento Mensal & Reincidência"
    ])

    # ABA 1: VISÃO OPERACIONAL
    with aba1:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Pendências Listadas", len(df_visao))
        k2.metric("Jovens Únicos Sem Acesso", df_visao["Jovem"].nunique())
        k3.metric("☀️ Manhã (M)", len(df_visao[df_visao["Turno"].astype(str).str.startswith("M")]))
        k4.metric("🌤️ Tarde (V)", len(df_visao[df_visao["Turno"].astype(str).str.startswith("V")]))

        busca = st.text_input("🔍 Buscar jovem específico:")
        df_show = df_visao[df_visao["Jovem"].astype(str).str.contains(busca, case=False, na=False)] if busca else df_visao
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    # ABA 2: COMPARATIVO ENTRE DUAS COLETAS (SEMANAL OU INÍCIO vs FIM DA SEMANA)
    with aba2:
        st.subheader("📈 Comparação Entre Coletas (Ex: Segunda-feira vs. Sexta-feira ou Semana Passada vs. Atual)")
        datas_unicas = sorted(df_base_filtro["Data_Coleta"].unique().tolist())

        if len(datas_unicas) < 2:
            st.info(
                "💡 Para usar o Comparativo Semanal, registre pelo menos **2 coletas em datas diferentes** "
                "(por exemplo, a coleta do dia em que você enviou os e-mails e uma nova coleta dias depois)."
            )
        else:
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                data_antiga = st.selectbox("1️⃣ Coleta Inicial (Antes / Cobrança):", datas_unicas, index=max(0, len(datas_unicas) - 2))
            with c_d2:
                data_nova = st.selectbox("2️⃣ Coleta Recente (Depois / Conferência):", datas_unicas, index=len(datas_unicas) - 1)

            df_ant = df_base_filtro[df_base_filtro["Data_Coleta"] == data_antiga]
            df_nov = df_base_filtro[df_base_filtro["Data_Coleta"] == data_nova]

            # Chave única de pendência: Turma + Atividade + Jovem
            chaves_cols = ["Turma", "Turno", "Instrutor", "Atividade", "Jovem"]
            comp = pd.merge(
                df_ant[chaves_cols],
                df_nov[chaves_cols],
                on=["Turma", "Atividade", "Jovem"],
                how="outer",
                suffixes=("_Antes", "_Depois"),
                indicator=True
            )

            regularizados = comp[comp["_merge"] == "left_only"]   # Estava sem acesso antes e sumiu da lista de sem acesso!
            continuam_pend = comp[comp["_merge"] == "both"]       # Continua sem acesso nas duas coletas
            novos_pend = comp[comp["_merge"] == "right_only"]     # Nova pendência que surgiu

            taxa_conv = (len(regularizados) / len(df_ant) * 100) if len(df_ant) > 0 else 0.0

            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
            m_c1.metric("Pendências na 1ª Coleta", len(df_ant))
            m_c2.metric("✅ Regularizaram (Fizeram!)", len(regularizados), delta=f"{taxa_conv:.1f}% resolvido")
            m_c3.metric("🚨 Continuam Pendentes", len(continuam_pend), delta_color="inverse")
            m_c4.metric("🆕 Novas Pendências", len(novos_pend))

            sub_reg, sub_pend = st.tabs(["✅ Jovens que Regularizaram após o E-mail", "🚨 Jovens que Ainda Não Fizeram"])
            with sub_reg:
                st.dataframe(regularizados[["Turma", "Atividade", "Jovem"]], use_container_width=True, hide_index=True)
            with sub_pend:
                st.dataframe(continuam_pend[["Turma", "Atividade", "Jovem"]], use_container_width=True, hide_index=True)

    # ABA 3: VISÃO MENSAL E REINCIDÊNCIA
    with aba3:
        st.subheader("🗓️ Consolidação Mensal e Ranking de Reincidência")
        meses_disp = sorted(df_base_filtro["Mes_Ano"].unique().tolist(), reverse=True)
        sel_mes = st.selectbox("Selecione o Mês de Referência:", meses_disp)

        df_mes = df_base_filtro[df_base_filtro["Mes_Ano"] == sel_mes]

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("**📊 Evolução de Pendências por Data de Coleta no Mês:**")
            evolucao_data = df_mes.groupby("Data_Coleta")["Jovem"].count()
            st.bar_chart(evolucao_data)
        with col_graf2:
            st.markdown("**🕒 Pendências Acumuladas no Mês por Turno (M vs V):**")
            evolucao_turno = df_mes.groupby("Turno")["Jovem"].count()
            st.bar_chart(evolucao_turno)

        st.markdown("#### 🚨 Ranking Mensal de Jovens Críticos (Mais Coletas/Atividades Sem Acesso no Mês)")
        ranking_mensal = (
            df_mes.groupby(["Jovem", "Turma", "Turno", "Instrutor"])
            .agg(
                Total_Apontamentos_No_Mes=("Atividade", "count"),
                Datas_Com_Pendencia=("Data_Coleta", lambda x: ", ".join(sorted(set(x)))),
                Atividades_Acumuladas=("Atividade", lambda x: " | ".join(sorted(set(x))))
            )
            .reset_index()
            .sort_values(by="Total_Apontamentos_No_Mes", ascending=False)
        )
        st.dataframe(ranking_mensal, use_container_width=True, hide_index=True)
