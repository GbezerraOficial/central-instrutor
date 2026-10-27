import streamlit as st
import pandas as pd
import io
import re
import csv
import zipfile
import hmac
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from datetime import datetime, date

st.set_page_config(
    page_title="Central do Instrutor - Painel Unificado",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# ESTILIZAÇÃO VISUAL AVANÇADA (MENUS E SUBMENUS DESTACADOS)
# ==============================================================================
st.markdown("""
<style>
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
        transition: all 0.2s ease-in-out !important;
        border: 2px solid #334155 !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(56, 189, 248, 0.35) !important;
        border-color: #38bdf8 !important;
    }
    button[data-baseweb="tab"] {
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 12px 22px !important;
        margin-right: 8px !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        border: 1px solid #334155 !important;
        border-bottom: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: 2px solid #38bdf8 !important;
        box-shadow: 0 -4px 12px rgba(56, 189, 248, 0.3) !important;
    }
    div[data-testid="stMetric"] {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-left: 5px solid #38bdf8;
        padding: 12px 16px;
        border-radius: 10px;
    }
    .banner-modulo {
        padding: 16px 22px;
        border-radius: 12px;
        margin-bottom: 18px;
        color: white;
        font-family: Arial, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. BANCO DE TURMAS DOS 8 INSTRUTORES E FUNÇÕES DE FIDELIDADE DE DADOS
# ==============================================================================
UFS_BRASIL = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
}

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

MAPA_TURMA_INSTRUTORES = {}
SET_TURMAS_POR_INSTRUTOR = {}

for inst, turnos in BANCO_TURMAS.items():
    SET_TURMAS_POR_INSTRUTOR[inst] = set()
    for cod in turnos["M"] + turnos["V"]:
        cod_norm = cod.strip().lstrip("0").upper()
        SET_TURMAS_POR_INSTRUTOR[inst].add(cod_norm)
        if cod_norm not in MAPA_TURMA_INSTRUTORES:
            MAPA_TURMA_INSTRUTORES[cod_norm] = []
        if inst not in MAPA_TURMA_INSTRUTORES[cod_norm]:
            MAPA_TURMA_INSTRUTORES[cod_norm].append(inst)

def identificar_instrutor(cod_turma):
    limpo = str(cod_turma).strip().lstrip("0").upper()
    if limpo in MAPA_TURMA_INSTRUTORES:
        return " / ".join(MAPA_TURMA_INSTRUTORES[limpo])
    for k, lista_inst in MAPA_TURMA_INSTRUTORES.items():
        if k in limpo or limpo in k:
            return " / ".join(lista_inst)
    return "Não Mapeado / Outros"

def filtrar_df_por_instrutor(df_alvo, nome_instrutor):
    if nome_instrutor == "🌟 Todos os Instrutores":
        return df_alvo
    if nome_instrutor == "Não Mapeado / Outros":
        return df_alvo[df_alvo["Instrutor"] == "Não Mapeado / Outros"]
    codigos_inst = SET_TURMAS_POR_INSTRUTOR.get(nome_instrutor, set())
    turmas_norm = df_alvo["Turma"].astype(str).str.strip().str.lstrip("0").str.upper()
    mask_turma = turmas_norm.isin(codigos_inst)
    mask_nome = df_alvo["Instrutor"].astype(str).str.contains(nome_instrutor, case=False, na=False)
    return df_alvo[mask_turma | mask_nome]

def identificar_turno(cod_turma, nome_arq=""):
    c = str(cod_turma).upper()
    if "M." in c:
        return "M - Manhã"
    if "V." in c:
        return "V - Tarde"
    n = str(nome_arq).upper()
    if "_M." in n or "/MAT/" in n or "\\MAT\\" in n or "MAT" in n:
        return "M - Manhã"
    if "_V." in n or "/VES/" in n or "\\VES\\" in n or "VES" in n:
        return "V - Tarde"
    return "Outro"

def separar_cidade_estado(texto_cid_uf):
    """Divide 'CAMPO GRANDE / MS' validando a sigla oficial das 27 UFs."""
    txt = str(texto_cid_uf).strip()
    if not txt or txt.lower() in ("nan", "none"):
        return "", ""
    for sep in ["/", " - ", "-"]:
        if sep in txt:
            partes = txt.rsplit(sep, 1)
            uf_cand = partes[1].strip().upper()
            if len(uf_cand) == 2 and uf_cand in UFS_BRASIL:
                return partes[0].strip(), uf_cand
    return txt, ""

def eh_cidade_uf(val):
    _, uf = separar_cidade_estado(val)
    return uf != "" and uf in UFS_BRASIL

def extrair_codigo_apc_turma(cod_turma):
    """Extrai o código base da disciplina dentro da turma (ex: APC09, APC02, APC01, APC00)."""
    m = re.search(r"(APC\.?\d+)", str(cod_turma).upper())
    return m.group(1).replace(".", "") if m else ""

def extrair_data_nome_arquivo(nome_arq, data_fallback):
    m = re.search(r"(\d{2})[-._](\d{2})[-._](\d{4})", str(nome_arq))
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return data_fallback

def calcular_semana_ano(data_iso):
    try:
        dt = datetime.strptime(str(data_iso)[:10], "%Y-%m-%d").date()
        return f"{dt.year}-Semana {dt.isocalendar()[1]:02d}"
    except Exception:
        return "Semana Atual"

def padronizar_base_faltas(df):
    """Garante integridade de todas as colunas da base de Faltas."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "Lancado_RM" not in df.columns:
        df.insert(0, "Lancado_RM", False)
    df["Lancado_RM"] = df["Lancado_RM"].fillna(False).astype(bool)
    if "Nome" not in df.columns and "Jovem" in df.columns:
        df["Nome"] = df["Jovem"]
    if "Matricula" not in df.columns and "ID_Jovem" in df.columns:
        df["Matricula"] = df["ID_Jovem"]
    df["Matricula"] = df["Matricula"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    if "Cidade" not in df.columns:
        if "Cidade_UF" in df.columns:
            pares = df["Cidade_UF"].apply(separar_cidade_estado)
            df["Cidade"] = [p[0] for p in pares]
            df["Estado"] = [p[1] for p in pares]
        else:
            df["Cidade"] = ""
            df["Estado"] = ""
    if "Disciplina" not in df.columns:
        if "Modulo_Sigla" in df.columns:
            df["Disciplina"] = df["Modulo_Sigla"].fillna("").astype(str)
        else:
            df["Disciplina"] = df["Turma"].apply(extrair_codigo_apc_turma)
    df["Disciplina"] = df["Disciplina"].replace({"": "GERAL", "nan": "GERAL"}).fillna("GERAL")
    if "Data_Falta" not in df.columns:
        df["Data_Falta"] = date.today().strftime("%Y-%m-%d")
    df["Data_Falta"] = df["Data_Falta"].astype(str).str.slice(0, 10)
    df["Semana_Ano"] = df["Data_Falta"].apply(calcular_semana_ano)
    df["Mes_Ano"] = df["Data_Falta"].str.slice(0, 7)
    df["Instrutor"] = df["Turma"].apply(identificar_instrutor)
    df["Turno"] = df.apply(lambda r: identificar_turno(r.get("Turma", ""), r.get("Arquivo_Origem", "")), axis=1)
    return df

def padronizar_base_moodle(df):
    """Garante integridade de todas as colunas da base do Moodle."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if "Data_Coleta" not in df.columns:
        df.insert(0, "Data_Coleta", date.today().strftime("%Y-%m-%d"))
    df["Data_Coleta"] = df["Data_Coleta"].astype(str).str.slice(0, 10)
    df["Semana_Ano"] = df["Data_Coleta"].apply(calcular_semana_ano)
    df["Mes_Ano"] = df["Data_Coleta"].str.slice(0, 7)
    if "Jovem" not in df.columns and "Nome" in df.columns:
        df["Jovem"] = df["Nome"]
    if "Turma" not in df.columns:
        df["Turma"] = "GERAL"
    df["Instrutor"] = df["Turma"].apply(identificar_instrutor)
    df["Turno"] = df["Turma"].apply(identificar_turno)
    if "Disciplina" not in df.columns:
        if "Encontro" in df.columns:
            df["Disciplina"] = df.apply(
                lambda r: f"{extrair_codigo_apc_turma(r['Turma'])} - {r['Encontro']}".strip(" -")
                if extrair_codigo_apc_turma(r["Turma"]) else str(r["Encontro"]),
                axis=1
            )
        else:
            df["Disciplina"] = df["Turma"].apply(lambda t: extrair_codigo_apc_turma(t) or "GERAL")
    return df

# ==============================================================================
# 2. LEITOR UNIVERSAL DE PLANILHAS (.XLS, .XLSX, HTML, XML, CSV, ZIP)
# ==============================================================================
class ExtratorTabelaHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.linhas = []
        self.linha_atual = []
        self.em_celula = False
        self.texto_celula = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "tr":
            self.linha_atual = []
        elif t in ("td", "th"):
            self.em_celula = True
            self.texto_celula = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("td", "th") and self.em_celula:
            self.linha_atual.append("".join(self.texto_celula).strip())
            self.em_celula = False
        elif t == "tr" and self.linha_atual:
            if any(c != "" for c in self.linha_atual):
                self.linhas.append(self.linha_atual)

    def handle_data(self, data):
        if self.em_celula:
            self.texto_celula.append(data)

def ler_xml_excel_2003(texto_xml):
    try:
        root = ET.fromstring(texto_xml)
        linhas = []
        for elem in root.iter():
            if elem.tag.endswith("Row"):
                linha = ["".join(c.itertext()).strip() for c in elem if c.tag.endswith("Cell")]
                if any(c != "" for c in linha):
                    linhas.append(linha)
        if linhas:
            return pd.DataFrame(linhas)
    except Exception:
        pass
    return None

def converter_bytes_em_dataframe(bytes_arq, nome_arq):
    if not bytes_arq or len(bytes_arq) < 60 or nome_arq.startswith("~$"):
        return None, "vazio"

    for eng in ["xlrd", "openpyxl"]:
        try:
            xls = pd.ExcelFile(io.BytesIO(bytes_arq), engine=eng)
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, header=None)
                if df is not None and not df.dropna(how="all").empty:
                    return df, f"excel ({eng})"
        except Exception:
            pass

    for enc in ["utf-8-sig", "utf-16", "latin-1", "cp1252"]:
        try:
            texto = bytes_arq.decode(enc, errors="ignore").strip()
            if not texto:
                continue
            if "<table" in texto.lower() or "<tr" in texto.lower():
                parser = ExtratorTabelaHTML()
                parser.feed(texto)
                if parser.linhas:
                    return pd.DataFrame(parser.linhas), "html_xls"
            if "<workbook" in texto.lower() or "<row" in texto.lower():
                df_xml = ler_xml_excel_2003(texto)
                if df_xml is not None and not df_xml.empty:
                    return df_xml, "xml_xls"
            linhas_txt = [l for l in texto.splitlines() if l.strip()]
            if linhas_txt:
                for sep in ["\t", ";", ","]:
                    if sep in linhas_txt[0] or (len(linhas_txt) > 1 and sep in linhas_txt[1]):
                        lidas = [r for r in csv.reader(linhas_txt, delimiter=sep) if any(c.strip() for c in r)]
                        if lidas and max(len(r) for r in lidas) >= 2:
                            return pd.DataFrame(lidas), f"csv ({sep})"
        except Exception:
            pass

    return None, "sem_dados"

def extrair_alunos_do_dataframe(df_raw, nome_arq, data_padrao_str):
    """Extração blindada contra colunas em branco (Fidelidade 100%)."""
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df_clean = df_raw.dropna(how="all")
    if df_clean.empty:
        return pd.DataFrame()

    nome_limpo = nome_arq.replace("\\", "/").split("/")[-1]
    data_falta = extrair_data_nome_arquivo(nome_limpo, data_padrao_str)
    semana_ano = calcular_semana_ano(data_falta)

    # Extrai o código da disciplina do nome da planilha (ex: EMP_UB02, INT_UA_03_6H, ProfiUB_04)
    disc_arquivo = re.split(r"\s*-\s*\d{2}[-._]\d{2}[-._]\d{4}", nome_limpo)[0]
    disc_arquivo = re.sub(r"\.(xlsx?|csv|tsv)$", "", disc_arquivo, flags=re.I).strip()

    registros = []

    for _, row in df_clean.iterrows():
        valores = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() not in ("", "nan", "None")]
        if len(valores) < 2:
            continue

        linha_upper = " ".join(valores).upper()
        if linha_upper.startswith("ID ") or ("NOME" in linha_upper and "TURMA" in linha_upper and "@" not in linha_upper):
            continue

        # 1. Turma (Col J ou padrão APC)
        turma = next((v for v in valores if re.search(r"(APC\.?\d+|\d+\.[A-Z0-9]+\.\d+[MV])", v, re.I)), "")
        if not turma and len(row) > 9 and pd.notna(row.iloc[9]):
            turma = str(row.iloc[9]).strip()

        # 2. Email
        email = next((v for v in valores if "@" in v and "." in v), "")

        # 3. Cidade e Estado (Validação estrita das 27 UFs do Brasil)
        cid_uf_val = next((v for v in valores if eh_cidade_uf(v)), "")
        if not cid_uf_val and len(row) > 5 and pd.notna(row.iloc[5]) and eh_cidade_uf(row.iloc[5]):
            cid_uf_val = str(row.iloc[5]).strip()
        cidade, estado = separar_cidade_estado(cid_uf_val)

        # 4. Matrícula (Col A ou primeiro número de matrícula)
        matricula = ""
        val0_limpo = re.sub(r"\.0$", "", valores[0])
        if re.match(r"^\d{3,12}$", val0_limpo):
            matricula = val0_limpo

        # 5. Nome do Jovem
        nome_jovem = ""
        if matricula and len(valores) >= 2:
            nome_jovem = valores[1]
        elif email and valores.index(email) >= 1:
            nome_jovem = valores[valores.index(email) - 1]
        else:
            nome_jovem = valores[0]

        # 6. Código da Disciplina (Coluna D = índice 3 da planilha ou prefixo do ficheiro)
        disciplina = ""
        if len(row) > 3 and pd.notna(row.iloc[3]):
            cand_d = str(row.iloc[3]).strip()
            if cand_d and cand_d not in (matricula, nome_jovem, email, cid_uf_val, turma) and not eh_cidade_uf(cand_d):
                disciplina = cand_d
        if not disciplina:
            usados = {matricula, valores[0], nome_jovem, email, cid_uf_val, turma}
            for v in valores:
                if v not in usados and not re.match(r"^\d{2}/\d{2}/\d{4}$", v) and not v.lower().startswith("encontro"):
                    disciplina = v
                    break
        if not disciplina:
            disciplina = disc_arquivo or extrair_codigo_apc_turma(turma) or "GERAL"

        if not turma:
            turma = disciplina
        if len(nome_jovem) < 3 or nome_jovem.isdigit():
            continue

        registros.append({
            "Lancado_RM": False,
            "Matricula": matricula,
            "Nome": re.sub(r"\s+", " ", nome_jovem).strip(),
            "Cidade": cidade,
            "Estado": estado,
            "Disciplina": disciplina,
            "Turma": turma,
            "Turno": identificar_turno(turma, nome_arq),
            "Instrutor": identificar_instrutor(turma),
            "Data_Falta": data_falta,
            "Semana_Ano": semana_ano,
            "Mes_Ano": data_falta[:7],
            "Arquivo_Origem": nome_limpo
        })

    return pd.DataFrame(registros)

def processar_arquivos_enviados(lista_arquivos, data_padrao_str):
    dfs_extraidos = []
    stats = {"total_arquivos": 0, "com_faltas": 0, "em_branco": 0, "detalhes": []}

    def processar_item_bytes(b_arq, nome_item):
        stats["total_arquivos"] += 1
        nome_curto = nome_item.replace("\\", "/").split("/")[-1]
        df_bruto, formato = converter_bytes_em_dataframe(b_arq, nome_curto)
        if df_bruto is not None:
            df_limpo = extrair_alunos_do_dataframe(df_bruto, nome_item, data_padrao_str)
            if not df_limpo.empty:
                dfs_extraidos.append(df_limpo)
                stats["com_faltas"] += 1
                stats["detalhes"].append(f"✅ {nome_curto}: {len(df_limpo)} jovens ({formato})")
            else:
                stats["em_branco"] += 1
                stats["detalhes"].append(f"⚪ {nome_curto}: Sem alunos ({len(b_arq)} bytes)")
        else:
            stats["em_branco"] += 1
            stats["detalhes"].append(f"⚪ {nome_curto}: Ficheiro em branco ({len(b_arq)} bytes)")

    def abrir_zip_recursivo(bytes_zip):
        with zipfile.ZipFile(io.BytesIO(bytes_zip), "r") as z:
            for item in z.namelist():
                if item.endswith("/") or "__MACOSX" in item or item.split("/")[-1].startswith("~$"):
                    continue
                item_lower = item.lower()
                if item_lower.endswith(".zip"):
                    abrir_zip_recursivo(z.read(item))
                elif item_lower.endswith((".xls", ".xlsx", ".csv", ".tsv")):
                    processar_item_bytes(z.read(item), item)

    for arq in lista_arquivos:
        conteudo = arq.getvalue()
        if arq.name.lower().endswith(".zip"):
            try:
                abrir_zip_recursivo(conteudo)
            except Exception as e:
                stats["detalhes"].append(f"❌ Erro ao abrir ZIP {arq.name}: {e}")
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
    senha_dig = st.text_input("Digite a sua senha de acesso:", type="password")
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

# ==============================================================================
# 4. BARRA LATERAL: BACKUP UNIFICADO (.XLSX)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🗄️ BACKUP HISTÓRICO (.XLSX)")
    st.caption("Guarde ou restaure toda a base (Faltas + Moodle) num único ficheiro Excel:")
    arq_hist = st.file_uploader("📂 Restaurar Histórico Salvo:", type=["xlsx"])
    if arq_hist and st.button("🔄 Carregar Histórico", use_container_width=True):
        xls = pd.ExcelFile(arq_hist)
        if "Historico_Moodle" in xls.sheet_names:
            st.session_state["base_moodle"] = padronizar_base_moodle(pd.read_excel(xls, "Historico_Moodle"))
        if "Historico_Faltas" in xls.sheet_names:
            st.session_state["base_faltas"] = padronizar_base_faltas(pd.read_excel(xls, "Historico_Faltas"))
        st.success("✅ Histórico restaurado e validado!")
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
# 5. MENU PRINCIPAL COM ALTO DESTAQUE VISUAL
# ==============================================================================
st.markdown("## 🧭 Menu Principal de Módulos")
qtd_faltas = len(st.session_state["base_faltas"])
qtd_moodle = len(st.session_state["base_moodle"])

nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button(f"🟧 1. CONTROLE DE FALTAS ({qtd_faltas} registos)", use_container_width=True, type="primary" if st.session_state["modulo_ativo"] == "FALTAS" else "secondary"):
        st.session_state["modulo_ativo"] = "FALTAS"
        st.rerun()
with nav2:
    if st.button(f"🟦 2. ATIVIDADES MOODLE ({qtd_moodle} registos)", use_container_width=True, type="primary" if st.session_state["modulo_ativo"] == "MOODLE" else "secondary"):
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
            Foco fidedigno: <b>Matrícula, Nome, Cidade, Estado, Disciplina, Turma e Turno</b> filtrados por <b>Instrutor</b> e <b>Código da Disciplina</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR FOLHAS DE CÁLCULO OU PACOTE .ZIP DE FALTAS", expanded=st.session_state["base_faltas"].empty):
        c_dt, c_up = st.columns([1, 2.5])
        with c_dt:
            data_ref = st.date_input("📅 Data padrão:", value=date.today(), format="DD/MM/YYYY")
            if st.button("🗑️ Limpar Base de Faltas", use_container_width=True):
                st.session_state["base_faltas"] = pd.DataFrame()
                st.session_state["ultimos_arquivos_lidos"] = []
                st.session_state.pop("ultimo_diagnostico", None)
                st.rerun()

        with c_up:
            arquivos_up = st.file_uploader(
                "Arraste aqui o ficheiro .ZIP ou as folhas de cálculo (.xls / .xlsx):",
                type=["zip", "xls", "xlsx", "csv", "tsv"],
                accept_multiple_files=True,
                key="uploader_faltas_auto"
            )

        if arquivos_up:
            assinatura_atual = [f"{a.name}_{a.size}" for a in arquivos_up]
            if st.session_state.get("ultimos_arquivos_lidos") != assinatura_atual:
                with st.spinner("A analisar ficheiros e a validar integridade dos dados..."):
                    df_novos, stats = processar_arquivos_enviados(arquivos_up, data_ref.strftime("%Y-%m-%d"))
                    st.session_state["ultimos_arquivos_lidos"] = assinatura_atual
                    st.session_state["ultimo_diagnostico"] = stats

                    if not df_novos.empty:
                        df_acum = pd.concat([st.session_state["base_faltas"], df_novos], ignore_index=True)
                        df_acum = padronizar_base_faltas(df_acum)
                        # Chave de integridade inclui Disciplina para não perder faltas do mesmo jovem em disciplinas distintas
                        df_acum = df_acum.drop_duplicates(
                            subset=["Data_Falta", "Disciplina", "Turma", "Matricula", "Nome"], keep="first"
                        ).reset_index(drop=True)
                        st.session_state["base_faltas"] = df_acum

        if "ultimo_diagnostico" in st.session_state:
            st_diag = st.session_state["ultimo_diagnostico"]
            st.info(
                f"🔍 **Diagnóstico da Leitura:** **{st_diag['total_arquivos']}** ficheiros processados "
                f"| ✅ **{st_diag['com_faltas']}** continham jovens ausentes "
                f"| ⚪ **{st_diag['em_branco']}** estavam em branco (810 bytes)."
            )
            with st.expander("🔎 Ver detalhe ficheiro a ficheiro"):
                st.write("\n".join(st_diag["detalhes"]))

    if not st.session_state["base_faltas"].empty:
        st.session_state["base_faltas"] = padronizar_base_faltas(st.session_state["base_faltas"])
        df_f = st.session_state["base_faltas"]

        # ======================================================================
        # BARRA DE FILTROS: INSTRUTOR + DISCIPLINAS + PERÍODO (DIA/SEMANA/MÊS) + TURNO
        # ======================================================================
        st.markdown("#### 🎯 Filtros de Trabalho (Instrutor, Código da Disciplina, Período e Turno)")
        f1, f2, f3, f4, f5, f6 = st.columns([1.4, 1.4, 0.9, 1.1, 0.9, 1.2])

        with f1:
            opcoes_instrutor = ["🌟 Todos os Instrutores"] + list(BANCO_TURMAS.keys()) + ["Não Mapeado / Outros"]
            sel_instrutor_f = st.selectbox("👤 1. Instrutor(a):", opcoes_instrutor, index=0, key="f_inst")

        with f3:
            modo_tempo_f = st.selectbox("🗓️ 3. Modo:", ["📅 Dia", "📆 Semana", "🗓️ Mês", "♾️ Tudo"], index=0, key="f_modo")

        with f4:
            if modo_tempo_f == "📅 Dia":
                opcoes_p = ["Todos os Dias"] + sorted(df_f["Data_Falta"].astype(str).unique().tolist(), reverse=True)
                sel_periodo_f = st.selectbox("Escolher Dia:", opcoes_p, key="f_dia")
            elif modo_tempo_f == "📆 Semana":
                opcoes_p = ["Todas as Semanas"] + sorted(df_f["Semana_Ano"].astype(str).unique().tolist(), reverse=True)
                sel_periodo_f = st.selectbox("Escolher Semana:", opcoes_p, key="f_sem")
            elif modo_tempo_f == "🗓️ Mês":
                opcoes_p = ["Todos os Meses"] + sorted(df_f["Mes_Ano"].astype(str).unique().tolist(), reverse=True)
                sel_periodo_f = st.selectbox("Escolher Mês:", opcoes_p, key="f_mes")
            else:
                sel_periodo_f = "Tudo"
                st.text_input("Período:", value="Todo o Histórico", disabled=True)

        # Filtra primeiro por Instrutor e Período para montar a lista exata de Disciplinas disponíveis naquele Dia/Semana/Mês
        df_sub = filtrar_df_por_instrutor(df_f, sel_instrutor_f)
        if modo_tempo_f == "📅 Dia" and sel_periodo_f != "Todos os Dias":
            df_sub = df_sub[df_sub["Data_Falta"] == sel_periodo_f]
        elif modo_tempo_f == "📆 Semana" and sel_periodo_f != "Todas as Semanas":
            df_sub = df_sub[df_sub["Semana_Ano"] == sel_periodo_f]
        elif modo_tempo_f == "🗓️ Mês" and sel_periodo_f != "Todos os Meses":
            df_sub = df_sub[df_sub["Mes_Ano"] == sel_periodo_f]

        with f2:
            # Reúne códigos de disciplina da planilha (ex: EMP_UB02) e códigos APC das turmas (ex: APC09)
            codigos_disc = sorted(df_sub["Disciplina"].dropna().astype(str).unique().tolist())
            codigos_apc = sorted(list({extrair_codigo_apc_turma(t) for t in df_sub["Turma"].dropna() if extrair_codigo_apc_turma(t)}))
            opcoes_disc_f = ["Todas as Disciplinas"] + codigos_disc + [f"Código Turma: {a}" for a in codigos_apc if a not in codigos_disc]
            sel_disc_f = st.selectbox("📘 2. Código da Disciplina:", opcoes_disc_f, index=0, key="f_disc")

        with f5:
            sel_turno_f = st.selectbox("🕒 4. Turno:", ["Todos (M + V)", "M - Manhã", "V - Tarde"], key="f_turno")

        with f6:
            busca_f = st.text_input("🔍 5. Busca Livre:", placeholder="Nome, Matrícula, Disciplina...", key="f_busca")

        # Aplica o filtro de Disciplina
        if sel_disc_f != "Todas as Disciplinas":
            if sel_disc_f.startswith("Código Turma: "):
                apc_alvo = sel_disc_f.replace("Código Turma: ", "").strip()
                df_sub = df_sub[df_sub["Turma"].astype(str).str.upper().str.contains(apc_alvo, na=False)]
            else:
                df_sub = df_sub[df_sub["Disciplina"] == sel_disc_f]

        if sel_turno_f != "Todos (M + V)":
            df_sub = df_sub[df_sub["Turno"] == sel_turno_f]

        if busca_f:
            termo = busca_f.strip()
            df_sub = df_sub[
                df_sub["Nome"].astype(str).str.contains(termo, case=False, na=False) |
                df_sub["Matricula"].astype(str).str.contains(termo, case=False, na=False) |
                df_sub["Disciplina"].astype(str).str.contains(termo, case=False, na=False) |
                df_sub["Turma"].astype(str).str.contains(termo, case=False, na=False) |
                df_sub["Cidade"].astype(str).str.contains(termo, case=False, na=False) |
                df_sub["Estado"].astype(str).str.contains(termo, case=False, na=False)
            ]

        if df_sub.empty:
            st.warning(
                "⚠️ Nenhum registo encontrado para esta combinação de filtros. "
                "Experimente selecionar **'🌟 Todos os Instrutores'** ou **'Todas as Disciplinas'**."
            )
        else:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Jovens Ausentes", len(df_sub))
            m2.metric("Disciplinas Ativas", df_sub["Disciplina"].nunique())
            m3.metric("Turmas no Filtro", df_sub["Turma"].nunique())
            m4.metric("☀️ Manhã (M)", len(df_sub[df_sub["Turno"] == "M - Manhã"]))
            m5.metric("🌤️ Tarde (V)", len(df_sub[df_sub["Turno"] == "V - Tarde"]))

            sub_f1, sub_f2, sub_f3 = st.tabs([
                "📋 1. RELAÇÃO DE JOVENS AUSENTES (DIA / SEMANA / MÊS)",
                "🚨 2. RANKING DE REINCIDÊNCIA (QUEM MAIS FALTA)",
                "📘 3. RESUMO POR DISCIPLINA E TURMA"
            ])

            colunas_foco = ["Lancado_RM", "Matricula", "Nome", "Cidade", "Estado", "Disciplina", "Turma", "Turno", "Data_Falta", "Instrutor"]
            cols_existentes = [c for c in colunas_foco if c in df_sub.columns]

            with sub_f1:
                df_ordenado = df_sub[cols_existentes].sort_values(by=["Turno", "Disciplina", "Turma", "Nome"])
                df_editado = st.data_editor(
                    df_ordenado,
                    use_container_width=True,
                    hide_index=True,
                    key="editor_faltas_rm",
                    column_config={
                        "Lancado_RM": st.column_config.CheckboxColumn("✅ RM", default=False),
                        "Matricula": st.column_config.TextColumn("Matrícula do Jovem"),
                        "Nome": st.column_config.TextColumn("Nome"),
                        "Cidade": st.column_config.TextColumn("Cidade"),
                        "Estado": st.column_config.TextColumn("Estado"),
                        "Disciplina": st.column_config.TextColumn("Disciplina"),
                        "Turma": st.column_config.TextColumn("Turma"),
                        "Turno": st.column_config.TextColumn("Turno"),
                        "Data_Falta": st.column_config.TextColumn("Data"),
                        "Instrutor": st.column_config.TextColumn("Instrutor(a)")
                    }
                )
                # Preserva a marcação do checkbox RM na base principal sem perder ao mudar de filtro
                st.session_state["base_faltas"].loc[df_editado.index, "Lancado_RM"] = df_editado["Lancado_RM"]

            with sub_f2:
                rank_f = (
                    df_sub.groupby(["Matricula", "Nome", "Cidade", "Estado", "Turma", "Turno"])
                    .agg(
                        Total_Faltas=("Data_Falta", "count"),
                        Disciplinas=("Disciplina", lambda x: ", ".join(sorted(set(str(v) for v in x)))),
                        Datas_Ausente=("Data_Falta", lambda x: ", ".join(sorted(set(str(v) for v in x))))
                    )
                    .reset_index()
                    .sort_values(by="Total_Faltas", ascending=False)
                )
                st.dataframe(rank_f, use_container_width=True, hide_index=True)

            with sub_f3:
                resumo_t = (
                    df_sub.groupby(["Turno", "Disciplina", "Turma", "Instrutor"])
                    .agg(Total_Ausencias=("Nome", "count"), Jovens_Unicos=("Nome", "nunique"))
                    .reset_index()
                    .sort_values(by=["Turno", "Total_Ausencias"], ascending=[True, False])
                )
                st.dataframe(resumo_t, use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 2: ATIVIDADES MOODLE (COM FILTRO DE DISCIPLINAS + UPLOAD DE PLANILHAS)
# ==============================================================================
elif st.session_state["modulo_ativo"] == "MOODLE":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #0284c7 0%, #1d4ed8 100%); border-left: 8px solid #bae6fd;">
        <h2 style="margin:0;color:white;">🟦 MÓDULO: Acompanhamento de Atividades (Moodle Demà Digital)</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Importação por Texto ou Planilhas (<b>.TSV, .CSV, .XLSX, .XLS</b>) e filtro por <b>Instrutor</b> e <b>Código da Disciplina</b> (Dia, Semana e Mês).
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 ADICIONAR COLETA DO MOODLE (COLAR TEXTO OU CARREGAR PLANILHAS)", expanded=st.session_state["base_moodle"].empty):
        cm1, cm2 = st.columns(2)
        with cm1:
            dt_moodle = st.date_input("📅 Data da Coleta:", value=date.today(), format="DD/MM/YYYY", key="dt_m_in")
        with cm2:
            disc_moodle_in = st.text_input(
                "📘 Código da Disciplina / Módulo (ex: EMP_UB04, Bancário, ID 2007):",
                value="",
                placeholder="Se deixar em branco, identifica automaticamente pela Turma/Relatório",
                key="disc_m_in"
            )

        col_in_m1, col_in_m2 = st.columns(2)
        with col_in_m1:
            txt_m = st.text_area(
                "Opção A: Cole (Ctrl+V) o relatório copiado pela Extensão do Moodle:",
                height=135,
                placeholder="Instrutor\tTurno\tTurma\tAtividade\tStatus\tJovem\tEmail_Enviado"
            )
        with col_in_m2:
            arqs_moodle_up = st.file_uploader(
                "Opção B: Carregar Planilhas / Ficheiros do Moodle (.tsv, .csv, .xlsx, .xls):",
                type=["tsv", "csv", "txt", "xlsx", "xls"],
                accept_multiple_files=True,
                key="uploader_moodle_files"
            )

        bm1, bm2 = st.columns([2, 1])
        with bm1:
            if st.button("➕ Guardar Coleta no Painel", type="primary", use_container_width=True):
                novos_m = []
                if txt_m.strip():
                    try:
                        novos_m.append(pd.read_csv(io.StringIO(txt_m.strip()), sep="\t"))
                    except Exception as e:
                        st.error(f"Erro ao ler texto colado: {e}")

                if arqs_moodle_up:
                    for arq_m in arqs_moodle_up:
                        try:
                            nome_m = arq_m.name.lower()
                            if nome_m.endswith((".xlsx", ".xls")):
                                df_m_arq, _ = converter_bytes_em_dataframe(arq_m.getvalue(), arq_m.name)
                                if df_m_arq is not None and not df_m_arq.empty:
                                    # Usa a primeira linha como cabeçalho se contiver 'Turma' ou 'Jovem'
                                    prim_linha = [str(x).strip() for x in df_m_arq.iloc[0].values]
                                    if any(k in " ".join(prim_linha).upper() for k in ["TURMA", "JOVEM", "ATIVIDADE"]):
                                        df_m_arq.columns = prim_linha
                                        df_m_arq = df_m_arq.iloc[1:].reset_index(drop=True)
                                    novos_m.append(df_m_arq)
                            else:
                                conteudo_m = arq_m.getvalue().decode("utf-8-sig", errors="ignore")
                                sep_m = "\t" if "\t" in conteudo_m else (";" if ";" in conteudo_m else ",")
                                novos_m.append(pd.read_csv(io.StringIO(conteudo_m), sep=sep_m))
                        except Exception as e:
                            st.error(f"Erro ao ler ficheiro {arq_m.name}: {e}")

                if novos_m:
                    df_lote = pd.concat(novos_m, ignore_index=True)
                    dt_str = dt_moodle.strftime("%Y-%m-%d")
                    df_lote["Data_Coleta"] = dt_str
                    if disc_moodle_in.strip():
                        df_lote["Disciplina"] = disc_moodle_in.strip()
                    elif "Disciplina" not in df_lote.columns and "Turma" in df_lote.columns:
                        df_lote["Disciplina"] = df_lote["Turma"].apply(lambda t: extrair_codigo_apc_turma(t) or "GERAL")

                    df_comb_m = pd.concat([st.session_state["base_moodle"], df_lote], ignore_index=True)
                    df_comb_m = padronizar_base_moodle(df_comb_m)
                    df_comb_m = df_comb_m.drop_duplicates(
                        subset=["Data_Coleta", "Disciplina", "Turma", "Atividade", "Jovem"], keep="last"
                    ).reset_index(drop=True)
                    st.session_state["base_moodle"] = df_comb_m
                    st.success("✅ Coleta do Moodle guardada com sucesso!")
                    st.rerun()
        with bm2:
            if st.button("🗑️ Limpar Base do Moodle", use_container_width=True):
                st.session_state["base_moodle"] = pd.DataFrame()
                st.rerun()

    if not st.session_state["base_moodle"].empty:
        st.session_state["base_moodle"] = padronizar_base_moodle(st.session_state["base_moodle"])
        df_m = st.session_state["base_moodle"]

        st.markdown("#### 🎯 Filtrar Atividades por Instrutor, Código da Disciplina e Período (Dia, Semana ou Mês)")
        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns([1.4, 1.4, 0.9, 1.1, 0.9, 1.2])
        with mc1:
            opcoes_inst_m = ["🌟 Todos os Instrutores"] + list(BANCO_TURMAS.keys()) + ["Não Mapeado / Outros"]
            sel_inst_m = st.selectbox("👤 1. Instrutor(a):", opcoes_inst_m, index=0, key="m_inst")
        with mc3:
            modo_m = st.selectbox("🗓️ 3. Modo:", ["📅 Dia", "📆 Semana", "🗓️ Mês", "♾️ Tudo"], index=0, key="m_modo")
        with mc4:
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
        if modo_m == "📅 Dia" and sel_per_m != "Todos os Dias":
            df_m_sub = df_m_sub[df_m_sub["Data_Coleta"] == sel_per_m]
        elif modo_m == "📆 Semana" and sel_per_m != "Todas as Semanas":
            df_m_sub = df_m_sub[df_m_sub["Semana_Ano"] == sel_per_m]
        elif modo_m == "🗓️ Mês" and sel_per_m != "Todos os Meses":
            df_m_sub = df_m_sub[df_m_sub["Mes_Ano"] == sel_per_m]

        with mc2:
            disc_m_disp = sorted(df_m_sub["Disciplina"].dropna().astype(str).unique().tolist())
            apc_m_disp = sorted(list({extrair_codigo_apc_turma(t) for t in df_m_sub["Turma"].dropna() if extrair_codigo_apc_turma(t)}))
            opcoes_disc_m = ["Todas as Disciplinas"] + disc_m_disp + [f"Código Turma: {a}" for a in apc_m_disp if a not in disc_m_disp]
            sel_disc_m = st.selectbox("📘 2. Código da Disciplina:", opcoes_disc_m, index=0, key="m_disc")

        with mc5:
            sel_turno_m = st.selectbox("🕒 4. Turno:", ["Todos (M + V)", "M - Manhã", "V - Tarde"], key="m_turno")
        with mc6:
            busca_m = st.text_input("🔍 5. Busca Livre:", placeholder="Jovem, Atividade, Disciplina...", key="m_busca")

        if sel_disc_m != "Todas as Disciplinas":
            if sel_disc_m.startswith("Código Turma: "):
                apc_alvo_m = sel_disc_m.replace("Código Turma: ", "").strip()
                df_m_sub = df_m_sub[df_m_sub["Turma"].astype(str).str.upper().str.contains(apc_alvo_m, na=False)]
            else:
                df_m_sub = df_m_sub[df_m_sub["Disciplina"] == sel_disc_m]

        if sel_turno_m != "Todos (M + V)":
            df_m_sub = df_m_sub[df_m_sub["Turno"] == sel_turno_m]
        if busca_m:
            df_m_sub = df_m_sub[
                df_m_sub["Jovem"].astype(str).str.contains(busca_m, case=False, na=False) |
                df_m_sub["Disciplina"].astype(str).str.contains(busca_m, case=False, na=False) |
                df_m_sub["Turma"].astype(str).str.contains(busca_m, case=False, na=False) |
                df_m_sub["Atividade"].astype(str).str.contains(busca_m, case=False, na=False)
            ]

        km1, km2, km3, km4, km5 = st.columns(5)
        km1.metric("Pendências Listadas", len(df_m_sub))
        km2.metric("Disciplinas no Filtro", df_m_sub["Disciplina"].nunique())
        km3.metric("Turmas no Filtro", df_m_sub["Turma"].nunique())
        km4.metric("☀️ Manhã (M)", len(df_m_sub[df_m_sub["Turno"] == "M - Manhã"]))
        km5.metric("🌤️ Tarde (V)", len(df_m_sub[df_m_sub["Turno"] == "V - Tarde"]))

        sub_m1, sub_m2 = st.tabs([
            "📋 1. PENDÊNCIAS POR INSTRUTOR E DISCIPLINA",
            "📈 2. COMPARATIVO SEMANAL / MENSAL (QUEM REGULARIZOU)"
        ])
        with sub_m1:
            cols_m_ordem = ["Data_Coleta", "Instrutor", "Disciplina", "Turno", "Turma", "Atividade", "Status", "Jovem", "Email_Enviado"]
            cols_m_pres = [c for c in cols_m_ordem if c in df_m_sub.columns]
            st.dataframe(df_m_sub[cols_m_pres], use_container_width=True, hide_index=True)
        with sub_m2:
            datas_m = sorted(df_m["Data_Coleta"].astype(str).unique().tolist())
            if len(datas_m) < 2:
                st.info("Registe pelo menos 2 datas diferentes de coleta para comparar quem regularizou na semana.")
            else:
                cd1, cd2 = st.columns(2)
                with cd1:
                    d_ant = st.selectbox("1ª Coleta (Cobrança Inicial):", datas_m, index=0)
                with cd2:
                    d_nov = st.selectbox("2ª Coleta (Conferência):", datas_m, index=len(datas_m)-1)
                df_a = filtrar_df_por_instrutor(df_m[df_m["Data_Coleta"] == d_ant], sel_inst_m)
                df_n = filtrar_df_por_instrutor(df_m[df_m["Data_Coleta"] == d_nov], sel_inst_m)
                comp = pd.merge(df_a, df_n, on=["Turma", "Atividade", "Jovem"], how="outer", indicator=True)
                st.metric("✅ Jovens que Regularizaram após o E-mail", len(comp[comp["_merge"] == "left_only"]))
                st.dataframe(comp[comp["_merge"] == "left_only"][["Turma", "Atividade", "Jovem"]], use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 3: VISÃO 360º (CRUZAMENTO FALTAS + MOODLE)
# ==============================================================================
elif st.session_state["modulo_ativo"] == "VISAO360":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #059669 0%, #047857 100%); border-left: 8px solid #a7f3d0;">
        <h2 style="margin:0;color:white;">🟩 MÓDULO: Visão 360º do Jovem (Cruzamento Faltas + Atividades)</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Pesquise qualquer jovem, matrícula, disciplina ou turma para cruzar faltas e atividades pendentes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    termo_360 = st.text_input("🔍 Digite o Nome do Jovem, Matrícula, Código da Disciplina ou Turma:")
    if termo_360:
        c360_1, c360_2 = st.columns(2)
        with c360_1:
            st.markdown("### 🟧 Faltas Registadas")
            if not st.session_state["base_faltas"].empty:
                df_f = padronizar_base_faltas(st.session_state["base_faltas"])
                res_f = df_f[
                    df_f["Nome"].astype(str).str.contains(termo_360, case=False, na=False) |
                    df_f["Matricula"].astype(str).str.contains(termo_360, case=False, na=False) |
                    df_f["Disciplina"].astype(str).str.contains(termo_360, case=False, na=False) |
                    df_f["Turma"].astype(str).str.contains(termo_360, case=False, na=False)
                ]
                cols_360_f = ["Data_Falta", "Matricula", "Nome", "Cidade", "Estado", "Disciplina", "Turma", "Turno"]
                st.dataframe(res_f[[c for c in cols_360_f if c in res_f.columns]], use_container_width=True, hide_index=True)
        with c360_2:
            st.markdown("### 🟦 Atividades Pendentes (Moodle)")
            if not st.session_state["base_moodle"].empty:
                df_m = padronizar_base_moodle(st.session_state["base_moodle"])
                res_m = df_m[
                    df_m["Jovem"].astype(str).str.contains(termo_360, case=False, na=False) |
                    df_m["Disciplina"].astype(str).str.contains(termo_360, case=False, na=False) |
                    df_m["Turma"].astype(str).str.contains(termo_360, case=False, na=False)
                ]
                cols_360_m = ["Data_Coleta", "Disciplina", "Turno", "Turma", "Jovem", "Atividade"]
                st.dataframe(res_m[[c for c in cols_360_m if c in res_m.columns]], use_container_width=True, hide_index=True)
