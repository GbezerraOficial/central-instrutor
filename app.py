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
# ESTILIZAÇÃO VISUAL AVANÇADA (DESTAQUE NOS MENUS E SUBMENUS)
# ==============================================================================
st.markdown("""
<style>
    /* Botões Principais de Navegação */
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
    /* Abas Internas (Submenus em destaque) */
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
    /* Cartões de Métricas */
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
# 1. BANCO DE TURMAS DOS 8 INSTRUTORES (MANHÃ 'M' E TARDE 'V')
# ==============================================================================
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

MAPA_TURMA_INSTRUTOR = {}
for inst, turnos in BANCO_TURMAS.items():
    for cod in turnos["M"] + turnos["V"]:
        MAPA_TURMA_INSTRUTOR[cod.lstrip("0").upper()] = inst

def identificar_instrutor(cod_turma):
    limpo = str(cod_turma).strip().lstrip("0").upper()
    if limpo in MAPA_TURMA_INSTRUTOR:
        return MAPA_TURMA_INSTRUTOR[limpo]
    for k, v in MAPA_TURMA_INSTRUTOR.items():
        if k in limpo or limpo in k:
            return v
    return "Outro Instrutor / Geral"

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

def identificar_unidade(texto):
    t = str(texto).upper()
    if "UB" in t:
        return "UB - Bojador"
    if "UA" in t:
        return "UA - Áurea"
    if "UC" in t:
        return "UC - Cerrado"
    if "UM" in t:
        return "UM - Missões"
    return "Geral / Outra"

def extrair_data_nome_arquivo(nome_arq, data_fallback):
    m = re.search(r"(\d{2})[-._](\d{2})[-._](\d{4})", str(nome_arq))
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return data_fallback

# ==============================================================================
# 2. LEITOR UNIVERSAL NATIVO (SEM LXML / SEM SUBPROCESS)
# ==============================================================================
class ExtratorTabelaHTML(HTMLParser):
    """Lê ficheiros .xls que na verdade são tabelas HTML sem precisar de lxml."""
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
    """Lê ficheiros .xls guardados no formato XML Spreadsheet 2003."""
    try:
        root = ET.fromstring(texto_xml)
        linhas = []
        for elem in root.iter():
            if elem.tag.endswith("Row"):
                linha = []
                for cell in elem:
                    if cell.tag.endswith("Cell"):
                        val = "".join(cell.itertext()).strip()
                        linha.append(val)
                if any(c != "" for c in linha):
                    linhas.append(linha)
        if linhas:
            return pd.DataFrame(linhas)
    except Exception:
        pass
    return None

def converter_bytes_em_dataframe(bytes_arq, nome_arq):
    """Abre qualquer ficheiro .xls ou .xlsx (Binário, OpenXML, HTML, XML ou Texto/CSV)."""
    if not bytes_arq or len(bytes_arq) < 60 or nome_arq.startswith("~$"):
        return None, "vazio"

    # 1. Tenta motores Excel (xlrd e openpyxl) - lê todas as abas até achar dados
    for eng in ["xlrd", "openpyxl"]:
        try:
            xls = pd.ExcelFile(io.BytesIO(bytes_arq), engine=eng)
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, header=None)
                if df is not None and not df.dropna(how="all").empty:
                    return df, f"excel ({eng})"
        except Exception:
            pass

    # 2. Tenta descodificar como Texto / HTML / XML / CSV / TSV (UTF-8, UTF-16, Latin-1)
    for enc in ["utf-8-sig", "utf-16", "latin-1", "cp1252"]:
        try:
            texto = bytes_arq.decode(enc, errors="ignore").strip()
            if not texto:
                continue

            # Se for HTML disfarçado de .xls
            if "<table" in texto.lower() or "<tr" in texto.lower():
                parser = ExtratorTabelaHTML()
                parser.feed(texto)
                if parser.linhas:
                    return pd.DataFrame(parser.linhas), "html_xls"

            # Se for XML Excel 2003 disfarçado de .xls
            if "<workbook" in texto.lower() or "<row" in texto.lower():
                df_xml = ler_xml_excel_2003(texto)
                if df_xml is not None and not df_xml.empty:
                    return df_xml, "xml_xls"

            # Se for TSV / CSV disfarçado de .xls
            linhas_txt = [l for l in texto.splitlines() if l.strip()]
            if linhas_txt:
                for sep in ["\t", ";", ","]:
                    if sep in linhas_txt[0] or (len(linhas_txt) > 1 and sep in linhas_txt[1]):
                        lidas = list(csv.reader(linhas_txt, delimiter=sep))
                        lidas = [r for r in lidas if any(c.strip() for c in r)]
                        if lidas and max(len(r) for r in lidas) >= 2:
                            return pd.DataFrame(lidas), f"csv ({sep})"
        except Exception:
            pass

    return None, "sem_dados"

def extrair_alunos_do_dataframe(df_raw, nome_arq, data_padrao_str):
    """Extrai os jovens ausentes de qualquer estrutura de planilha."""
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df_clean = df_raw.dropna(how="all").dropna(axis=1, how="all")
    if df_clean.empty:
        return pd.DataFrame()

    nome_limpo = nome_arq.replace("\\", "/").split("/")[-1]
    data_falta = extrair_data_nome_arquivo(nome_limpo, data_padrao_str)
    modulo_padrao_arq = nome_limpo.split("-")[0].strip() if "-" in nome_limpo else nome_limpo

    registros = []

    for _, row in df_clean.iterrows():
        valores = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() not in ("", "nan", "None")]
        if len(valores) < 2:
            continue

        linha_upper = " ".join(valores).upper()
        # Ignora linhas que são apenas cabeçalho
        if linha_upper.startswith("ID ") or ("NOME" in linha_upper and "TURMA" in linha_upper and len(valores) <= 10 and "@" not in linha_upper):
            continue

        email = next((v for v in valores if "@" in v and "." in v), "")
        turma = next((v for v in valores if re.search(r"(APC|\d+\.[A-Z0-9]+\.\d+[MV])", v, re.I)), "")

        # Posicionamento inteligente caso a planilha tenha todas as células ou menos colunas
        id_jovem = ""
        nome_jovem = ""
        modulo_sigla = modulo_padrao_arq
        cidade_uf = ""
        encontro = ""

        if email and email in valores:
            idx_em = valores.index(email)
            if idx_em >= 1:
                nome_jovem = valores[idx_em - 1]
            if idx_em >= 2:
                id_jovem = valores[idx_em - 2]
            apos_email = [v for v in valores[idx_em + 1:] if v != turma]
            if len(apos_email) >= 1:
                modulo_sigla = apos_email[0]
            if len(apos_email) >= 2:
                cidade_uf = apos_email[1]
            if len(apos_email) >= 3:
                encontro = apos_email[2]
        else:
            # Fallback para planilhas que só têm ID e Nome (ou Nome e Turma) sem e-mail
            if valores[0].replace(".", "").isdigit() and len(valores) >= 2:
                id_jovem = valores[0]
                nome_jovem = valores[1]
                restantes = [v for v in valores[2:] if v != turma]
            else:
                nome_jovem = valores[0]
                restantes = [v for v in valores[1:] if v != turma]

            if len(restantes) >= 1:
                modulo_sigla = restantes[0]
            if len(restantes) >= 2:
                cidade_uf = restantes[1]
            if len(restantes) >= 3:
                encontro = restantes[2]

        if not turma:
            turma = modulo_sigla

        # Evita adicionar títulos soltos de 1 palavra
        if len(nome_jovem) < 3:
            continue

        registros.append({
            "Lancado_RM": False,
            "Data_Falta": data_falta,
            "Mes_Ano": data_falta[:7],
            "Instrutor": identificar_instrutor(turma),
            "Turno": identificar_turno(turma, nome_arq),
            "Unidade": identificar_unidade(modulo_sigla + " " + nome_limpo),
            "Turma": turma,
            "ID_Jovem": id_jovem,
            "Jovem": re.sub(r"\s+", " ", nome_jovem).strip(),
            "Email": email,
            "Encontro": encontro,
            "Modulo_Sigla": modulo_sigla,
            "Cidade_UF": cidade_uf,
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
            stats["detalhes"].append(f"⚪ {nome_curto}: Ficheiro vazio ({len(b_arq)} bytes)")

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
# 4. BARRA LATERAL: FILTROS GLOBAIS E BACKUP
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎯 FILTROS DE VISUALIZAÇÃO")
    opcoes_inst = ["🌟 Todos os Instrutores (Visão Geral)"] + list(BANCO_TURMAS.keys()) + ["Outro Instrutor / Geral"]
    filtro_global_inst = st.selectbox("👤 Filtrar por Instrutor(a):", opcoes_inst, index=0)
    filtro_global_turno = st.selectbox("🕒 Filtrar por Turno (M / V):", ["Todos (M + V)", "M - Manhã", "V - Tarde"])

    st.divider()
    st.markdown("### 🗄️ BACKUP HISTÓRICO (.XLSX)")
    arq_hist = st.file_uploader("📂 Restaurar Histórico Salvo:", type=["xlsx"])
    if arq_hist and st.button("🔄 Carregar Histórico", use_container_width=True):
        xls = pd.ExcelFile(arq_hist)
        if "Historico_Moodle" in xls.sheet_names:
            st.session_state["base_moodle"] = pd.read_excel(xls, "Historico_Moodle")
        if "Historico_Faltas" in xls.sheet_names:
            st.session_state["base_faltas"] = pd.read_excel(xls, "Historico_Faltas")
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
            Leitura imediata de pacotes <b>.ZIP</b> (pastas MAT e VES) e folhas de cálculo <b>.XLS / .XLSX</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR FOLHAS DE CÁLCULO OU PACOTE .ZIP DE FALTAS", expanded=True):
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
                with st.spinner("A analisar ficheiros e a extrair jovens ausentes..."):
                    df_novos, stats = processar_arquivos_enviados(arquivos_up, data_ref.strftime("%Y-%m-%d"))
                    st.session_state["ultimos_arquivos_lidos"] = assinatura_atual
                    st.session_state["ultimo_diagnostico"] = stats

                    if not df_novos.empty:
                        df_acum = pd.concat([st.session_state["base_faltas"], df_novos], ignore_index=True)
                        df_acum = df_acum.drop_duplicates(subset=["Data_Falta", "Turma", "ID_Jovem", "Jovem"], keep="first")
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

    df_f_total = st.session_state["base_faltas"].copy()

    if not df_f_total.empty:
        df_f = df_f_total.copy()
        if filtro_global_inst != "🌟 Todos os Instrutores (Visão Geral)":
            df_f = df_f[df_f["Instrutor"] == filtro_global_inst]
        if filtro_global_turno != "Todos (M + V)":
            df_f = df_f[df_f["Turno"] == filtro_global_turno]

        if df_f.empty and not df_f_total.empty:
            st.warning(
                f"⚠️ Foram lidas **{len(df_f_total)} faltas**, mas pertencem a outros instrutores/turnos. "
                f"Altere o filtro na barra lateral esquerda para **'🌟 Todos os Instrutores'**!"
            )
        else:
            sub_f1, sub_f2, sub_f3 = st.tabs([
                "📝 1. LANÇAR FALTAS NO RM (POR TURMA)",
                "🚨 2. RANKING SEMANAL / MENSAL DE FALTAS",
                "📊 3. GRÁFICOS POR UNIDADE E TURNO (M / V)"
            ])

            with sub_f1:
                f_c1, f_c2, f_c3, f_c4 = st.columns(4)
                with f_c1:
                    sel_dt = st.selectbox("📅 Filtrar Data:", ["Todas"] + sorted(df_f["Data_Falta"].unique().tolist(), reverse=True))
                with f_c2:
                    sel_unid = st.selectbox("🏢 Filtrar Unidade:", ["Todas"] + sorted(df_f["Unidade"].unique().tolist()))
                with f_c3:
                    df_sub = df_f.copy()
                    if sel_dt != "Todas":
                        df_sub = df_sub[df_sub["Data_Falta"] == sel_dt]
                    if sel_unid != "Todas":
                        df_sub = df_sub[df_sub["Unidade"] == sel_unid]
                    sel_turma = st.selectbox("🏫 Filtrar Turma:", ["Todas"] + sorted(df_sub["Turma"].unique().tolist()))
                with f_c4:
                    busca_f = st.text_input("🔍 Procurar Nome ou ID do Jovem:")

                if sel_turma != "Todas":
                    df_sub = df_sub[df_sub["Turma"] == sel_turma]
                if busca_f:
                    df_sub = df_sub[
                        df_sub["Jovem"].str.contains(busca_f, case=False, na=False) |
                        df_sub["ID_Jovem"].str.contains(busca_f, case=False, na=False)
                    ]

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ausências Filtradas", len(df_sub))
                m2.metric("☀️ Manhã (M)", len(df_sub[df_sub["Turno"] == "M - Manhã"]))
                m3.metric("🌤️ Tarde (V)", len(df_sub[df_sub["Turno"] == "V - Tarde"]))
                m4.metric("Turmas Afetadas", df_sub["Turma"].nunique())

                st.data_editor(
                    df_sub,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Lancado_RM": st.column_config.CheckboxColumn("✅ Lançado no RM?", default=False)
                    }
                )

            with sub_f2:
                rank_f = (
                    df_f.groupby(["ID_Jovem", "Jovem", "Email", "Turma", "Turno", "Instrutor", "Unidade"])
                    .agg(
                        Total_Faltas=("Data_Falta", "count"),
                        Datas_Ausente=("Data_Falta", lambda x: ", ".join(sorted(set(x)))),
                        Encontros=("Encontro", lambda x: " | ".join(sorted(set(str(v) for v in x if v))))
                    )
                    .reset_index()
                    .sort_values(by="Total_Faltas", ascending=False)
                )
                st.dataframe(rank_f, use_container_width=True, hide_index=True)

            with sub_f3:
                g1, g2 = st.columns(2)
                with g1:
                    st.markdown("**🏢 Faltas por Unidade:**")
                    st.bar_chart(df_f.groupby("Unidade")["Jovem"].count())
                with g2:
                    st.markdown("**🕒 Faltas por Turno (M vs V):**")
                    st.bar_chart(df_f.groupby("Turno")["Jovem"].count())

# ==============================================================================
# MÓDULO 2: ATIVIDADES MOODLE (DEMÀ DIGITAL)
# ==============================================================================
elif st.session_state["modulo_ativo"] == "MOODLE":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #0284c7 0%, #1d4ed8 100%); border-left: 8px solid #bae6fd;">
        <h2 style="margin:0;color:white;">🟦 MÓDULO: Acompanhamento de Atividades (Moodle Demà Digital)</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Consolidação das 7 atividades, controlo de e-mails enviados e comparativo semanal/mensal.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 ADICIONAR COLETA EXTRAÍDA PELA EXTENSÃO DO MOODLE", expanded=st.session_state["base_moodle"].empty):
        cm1, cm2 = st.columns(2)
        with cm1:
            dt_moodle = st.date_input("📅 Data da Coleta:", value=date.today(), format="DD/MM/YYYY")
        with cm2:
            enc_moodle = st.text_input("📘 Módulo / Encontro:", value="Encontro da Semana")

        txt_m = st.text_area("Cole (Ctrl+V) o relatório copiado pela Extensão do Moodle:", height=110)
        if st.button("➕ Guardar Coleta no Painel", type="primary"):
            if txt_m.strip():
                df_lote = pd.read_csv(io.StringIO(txt_m.strip()), sep="\t")
                dt_str = dt_moodle.strftime("%Y-%m-%d")
                if "Data_Coleta" not in df_lote.columns:
                    df_lote.insert(0, "Data_Coleta", dt_str)
                if "Mes_Ano" not in df_lote.columns:
                    df_lote.insert(1, "Mes_Ano", dt_str[:7])
                if "Encontro" not in df_lote.columns:
                    df_lote.insert(2, "Encontro", enc_moodle)
                st.session_state["base_moodle"] = pd.concat([st.session_state["base_moodle"], df_lote], ignore_index=True).drop_duplicates(
                    subset=["Data_Coleta", "Turma", "Atividade", "Jovem"], keep="last"
                )
                st.success("✅ Coleta registada!")
                st.rerun()

    df_m = st.session_state["base_moodle"].copy()
    if not df_m.empty:
        if filtro_global_inst != "🌟 Todos os Instrutores (Visão Geral)":
            df_m = df_m[df_m["Instrutor"] == filtro_global_inst]
        if filtro_global_turno != "Todos (M + V)":
            df_m = df_m[df_m["Turno"] == filtro_global_turno]

        sub_m1, sub_m2 = st.tabs([
            "📋 1. LISTA DE PENDÊNCIAS MOODLE",
            "📈 2. COMPARATIVO SEMANAL (QUEM REGULARIZOU)"
        ])
        with sub_m1:
            st.dataframe(df_m, use_container_width=True, hide_index=True)
        with sub_m2:
            datas_m = sorted(df_m["Data_Coleta"].astype(str).unique().tolist())
            if len(datas_m) < 2:
                st.info("Registe pelo menos 2 datas diferentes de coleta para comparar quem regularizou na semana.")
            else:
                d_ant = st.selectbox("Coleta Inicial:", datas_m, index=0)
                d_nov = st.selectbox("Coleta Recente:", datas_m, index=len(datas_m)-1)
                df_a = df_m[df_m["Data_Coleta"] == d_ant]
                df_n = df_m[df_m["Data_Coleta"] == d_nov]
                comp = pd.merge(df_a, df_n, on=["Turma", "Atividade", "Jovem"], how="outer", indicator=True)
                st.metric("✅ Regularizaram (Fizeram a atividade!)", len(comp[comp["_merge"] == "left_only"]))
                st.dataframe(comp[comp["_merge"] == "left_only"][["Turma", "Atividade", "Jovem"]], use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 3: VISÃO 360º (CRUZAMENTO FALTAS + MOODLE)
# ==============================================================================
elif st.session_state["modulo_ativo"] == "VISAO360":
    st.markdown("""
    <div class="banner-modulo" style="background: linear-gradient(90deg, #059669 0%, #047857 100%); border-left: 8px solid #a7f3d0;">
        <h2 style="margin:0;color:white;">🟩 MÓDULO: Visão 360º do Jovem (Cruzamento Faltas + Atividades)</h2>
        <p style="margin:4px 0 0 0;opacity:0.95;font-size:14px;">
            Pesquise qualquer jovem ou turma para ver em simultâneo as suas faltas e atividades pendentes no Moodle.
        </p>
    </div>
    """, unsafe_allow_html=True)

    termo_360 = st.text_input("🔍 Digite o Nome do Jovem ou o Código da Turma:")
    if termo_360:
        c360_1, c360_2 = st.columns(2)
        with c360_1:
            st.markdown("### 🟧 Faltas Registadas")
            df_f = st.session_state["base_faltas"]
            if not df_f.empty:
                res_f = df_f[df_f["Jovem"].str.contains(termo_360, case=False, na=False) | df_f["Turma"].str.contains(termo_360, case=False, na=False)]
                st.dataframe(res_f[["Data_Falta", "Turno", "Turma", "Jovem", "Encontro"]], use_container_width=True, hide_index=True)
        with c360_2:
            st.markdown("### 🟦 Atividades Pendentes (Moodle)")
            df_m = st.session_state["base_moodle"]
            if not df_m.empty:
                res_m = df_m[df_m["Jovem"].str.contains(termo_360, case=False, na=False) | df_m["Turma"].str.contains(termo_360, case=False, na=False)]
                st.dataframe(res_m[["Data_Coleta", "Turno", "Turma", "Jovem", "Atividade"]], use_container_width=True, hide_index=True)
