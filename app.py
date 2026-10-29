import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import csv
import time
import zipfile
import hmac
import hashlib
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from datetime import datetime, date

st.set_page_config(
    page_title="Central Demà & RM - Equipe Bojador",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. LOGIN COM DIFERENCIAÇÃO AUTOMÁTICA: UTILIZADOR FINAL vs ADMINISTRADOR
# ==============================================================================
def autenticar():
    if st.session_state.get("logado", False):
        return True

    if "tentativas_login" not in st.session_state:
        st.session_state["tentativas_login"] = 0
    if "bloqueado_ate" not in st.session_state:
        st.session_state["bloqueado_ate"] = 0.0

    agora = time.time()
    if agora < st.session_state["bloqueado_ate"]:
        restante = int(st.session_state["bloqueado_ate"] - agora)
        st.error(f"⏳ Muitas tentativas incorretas. Aguarde {restante} segundos.")
        st.stop()

    senha_usuario = str(st.secrets.get("SENHA_PAINEL", "1234"))
    senha_admin = str(st.secrets.get("SENHA_ADMIN", "admin2026"))

    st.markdown("""
    <div style="background-color:var(--secondary-background-color);border:1.5px solid rgba(37,99,235,0.45);border-left:8px solid #2563eb;padding:16px 22px;border-radius:12px;margin-bottom:16px;">
        <h2 style="margin:0;color:var(--text-color);">⚡ Central Demà & RM — Equipe Bojador</h2>
        <p style="margin:4px 0 0 0;color:var(--text-color);opacity:0.85;font-size:14px;">
            Insira a sua credencial de acesso (Utilizador ou Administrador).
        </p>
    </div>
    """, unsafe_allow_html=True)

    senha_dig = st.text_input("Senha de acesso:", type="password")
    if senha_dig:
        dig_bytes = senha_dig.encode("utf-8")
        if hmac.compare_digest(dig_bytes, senha_admin.encode("utf-8")):
            st.session_state["logado"] = True
            st.session_state["is_admin"] = True
            st.session_state["tentativas_login"] = 0
            st.rerun()
        elif hmac.compare_digest(dig_bytes, senha_usuario.encode("utf-8")):
            st.session_state["logado"] = True
            st.session_state["is_admin"] = False
            st.session_state["tentativas_login"] = 0
            st.rerun()
        else:
            st.session_state["tentativas_login"] += 1
            if st.session_state["tentativas_login"] >= 5:
                st.session_state["bloqueado_ate"] = time.time() + 30
                st.error("🚫 5 tentativas falhadas. Acesso bloqueado por 30 segundos.")
            else:
                st.error(f"❌ Senha incorreta ({st.session_state['tentativas_login']}/5).")
    return False

# Bloqueia os ícones de topo na tela de login por padrão
if not st.session_state.get("logado", False):
    st.markdown("""
    <style>
        [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
        .stAppDeployButton, header[data-testid="stHeader"] a,
        [data-testid="manage-app-button"], footer { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

if not autenticar():
    st.stop()

# ==============================================================================
# 2. DESIGN 100% ADAPTATIVO (CLARO/ESCURO) + OCULTAÇÃO DE ÍCONES PARA NÃO-ADMINS
# ==============================================================================
css_ocultar_icones_usuario = ""
if not st.session_state.get("is_admin", False):
    # Oculta Share, Estrela, Lápis, GitHub e Manage App, mantendo APENAS os 3 pontinhos (⋮ -> Theme)
    css_ocultar_icones_usuario = """
    [data-testid="stToolbarActions"],
    [data-testid="stToolbarActionButton"],
    [data-testid="stAppDeployButton"],
    .stAppDeployButton,
    header[data-testid="stHeader"] a,
    [data-testid="manage-app-button"],
    div[class*="viewerBadge"],
    footer {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    """

st.markdown(f"""
<style>
    {css_ocultar_icones_usuario}

    section[data-testid="stSidebar"] {{
        border-right: 2px solid #2563eb !important;
    }}
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    label {{
        color: var(--text-color) !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }}
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="textarea"],
    [data-baseweb="select"] > div {{
        border: 1.5px solid rgba(128, 128, 128, 0.4) !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
    }}
    [data-baseweb="input"]:focus-within,
    [data-baseweb="textarea"]:focus-within,
    [data-baseweb="select"] > div:focus-within {{
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25) !important;
    }}
    div[data-testid="stExpander"] {{
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
        border-left: 5px solid #2563eb !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }}
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {{
        color: var(--text-color) !important;
        font-weight: 800 !important;
        font-size: 14px !important;
    }}
    [data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed #2563eb !important;
        border-radius: 10px !important;
    }}
    div.stButton > button {{
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        padding: 10px 14px !important;
        transition: all 0.15s ease !important;
        border: 1.5px solid rgba(128, 128, 128, 0.35) !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-1px);
        border-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #001ae6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(0, 26, 230, 0.3) !important;
    }}
    div.stButton > button[kind="primary"] p,
    div.stButton > button[kind="primary"] span {{
        color: #ffffff !important;
    }}
    div.stDownloadButton > button {{
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }}
    div.stDownloadButton > button p,
    div.stDownloadButton > button span {{
        color: #ffffff !important;
    }}
    div[data-baseweb="tab-list"] {{
        gap: 8px !important;
        background-color: transparent !important;
        padding-bottom: 6px !important;
    }}
    button[data-baseweb="tab"] {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-radius: 8px !important;
        padding: 11px 18px !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        border: 1.5px solid rgba(128, 128, 128, 0.3) !important;
        flex: 1 !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }}
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {{
        color: var(--text-color) !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }}
    button[data-baseweb="tab"]:hover {{
        border-color: #3b82f6 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg, #001ae6 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: 1.5px solid #3b82f6 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {{
        color: #ffffff !important;
    }}
    div[data-testid="stMetric"] {{
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-left: 5px solid #2563eb !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] div {{
        color: var(--text-color) !important;
        opacity: 0.85;
        font-weight: 700 !important;
    }}
    div[data-testid="stMetricValue"] div {{
        color: var(--text-color) !important;
        font-weight: 800 !important;
    }}
    .banner-dema {{
        background-color: var(--secondary-background-color);
        border: 1.5px solid rgba(37, 99, 235, 0.45);
        border-left: 8px solid #2563eb;
        padding: 14px 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        font-family: Arial, sans-serif;
    }}
    .banner-dema h2 {{
        margin: 0;
        color: var(--text-color) !important;
        font-size: 22px;
        font-weight: 800;
    }}
    .banner-dema p {{
        margin: 4px 0 0 0;
        color: var(--text-color) !important;
        opacity: 0.88;
        font-size: 13.5px;
    }}
    .titulo-secao {{
        color: var(--text-color) !important;
        font-weight: 800 !important;
        margin-top: 4px !important;
        margin-bottom: 8px !important;
    }}
    .visor-sucesso {{
        background-color: rgba(46, 125, 50, 0.15);
        border: 1px solid #2e7d32;
        border-left: 5px solid #2e7d32;
        color: var(--text-color) !important;
        padding: 10px 14px;
        border-radius: 8px;
        font-weight: 700;
        margin-bottom: 12px;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. BANCO DE TURMAS (OUTUBRO 2026) E FUNÇÕES DE RESET DE FILTROS
# ==============================================================================
UFS_BRASIL = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
}

LIMITE_BYTES_ARQUIVO = 50 * 1024 * 1024
REGEX_DATA_ARQ = re.compile(r"(\d{2})[-._](\d{2})[-._](\d{4})")
REGEX_DISC_ARQ = re.compile(r"\s*-\s*\d{2}[-._]\d{2}[-._]\d{4}")
REGEX_EXT_ARQ = re.compile(r"\.(xlsx?|csv|tsv)$", re.I)
REGEX_TURMA_APC = re.compile(r"(APC\.?\d+|\d+\.[A-Z0-9]+\.\d+[MV])", re.I)
REGEX_MATRICULA = re.compile(r"^\d{3,12}$")

TURMAS_DESATIVADAS_PADRAO = {
    "3872.APC01.4V.101", "3872.APC01.4V.89", "3872.APC01.4V.92", "671.APC01.4V.101",
    "671.APC02.2V.100", "671.APC02.4M.54", "671.APC02.4V.54", "671.APC02.4V.78"
}

BANCO_TURMAS_PADRAO = {
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

# Callbacks de Limpeza Instantânea de Filtros (Executam antes de renderizar os widgets)
def limpar_filtros_faltas():
    st.session_state["f_inst"] = "🌟 Todos os Instrutores"
    st.session_state["f_disc"] = "Todas as Disciplinas"
    st.session_state["f_modo"] = "📅 Dia"
    st.session_state["f_dia"] = "Todos os Dias"
    st.session_state["f_sem"] = "Todas as Semanas"
    st.session_state["f_mes"] = "Todos os Meses"
    st.session_state["f_turno"] = "Todos (M + V)"
    st.session_state["f_busca"] = ""

def limpar_filtros_moodle():
    st.session_state["m_inst"] = "🌟 Todos os Instrutores"
    st.session_state["m_disc"] = "Todas as Disciplinas"
    st.session_state["m_modo"] = "📅 Dia"
    st.session_state["m_dia"] = "Todos os Dias"
    st.session_state["m_sem"] = "Todas as Semanas"
    st.session_state["m_mes"] = "Todos os Meses"
    st.session_state["m_turno"] = "Todos (M + V)"
    st.session_state["m_busca"] = ""

def limpar_filtros_rm():
    st.session_state["r_inst"] = "🌟 Todos os Instrutores"
    if not st.session_state.get("base_rm", pd.DataFrame()).empty:
        status_disp = sorted(st.session_state["base_rm"]["STATUS_PROVA"].unique().tolist())
        st.session_state["r_st_prova"] = [s for s in status_disp if s.upper() != "FINALIZADO"] or status_disp
    st.session_state["r_st_per"] = "Todos"
    st.session_state["r_ciclo"] = "Todos os Períodos"
    st.session_state["r_busca"] = ""

def limpar_filtros_360():
    st.session_state["busca_360_input"] = ""

def limpar_todos_os_filtros_global():
    limpar_filtros_faltas()
    limpar_filtros_moodle()
    limpar_filtros_rm()
    limpar_filtros_360()

def normalizar_codigo_turma(s):
    txt = str(s or "").upper().strip()
    txt = re.sub(r"^0+(\d)", r"\1", txt)
    txt = re.sub(r"^4\.0\.APC", "4.APC", txt)
    txt = re.sub(r"\.APC\.(\d)", r".APC\1", txt)
    txt = re.sub(r"\.0+(\d+)$", r".\1", txt)
    return txt

if "banco_turmas_atual" not in st.session_state:
    st.session_state["banco_turmas_atual"] = BANCO_TURMAS_PADRAO
if "turmas_desativadas" not in st.session_state:
    st.session_state["turmas_desativadas"] = {normalizar_codigo_turma(c) for c in TURMAS_DESATIVADAS_PADRAO}

def construir_mapas_turmas():
    banco = st.session_state["banco_turmas_atual"]
    mapa_str = {}
    set_por_inst = {}
    for inst, turnos in banco.items():
        set_por_inst[inst] = set()
        for cod in turnos["M"] + turnos["V"]:
            cod_norm = normalizar_codigo_turma(cod)
            set_por_inst[inst].add(cod_norm)
            if cod_norm not in mapa_str:
                mapa_str[cod_norm] = inst
            elif inst not in mapa_str[cod_norm]:
                mapa_str[cod_norm] += f" / {inst}"
    return mapa_str, set_por_inst

if "mapas_cache" not in st.session_state:
    st.session_state["mapas_cache"] = construir_mapas_turmas()

MAPA_TURMA_STR, SET_TURMAS_POR_INSTRUTOR = st.session_state["mapas_cache"]

@st.cache_data(show_spinner=False, max_entries=15)
def converter_df_para_excel_bytes(df_exportar, nome_aba="Dados"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_exportar.to_excel(writer, sheet_name=nome_aba, index=False)
    return buf.getvalue()

@st.cache_data(show_spinner=False, max_entries=5)
def gerar_backup_unificado_bytes(df_f, df_m, df_r):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if not df_f.empty:
            cols_f = [c for c in df_f.columns if not c.startswith("_")]
            df_f[cols_f].to_excel(writer, sheet_name="Historico_Faltas", index=False)
        if not df_m.empty:
            cols_m = [c for c in df_m.columns if not c.startswith("_")]
            df_m[cols_m].to_excel(writer, sheet_name="Historico_Moodle", index=False)
        if not df_r.empty:
            cols_r = [c for c in df_r.columns if not c.startswith("_")]
            df_r[cols_r].to_excel(writer, sheet_name="Historico_RM", index=False)
    return buf.getvalue()

def atualizar_banco_via_planilha_grade(arq_excel):
    xls = pd.ExcelFile(arq_excel)
    abas_turmas = [s for s in xls.sheet_names if s.startswith("Turmas_")]
    if not abas_turmas:
        return False, "Nenhuma aba iniciada por 'Turmas_' foi encontrada na planilha."

    novo_banco = {k: {"M": [], "V": []} for k in BANCO_TURMAS_PADRAO.keys()}
    novas_desativadas = set()
    total_lidas = 0

    for aba in abas_turmas:
        df = pd.read_excel(xls, sheet_name=aba)
        if df.empty:
            continue
        header_idx = None
        for r_idx in range(len(df)):
            vals = [str(x).strip().upper() for x in df.iloc[r_idx].values]
            if "CODTURMA" in vals:
                header_idx = r_idx
                break
        if header_idx is None:
            continue

        df_data = df.iloc[header_idx + 1:].copy()
        for _, row in df_data.iterrows():
            cod = str(row.iloc[1]).strip() if len(row) > 1 else ""
            if not cod or cod.lower() in ("nan", "none"):
                continue
            turno_raw = str(row.iloc[2]).strip().upper() if len(row) > 2 else ""
            if aba == "Turmas_Profissa 4.0":
                tutor = "Guilherme Gomes Bezerra"
                obs = ""
            else:
                tutor = str(row.iloc[4]).strip() if len(row) > 4 else ""
                obs = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else ""

            tutor_chave = None
            for nome_padrao in novo_banco.keys():
                if nome_padrao.split()[0].upper() in tutor.upper():
                    tutor_chave = nome_padrao
                    break
            if not tutor_chave:
                continue

            sigla_t = "M" if ("MATUTINO" in turno_raw or "M." in cod.upper()) else "V"
            if cod not in novo_banco[tutor_chave][sigla_t]:
                novo_banco[tutor_chave][sigla_t].append(cod)
                total_lidas += 1

            if "desativada" in obs.lower():
                novas_desativadas.add(normalizar_codigo_turma(cod))

    st.session_state["banco_turmas_atual"] = novo_banco
    st.session_state["turmas_desativadas"] = novas_desativadas
    st.session_state["mapas_cache"] = construir_mapas_turmas()
    return True, f"{total_lidas} turmas carregadas ({len(novas_desativadas)} marcadas para desativação)."

def sanitizar_celula(valor):
    s = str(valor).strip()
    if s and s[0] in ("=", "+", "-", "@") and "@" not in s[1:]:
        return "'" + s
    return s

def separar_cidade_estado(texto_cid_uf):
    txt = str(texto_cid_uf).strip()
    if not txt or txt.lower() in ("nan", "none"):
        return "", ""
    for sep in ("/", " - ", "-"):
        if sep in txt:
            partes = txt.rsplit(sep, 1)
            uf_cand = partes[1].strip().upper()
            if len(uf_cand) == 2 and uf_cand in UFS_BRASIL:
                return partes[0].strip(), uf_cand
    return txt, ""

def eh_cidade_uf(val):
    _, uf = separar_cidade_estado(val)
    return uf != ""

def calcular_semana_vetorizado(serie_datas):
    datas_dt = pd.to_datetime(serie_datas, errors="coerce")
    iso = datas_dt.dt.isocalendar()
    return (iso["year"].astype(str) + "-Semana " + iso["week"].apply(lambda w: f"{int(w):02d}" if pd.notna(w) else "00")).fillna("Semana Atual")

def ler_texto_rm_blindado(texto_bruto):
    linhas = [l for l in texto_bruto.splitlines() if l.strip()]
    if len(linhas) <= 1:
        return pd.DataFrame()

    sep = "\t" if "\t" in linhas[0] else (";" if ";" in linhas[0] else ",")
    lidas = [r for r in csv.reader(linhas, delimiter=sep) if any(c.strip() for c in r)]
    if len(lidas) <= 1:
        return pd.DataFrame()

    max_cols = max(len(r) for r in lidas)
    cabecalho = [c.strip() for c in lidas[0]]
    if len(cabecalho) < max_cols:
        for i in range(len(cabecalho), max_cols):
            cabecalho.append(f"COL_EXTRA_{i+1}")

    cab_unico = []
    vistos = {}
    for c in cabecalho:
        nome_c = c if c else "COL"
        if nome_c in vistos:
            vistos[nome_c] += 1
            cab_unico.append(f"{nome_c}_{vistos[nome_c]}")
        else:
            vistos[nome_c] = 1
            cab_unico.append(nome_c)

    dados = []
    for r in lidas[1:]:
        if any("STATUS_PROVA" in str(x).upper() for x in r[:3]):
            continue
        if len(r) < max_cols:
            r = r + [""] * (max_cols - len(r))
        else:
            r = r[:max_cols]
        dados.append(r)

    if not dados:
        return pd.DataFrame()

    return pd.DataFrame(dados, columns=cab_unico)

def indexar_base_faltas(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.loc[:, ~df.columns.duplicated()].copy().reset_index(drop=True)
    if "Lancado_RM" not in df.columns:
        df.insert(0, "Lancado_RM", False)
    df["Lancado_RM"] = df["Lancado_RM"].fillna(False).astype(bool)

    if "Nome" not in df.columns and "Jovem" in df.columns:
        df["Nome"] = df["Jovem"]
    if "Matricula" not in df.columns and "ID_Jovem" in df.columns:
        df["Matricula"] = df["ID_Jovem"]

    df["Matricula"] = df["Matricula"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    df["Nome"] = df["Nome"].fillna("").astype(str).apply(sanitizar_celula)
    df["Turma"] = df["Turma"].fillna("").astype(str).str.strip()

    if "Cidade" not in df.columns:
        if "Cidade_UF" in df.columns:
            pares = [separar_cidade_estado(x) for x in df["Cidade_UF"]]
            df["Cidade"] = [p[0] for p in pares]
            df["Estado"] = [p[1] for p in pares]
        else:
            df["Cidade"] = ""
            df["Estado"] = ""

    df["_turma_norm"] = df["Turma"].apply(normalizar_codigo_turma)
    df["_cod_apc"] = df["_turma_norm"].str.extract(r"(APC\.?\d+)", expand=False).str.replace(".", "", regex=False).fillna("")

    if "Disciplina" not in df.columns:
        if "Modulo_Sigla" in df.columns:
            df["Disciplina"] = df["Modulo_Sigla"].fillna("").astype(str)
        else:
            df["Disciplina"] = df["_cod_apc"]
    df["Disciplina"] = df["Disciplina"].replace({"": "GERAL", "nan": "GERAL"}).fillna("GERAL").astype(str)

    if "Data_Falta" not in df.columns:
        df["Data_Falta"] = date.today().strftime("%Y-%m-%d")
    df["Data_Falta"] = df["Data_Falta"].astype(str).str.slice(0, 10)
    df["Mes_Ano"] = df["Data_Falta"].str.slice(0, 7)
    df["Semana_Ano"] = calcular_semana_vetorizado(df["Data_Falta"])

    df["Instrutor"] = df["_turma_norm"].map(MAPA_TURMA_STR).fillna("Não Mapeado / Outros")
    arq_orig = df["Arquivo_Origem"].astype(str).str.upper() if "Arquivo_Origem" in df.columns else pd.Series("", index=df.index)
    cond_m = df["_turma_norm"].str.contains("M.", regex=False) | arq_orig.str.contains("MAT|_M\\.", regex=True)
    cond_v = df["_turma_norm"].str.contains("V.", regex=False) | arq_orig.str.contains("VES|_V\\.", regex=True)
    df["Turno"] = np.select([cond_m, cond_v], ["M - Manhã", "V - Tarde"], default="Outro")

    df["_busca_idx"] = (
        df["Matricula"] + " " + df["Nome"] + " " + df["Cidade"].astype(str) + " " +
        df["Estado"].astype(str) + " " + df["Disciplina"] + " " + df["Turma"]
    ).str.upper()

    return df

def indexar_base_moodle(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.loc[:, ~df.columns.duplicated()].copy().reset_index(drop=True)
    if "Data_Coleta" not in df.columns:
        df.insert(0, "Data_Coleta", date.today().strftime("%Y-%m-%d"))
    df["Data_Coleta"] = df["Data_Coleta"].astype(str).str.slice(0, 10)
    df["Mes_Ano"] = df["Data_Coleta"].str.slice(0, 7)
    df["Semana_Ano"] = calcular_semana_vetorizado(df["Data_Coleta"])

    if "Jovem" not in df.columns and "Nome" in df.columns:
        df["Jovem"] = df["Nome"]
    df["Jovem"] = df["Jovem"].fillna("").astype(str).apply(sanitizar_celula)
    df["Turma"] = df["Turma"].fillna("GERAL").astype(str).str.strip()
    df["Atividade"] = df["Atividade"].fillna("").astype(str).str.strip() if "Atividade" in df.columns else ""

    df["_turma_norm"] = df["Turma"].apply(normalizar_codigo_turma)
    df["_cod_apc"] = df["_turma_norm"].str.extract(r"(APC\.?\d+)", expand=False).str.replace(".", "", regex=False).fillna("")
    df["Instrutor"] = df["_turma_norm"].map(MAPA_TURMA_STR).fillna("Não Mapeado / Outros")

    cond_m = df["_turma_norm"].str.contains("M.", regex=False)
    cond_v = df["_turma_norm"].str.contains("V.", regex=False)
    df["Turno"] = np.select([cond_m, cond_v], ["M - Manhã", "V - Tarde"], default="Outro")

    if "Disciplina" not in df.columns:
        df["Disciplina"] = np.where(df["_cod_apc"] != "", df["_cod_apc"], "GERAL")
    df["Disciplina"] = df["Disciplina"].replace({"": "GERAL", "nan": "GERAL"}).fillna("GERAL").astype(str)

    df["_busca_idx"] = (
        df["Jovem"] + " " + df["Disciplina"] + " " + df["Turma"] + " " + df["Atividade"]
    ).str.upper()

    return df

def indexar_base_rm(df, df_faltas=None, df_moodle=None):
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.loc[:, ~df.columns.duplicated()].copy().reset_index(drop=True)

    mapa_exato = {
        "STATUS_PROVA": "STATUS_PROVA",
        "STATUS_PERIODO": "STATUS_PERIODO",
        "CODPESSOA": "CODPESSOA",
        "CODPROVA": "CODPROVA",
        "CODPERIODO": "CODPERIODO",
        "NOMEPROVA": "NOMEPROVA",
        "NOMEPERIODO": "NOMEPERIODO",
        "DATAINICIAL": "DATAINICIAL",
        "DATAFINAL": "DATAFINAL",
        "CODIGO_ACESSO": "CODIGO_ACESSO",
        "NOME": "NOME",
        "CIDADE": "CIDADE",
        "CODTURMA": "Turma",
        "TURMA": "Turma",
        "NOMEPROFESSOR": "Instrutor_RM",
        "INSTRUTOR": "Instrutor",
        "INSTRUTOR_FILTRO": "Instrutor_Filtro"
    }

    alvos_usados = set()
    col_map = {}

    for c in df.columns:
        cu = str(c).strip().upper()
        if cu in mapa_exato:
            dest = mapa_exato[cu]
            if dest not in alvos_usados:
                col_map[c] = dest
                alvos_usados.add(dest)

    for c in df.columns:
        if c in col_map:
            continue
        cu = str(c).strip().upper()
        dest = None
        if "STATUS_PROVA" in cu: dest = "STATUS_PROVA"
        elif "STATUS_PERIODO" in cu: dest = "STATUS_PERIODO"
        elif "CODPESSOA" in cu: dest = "CODPESSOA"
        elif "NOMEPROVA" in cu: dest = "NOMEPROVA"
        elif "NOMEPERIODO" in cu: dest = "NOMEPERIODO"
        elif "DATAINICIAL" in cu: dest = "DATAINICIAL"
        elif "DATAFINAL" in cu: dest = "DATAFINAL"
        elif "ACESSO" in cu: dest = "CODIGO_ACESSO"
        elif "CIDADE" in cu: dest = "CIDADE"
        elif "TURMA" in cu: dest = "Turma"
        elif "PROFESSOR" in cu: dest = "Instrutor_RM"
        elif "INSTRUTOR" in cu: dest = "Instrutor_Filtro"

        if dest and dest not in alvos_usados:
            col_map[c] = dest
            alvos_usados.add(dest)

    df = df.rename(columns=col_map)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    if "Turma" not in df.columns:
        for c in df.columns:
            amostra = df[c].dropna().astype(str).head(25)
            if amostra.str.contains(r"APC\d+", case=False, regex=True).any():
                df["Turma"] = df[c].astype(str).str.strip()
                break

    colunas_padrao = [
        "STATUS_PROVA", "STATUS_PERIODO", "CODPESSOA", "CODPROVA", "CODPERIODO",
        "NOMEPROVA", "NOMEPERIODO", "DATAINICIAL", "DATAFINAL", "CODIGO_ACESSO", "NOME", "CIDADE"
    ]
    for col_obr in colunas_padrao:
        if col_obr not in df.columns:
            df[col_obr] = ""
        serie_col = df[col_obr]
        if isinstance(serie_col, pd.DataFrame):
            serie_col = serie_col.iloc[:, 0]
        df[col_obr] = serie_col.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()

    df["NOME"] = df["NOME"].apply(sanitizar_celula)
    df["_nome_upper"] = df["NOME"].str.upper()

    mapa_nome_turma = {}
    mapa_nome_mat = {}
    if df_moodle is not None and not df_moodle.empty and "Jovem" in df_moodle.columns and "Turma" in df_moodle.columns:
        for n_j, t_j in zip(df_moodle["Jovem"].astype(str).str.upper(), df_moodle["Turma"].astype(str)):
            if n_j and t_j:
                mapa_nome_turma[n_j] = t_j
    if df_faltas is not None and not df_faltas.empty and "Nome" in df_faltas.columns and "Turma" in df_faltas.columns:
        for n_j, t_j, m_j in zip(df_faltas["Nome"].astype(str).str.upper(), df_faltas["Turma"].astype(str), df_faltas["Matricula"].astype(str)):
            if n_j and t_j:
                mapa_nome_turma[n_j] = t_j
            if n_j and m_j:
                mapa_nome_mat[n_j] = m_j

    turma_cruzada = df["_nome_upper"].map(mapa_nome_turma).fillna("Não Identificada")
    if "Turma" not in df.columns:
        df["Turma"] = turma_cruzada
    else:
        serie_turma = df["Turma"].iloc[:, 0] if isinstance(df["Turma"], pd.DataFrame) else df["Turma"]
        serie_turma = serie_turma.fillna("").astype(str).str.strip()
        mask_vazia = serie_turma.isin(["", "nan", "None", "Não Identificada"])
        df["Turma"] = np.where(mask_vazia, turma_cruzada, serie_turma)

    df["Matricula"] = df["_nome_upper"].map(mapa_nome_mat).fillna(df["CODPESSOA"])
    df["_turma_norm"] = pd.Series(df["Turma"], index=df.index).apply(normalizar_codigo_turma)

    inst_base = pd.Series("", index=df.index)
    if "Instrutor_RM" in df.columns:
        s_rm = df["Instrutor_RM"].iloc[:, 0] if isinstance(df["Instrutor_RM"], pd.DataFrame) else df["Instrutor_RM"]
        inst_base = s_rm.fillna("").astype(str).str.strip()
    elif "Instrutor" in df.columns:
        s_in = df["Instrutor"].iloc[:, 0] if isinstance(df["Instrutor"], pd.DataFrame) else df["Instrutor"]
        inst_base = s_in.fillna("").astype(str).str.strip()

    inst_turma = df["_turma_norm"].map(MAPA_TURMA_STR).fillna("")
    if "Instrutor_Filtro" in df.columns:
        s_flt = df["Instrutor_Filtro"].iloc[:, 0] if isinstance(df["Instrutor_Filtro"], pd.DataFrame) else df["Instrutor_Filtro"]
        inst_filtro = s_flt.fillna("").astype(str).str.strip()
    else:
        inst_filtro = pd.Series("Guilherme Gomes Bezerra", index=df.index)

    df["Instrutor"] = np.where(inst_base != "", inst_base, np.where(inst_turma != "", inst_turma, inst_filtro))
    df["Instrutor"] = pd.Series(df["Instrutor"], index=df.index).replace("", "Guilherme Gomes Bezerra")

    cond_m = df["_turma_norm"].str.contains("M.", regex=False)
    cond_v = df["_turma_norm"].str.contains("V.", regex=False)
    df["Turno"] = np.select([cond_m, cond_v], ["M - Manhã", "V - Tarde"], default="Geral")

    df["_busca_idx"] = (
        df["CODPESSOA"] + " " + df["Matricula"] + " " + df["NOME"] + " " +
        df["CODIGO_ACESSO"] + " " + df["CIDADE"] + " " + df["Turma"] + " " + df["NOMEPERIODO"]
    ).str.upper()

    return df

def filtrar_rapido_por_instrutor(df_alvo, nome_instrutor):
    if st.session_state.get("ocultar_desativadas", False) and "_turma_norm" in df_alvo.columns:
        df_alvo = df_alvo[~df_alvo["_turma_norm"].isin(st.session_state["turmas_desativadas"])]
    if nome_instrutor == "🌟 Todos os Instrutores":
        return df_alvo
    if nome_instrutor == "Não Mapeado / Outros":
        return df_alvo[df_alvo["Instrutor"] == "Não Mapeado / Outros"]
    codigos_inst = SET_TURMAS_POR_INSTRUTOR.get(nome_instrutor, set())
    mask_turma = df_alvo["_turma_norm"].isin(codigos_inst) if "_turma_norm" in df_alvo.columns else False
    mask_inst = df_alvo["Instrutor"].astype(str).str.contains(nome_instrutor, case=False, na=False)
    return df_alvo[mask_turma | mask_inst]

# ==============================================================================
# 4. LEITOR UNIVERSAL PARALELO E CACHEADO (@st.cache_data)
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
    if not bytes_arq or len(bytes_arq) <= 850 or len(bytes_arq) > LIMITE_BYTES_ARQUIVO or nome_arq.startswith("~$"):
        return None, "vazio_810b"

    ext = nome_arq.lower().split(".")[-1]
    motores = ["xlrd", "openpyxl"] if ext == "xls" else ["openpyxl", "xlrd"]

    for eng in motores:
        try:
            df = pd.read_excel(io.BytesIO(bytes_arq), header=None, engine=eng)
            if df is not None and not df.dropna(how="all").empty:
                return df, f"excel ({eng})"
        except Exception:
            pass

    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            texto = bytes_arq.decode(enc, errors="ignore").strip()
            if not texto:
                continue
            t_low = texto[:400].lower()
            if "<table" in t_low or "<tr" in t_low:
                parser = ExtratorTabelaHTML()
                parser.feed(texto)
                if parser.linhas:
                    return pd.DataFrame(parser.linhas), "html_xls"
            if "<workbook" in t_low or "<row" in t_low:
                df_xml = ler_xml_excel_2003(texto)
                if df_xml is not None and not df_xml.empty:
                    return df_xml, "xml_xls"
            linhas_txt = [l for l in texto.splitlines() if l.strip()]
            if linhas_txt:
                for sep in ("\t", ";", ","):
                    if sep in linhas_txt[0]:
                        lidas = [r for r in csv.reader(linhas_txt, delimiter=sep) if any(c.strip() for c in r)]
                        if lidas and max(len(r) for r in lidas) >= 2:
                            return pd.DataFrame(lidas), f"csv ({sep})"
        except Exception:
            pass

    return None, "sem_dados"

def extrair_alunos_do_dataframe(df_raw, nome_arq, data_padrao_str):
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df_clean = df_raw.dropna(how="all")
    if df_clean.empty:
        return pd.DataFrame()

    nome_limpo = nome_arq.replace("\\", "/").split("/")[-1]
    m_dt = REGEX_DATA_ARQ.search(nome_limpo)
    data_falta = f"{m_dt.group(3)}-{m_dt.group(2)}-{m_dt.group(1)}" if m_dt else data_padrao_str

    disc_arquivo = REGEX_DISC_ARQ.split(nome_limpo)[0]
    disc_arquivo = REGEX_EXT_ARQ.sub("", disc_arquivo).strip()

    if df_clean.shape[1] >= 10:
        col_j = df_clean.iloc[:, 9].dropna().astype(str)
        if not col_j.empty and col_j.str.contains("APC", case=False, na=False).any():
            sub = df_clean[[0, 1, 3, 5, 9]].copy()
            sub.columns = ["Matricula", "Nome", "Disciplina", "Cidade_UF", "Turma"]
            sub = sub.dropna(subset=["Nome", "Turma"], how="any")
            sub = sub[~sub["Turma"].astype(str).str.upper().isin(["TURMA", "CODTURMA", "NAN", ""])]
            if not sub.empty:
                pares = [separar_cidade_estado(x) for x in sub["Cidade_UF"]]
                sub["Cidade"] = [p[0] for p in pares]
                sub["Estado"] = [p[1] for p in pares]
                sub["Disciplina"] = sub["Disciplina"].fillna(disc_arquivo).replace("", disc_arquivo)
                sub["Data_Falta"] = data_falta
                sub["Arquivo_Origem"] = nome_limpo
                return sub[["Matricula", "Nome", "Cidade", "Estado", "Disciplina", "Turma", "Data_Falta", "Arquivo_Origem"]]

    registros = []
    for _, row in df_clean.iterrows():
        valores = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() not in ("", "nan", "None")]
        if len(valores) < 2:
            continue
        linha_upper = " ".join(valores).upper()
        if linha_upper.startswith("ID ") or ("NOME" in linha_upper and "TURMA" in linha_upper and "@" not in linha_upper):
            continue

        turma = next((v for v in valores if REGEX_TURMA_APC.search(v)), "")
        email = next((v for v in valores if "@" in v and "." in v), "")
        cid_uf_val = next((v for v in valores if eh_cidade_uf(v)), "")
        cidade, estado = separar_cidade_estado(cid_uf_val)

        val0_limpo = re.sub(r"\.0$", "", valores[0])
        matricula = val0_limpo if REGEX_MATRICULA.match(val0_limpo) else ""

        if matricula and len(valores) >= 2:
            nome_jovem = valores[1]
        elif email and valores.index(email) >= 1:
            nome_jovem = valores[valores.index(email) - 1]
        else:
            nome_jovem = valores[0]

        disciplina = disc_arquivo or "GERAL"
        if not turma:
            turma = disciplina
        if len(nome_jovem) < 3 or nome_jovem.isdigit():
            continue

        registros.append({
            "Matricula": matricula,
            "Nome": nome_jovem,
            "Cidade": cidade,
            "Estado": estado,
            "Disciplina": disciplina,
            "Turma": turma,
            "Data_Falta": data_falta,
            "Arquivo_Origem": nome_limpo
        })

    return pd.DataFrame(registros)

def _processar_unico_item(args):
    b_arq, nome_item, data_padrao_str = args
    nome_curto = nome_item.replace("\\", "/").split("/")[-1]
    df_bruto, _ = converter_bytes_em_dataframe(b_arq, nome_curto)
    if df_bruto is not None:
        df_limpo = extrair_alunos_do_dataframe(df_bruto, nome_item, data_padrao_str)
        if not df_limpo.empty:
            return df_limpo, True
    return None, False

@st.cache_data(show_spinner=False, max_entries=10)
def processar_lote_em_paralelo(itens_bytes_nomes, data_padrao_str):
    tarefas = [(b, nome, data_padrao_str) for b, nome in itens_bytes_nomes]
    dfs_validos = []
    com_faltas = 0
    em_branco = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        for df_res, teve_falta in executor.map(_processar_unico_item, tarefas):
            if teve_falta and df_res is not None:
                dfs_validos.append(df_res)
                com_faltas += 1
            else:
                em_branco += 1

    df_final = pd.concat(dfs_validos, ignore_index=True) if dfs_validos else pd.DataFrame()
    if not df_final.empty:
        df_final = indexar_base_faltas(df_final)
    stats = {"total_arquivos": len(tarefas), "com_faltas": com_faltas, "em_branco": em_branco}
    return df_final, stats

def extrair_itens_upload(lista_arquivos):
    itens = []
    def descompactar_zip(b_zip):
        with zipfile.ZipFile(io.BytesIO(b_zip), "r") as z:
            for info in z.infolist():
                item = info.filename
                if item.endswith("/") or "__MACOSX" in item or item.split("/")[-1].startswith("~$"):
                    continue
                if info.file_size > LIMITE_BYTES_ARQUIVO:
                    continue
                ilow = item.lower()
                if ilow.endswith(".zip"):
                    descompactar_zip(z.read(item))
                elif ilow.endswith((".xls", ".xlsx", ".csv", ".tsv")):
                    itens.append((z.read(item), item))

    for arq in lista_arquivos:
        if arq.name.lower().endswith(".zip"):
            descompactar_zip(arq.getvalue())
        else:
            itens.append((arq.getvalue(), arq.name))
    return itens

if "base_moodle" not in st.session_state:
    st.session_state["base_moodle"] = pd.DataFrame()
if "base_faltas" not in st.session_state:
    st.session_state["base_faltas"] = pd.DataFrame()
if "base_rm" not in st.session_state:
    st.session_state["base_rm"] = pd.DataFrame()

# ==============================================================================
# 5. BARRA LATERAL: BACKUP AUTOMÁTICO + FERRAMENTAS EXCLUSIVAS DE ADMIN
# ==============================================================================
with st.sidebar:
    st.markdown("<h3 class='titulo-secao'>⚡ Suíte Equipe Bojador</h3>", unsafe_allow_html=True)
    if st.session_state.get("is_admin", False):
        st.success("👑 Modo Administrador Ativo")
    else:
        st.caption("👤 Modo Utilizador")

    st.button(
        "🔄 Limpar Todos os Filtros (Geral)",
        on_click=limpar_todos_os_filtros_global,
        use_container_width=True
    )

    st.checkbox(
        f"🚫 Ocultar {len(st.session_state['turmas_desativadas'])} turmas 'A ser desativada'",
        value=False,
        key="ocultar_desativadas"
    )

    st.divider()
    st.caption("📂 **Backup Unificado (Carregamento Automático):**")
    arq_hist = st.file_uploader("Solte o Histórico (.xlsx) para restaurar:", type=["xlsx"], key="up_hist_auto")
    if arq_hist:
        ass_hist = f"{arq_hist.name}_{arq_hist.size}"
        if st.session_state.get("ultimo_hist_carregado") != ass_hist:
            xls = pd.ExcelFile(arq_hist)
            if "Historico_Moodle" in xls.sheet_names:
                st.session_state["base_moodle"] = indexar_base_moodle(pd.read_excel(xls, "Historico_Moodle"))
            if "Historico_Faltas" in xls.sheet_names:
                st.session_state["base_faltas"] = indexar_base_faltas(pd.read_excel(xls, "Historico_Faltas"))
            if "Historico_RM" in xls.sheet_names:
                st.session_state["base_rm"] = indexar_base_rm(
                    pd.read_excel(xls, "Historico_RM"),
                    st.session_state["base_faltas"],
                    st.session_state["base_moodle"]
                )
            st.session_state["ultimo_hist_carregado"] = ass_hist
            st.rerun()

    tem_dados = any(not st.session_state[k].empty for k in ["base_moodle", "base_faltas", "base_rm"])
    if tem_dados:
        bytes_backup = gerar_backup_unificado_bytes(
            st.session_state["base_faltas"],
            st.session_state["base_moodle"],
            st.session_state["base_rm"]
        )
        st.download_button(
            label="💾 Baixar Base Unificada (.xlsx)",
            data=bytes_backup,
            file_name=f"Base_Completa_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

    # Ferramentas restritas ao Administrador (Guilherme)
    if st.session_state.get("is_admin", False):
        st.divider()
        with st.expander("👑 Painel do Administrador"):
            arq_grade = st.file_uploader("Atualizar Grade Horária (.xlsx):", type=["xlsx", "xls"], key="up_grade_auto")
            if arq_grade:
                ass_grade = f"{arq_grade.name}_{arq_grade.size}"
                if st.session_state.get("ultima_grade_lida") != ass_grade:
                    ok, msg = atualizar_banco_via_planilha_grade(arq_grade)
                    st.session_state["ultima_grade_lida"] = ass_grade
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            if st.button("🗑️ Zerar Todas as Bases da Memória", use_container_width=True):
                st.session_state["base_faltas"] = pd.DataFrame()
                st.session_state["base_moodle"] = pd.DataFrame()
                st.session_state["base_rm"] = pd.DataFrame()
                st.session_state["ultimos_arquivos_lidos"] = []
                st.session_state["ultimos_arquivos_moodle"] = []
                st.session_state["ultimos_arquivos_rm"] = []
                st.rerun()
    else:
        st.divider()
        with st.expander("🔑 Acesso Admin"):
            senha_adm_side = st.text_input("Chave de Administrador:", type="password", key="adm_unlock")
            if senha_adm_side:
                if hmac.compare_digest(senha_adm_side.encode("utf-8"), str(st.secrets.get("SENHA_ADMIN", "admin2026")).encode("utf-8")):
                    st.session_state["is_admin"] = True
                    st.rerun()
                else:
                    st.error("Chave incorreta.")

# ==============================================================================
# FRAGMENTO 1: PAINEL DE FALTAS
# ==============================================================================
@st.fragment
def renderizar_painel_faltas():
    df_f = st.session_state["base_faltas"]
    if df_f.empty:
        return

    col_tit_f, col_btn_f = st.columns([3.2, 1])
    with col_tit_f:
        st.markdown("<h4 class='titulo-secao'>⚡ Filtros Instantâneos (Instrutor, Código da Disciplina, Período e Turno)</h4>", unsafe_allow_html=True)
    with col_btn_f:
        st.button("🔄 Limpar Filtros Aplicados", on_click=limpar_filtros_faltas, key="btn_limpar_f_top", use_container_width=True)

    f1, f2, f3, f4, f5, f6 = st.columns([1.4, 1.4, 0.9, 1.1, 0.9, 1.2])

    with f1:
        opcoes_instrutor = ["🌟 Todos os Instrutores"] + list(st.session_state["banco_turmas_atual"].keys()) + ["Não Mapeado / Outros"]
        sel_instrutor_f = st.selectbox("👤 1. Instrutor(a):", opcoes_instrutor, index=0, key="f_inst")
    with f3:
        modo_tempo_f = st.selectbox("🗓️ 3. Modo:", ["📅 Dia", "📆 Semana", "🗓️ Mês", "♾️ Tudo"], index=0, key="f_modo")
    with f4:
        if modo_tempo_f == "📅 Dia":
            opcoes_p = ["Todos os Dias"] + sorted(df_f["Data_Falta"].unique().tolist(), reverse=True)
            sel_periodo_f = st.selectbox("Escolher Dia:", opcoes_p, key="f_dia")
        elif modo_tempo_f == "📆 Semana":
            opcoes_p = ["Todas as Semanas"] + sorted(df_f["Semana_Ano"].unique().tolist(), reverse=True)
            sel_periodo_f = st.selectbox("Escolher Semana:", opcoes_p, key="f_sem")
        elif modo_tempo_f == "🗓️ Mês":
            opcoes_p = ["Todos os Meses"] + sorted(df_f["Mes_Ano"].unique().tolist(), reverse=True)
            sel_periodo_f = st.selectbox("Escolher Mês:", opcoes_p, key="f_mes")
        else:
            sel_periodo_f = "Tudo"
            st.text_input("Período:", value="Todo o Histórico", disabled=True)

    df_sub = filtrar_rapido_por_instrutor(df_f, sel_instrutor_f)
    if modo_tempo_f == "📅 Dia" and sel_periodo_f != "Todos os Dias":
        df_sub = df_sub[df_sub["Data_Falta"] == sel_periodo_f]
    elif modo_tempo_f == "📆 Semana" and sel_periodo_f != "Todas as Semanas":
        df_sub = df_sub[df_sub["Semana_Ano"] == sel_periodo_f]
    elif modo_tempo_f == "🗓️ Mês" and sel_periodo_f != "Todos os Meses":
        df_sub = df_sub[df_sub["Mes_Ano"] == sel_periodo_f]

    with f2:
        codigos_disc = sorted(df_sub["Disciplina"].unique().tolist())
        codigos_apc = sorted([c for c in df_sub["_cod_apc"].unique().tolist() if c and c not in codigos_disc])
        opcoes_disc_f = ["Todas as Disciplinas"] + codigos_disc + [f"Código Turma: {a}" for a in codigos_apc]
        if st.session_state.get("f_disc") not in opcoes_disc_f:
            st.session_state["f_disc"] = "Todas as Disciplinas"
        sel_disc_f = st.selectbox("📘 2. Código da Disciplina:", opcoes_disc_f, key="f_disc")
    with f5:
        sel_turno_f = st.selectbox("🕒 4. Turno:", ["Todos (M + V)", "M - Manhã", "V - Tarde"], key="f_turno")
    with f6:
        busca_f = st.text_input("🔍 5. Busca Livre:", placeholder="Nome, Matrícula, UF...", key="f_busca")

    if sel_disc_f != "Todas as Disciplinas":
        if sel_disc_f.startswith("Código Turma: "):
            apc_alvo = sel_disc_f.replace("Código Turma: ", "")
            df_sub = df_sub[df_sub["_cod_apc"] == apc_alvo]
        else:
            df_sub = df_sub[df_sub["Disciplina"] == sel_disc_f]

    if sel_turno_f != "Todos (M + V)":
        df_sub = df_sub[df_sub["Turno"] == sel_turno_f]
    if busca_f:
        df_sub = df_sub[df_sub["_busca_idx"].str.contains(busca_f.strip().upper(), regex=False, na=False)]

    if df_sub.empty:
        st.warning("⚠️ Nenhum registo encontrado para esta combinação de filtros. Clique em '🔄 Limpar Filtros Aplicados'.")
        return

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Jovens Ausentes", len(df_sub))
    m2.metric("Disciplinas Ativas", df_sub["Disciplina"].nunique())
    m3.metric("Turmas no Filtro", df_sub["Turma"].nunique())
    m4.metric("☀️ Manhã (M)", int((df_sub["Turno"] == "M - Manhã").sum()))
    m5.metric("🌇 Tarde (V)", int((df_sub["Turno"] == "V - Tarde").sum()))

    sub_f1, sub_f2, sub_f3 = st.tabs([
        "📋 1. RELAÇÃO DE JOVENS AUSENTES (DIA / SEMANA / MÊS)",
        "🚨 2. RANKING DE REINCIDÊNCIA (QUEM MAIS FALTA)",
        "📘 3. RESUMO POR DISCIPLINA E TURMA"
    ])

    colunas_foco = ["Lancado_RM", "Matricula", "Nome", "Cidade", "Estado", "Disciplina", "Turma", "Turno", "Data_Falta", "Instrutor"]

    with sub_f1:
        df_ordenado = df_sub[colunas_foco].sort_values(by=["Turno", "Disciplina", "Turma", "Nome"])
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
        st.session_state["base_faltas"].loc[df_editado.index, "Lancado_RM"] = df_editado["Lancado_RM"]

        st.download_button(
            label="📥 Exportar Tabela Filtrada (.xlsx)",
            data=converter_df_para_excel_bytes(df_ordenado, "Faltas_Filtradas"),
            file_name=f"Faltas_Filtradas_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with sub_f2:
        rank_f = (
            df_sub.groupby(["Matricula", "Nome", "Cidade", "Estado", "Turma", "Turno"], as_index=False)
            .agg(
                Total_Faltas=("Data_Falta", "count"),
                Disciplinas=("Disciplina", lambda x: ", ".join(sorted(set(x)))),
                Datas_Ausente=("Data_Falta", lambda x: ", ".join(sorted(set(x))))
            )
            .sort_values(by="Total_Faltas", ascending=False)
        )
        st.dataframe(rank_f, use_container_width=True, hide_index=True)

    with sub_f3:
        resumo_t = (
            df_sub.groupby(["Turno", "Disciplina", "Turma", "Instrutor"], as_index=False)
            .agg(Total_Ausencias=("Nome", "count"), Jovens_Unicos=("Nome", "nunique"))
            .sort_values(by=["Turno", "Total_Ausencias"], ascending=[True, False])
        )
        st.dataframe(resumo_t, use_container_width=True, hide_index=True)

# ==============================================================================
# FRAGMENTO 2: PAINEL DO MOODLE
# ==============================================================================
@st.fragment
def renderizar_painel_moodle():
    df_m = st.session_state["base_moodle"]
    if df_m.empty:
        return

    col_tit_m, col_btn_m = st.columns([3.2, 1])
    with col_tit_m:
        st.markdown("<h4 class='titulo-secao'>⚡ Filtros Instantâneos do Moodle (Instrutor, Disciplina, Período e Turno)</h4>", unsafe_allow_html=True)
    with col_btn_m:
        st.button("🔄 Limpar Filtros Aplicados", on_click=limpar_filtros_moodle, key="btn_limpar_m_top", use_container_width=True)

    mc1, mc2, mc3, mc4, mc5, mc6 = st.columns([1.4, 1.4, 0.9, 1.1, 0.9, 1.2])
    with mc1:
        opcoes_inst_m = ["🌟 Todos os Instrutores"] + list(st.session_state["banco_turmas_atual"].keys()) + ["Não Mapeado / Outros"]
        sel_inst_m = st.selectbox("👤 1. Instrutor(a):", opcoes_inst_m, index=0, key="m_inst")
    with mc3:
        modo_m = st.selectbox("🗓️ 3. Modo:", ["📅 Dia", "📆 Semana", "🗓️ Mês", "♾️ Tudo"], index=0, key="m_modo")
    with mc4:
        if modo_m == "📅 Dia":
            op_pm = ["Todos os Dias"] + sorted(df_m["Data_Coleta"].unique().tolist(), reverse=True)
            sel_per_m = st.selectbox("Escolher Dia:", op_pm, key="m_dia")
        elif modo_m == "📆 Semana":
            op_pm = ["Todas as Semanas"] + sorted(df_m["Semana_Ano"].unique().tolist(), reverse=True)
            sel_per_m = st.selectbox("Escolher Semana:", op_pm, key="m_sem")
        elif modo_m == "🗓️ Mês":
            op_pm = ["Todos os Meses"] + sorted(df_m["Mes_Ano"].unique().tolist(), reverse=True)
            sel_per_m = st.selectbox("Escolher Mês:", op_pm, key="m_mes")
        else:
            sel_per_m = "Tudo"
            st.text_input("Período:", value="Todo o Histórico", disabled=True, key="m_tudo")

    df_m_sub = filtrar_rapido_por_instrutor(df_m, sel_inst_m)
    if modo_m == "📅 Dia" and sel_per_m != "Todos os Dias":
        df_m_sub = df_m_sub[df_m_sub["Data_Coleta"] == sel_per_m]
    elif modo_m == "📆 Semana" and sel_per_m != "Todas as Semanas":
        df_m_sub = df_m_sub[df_m_sub["Semana_Ano"] == sel_per_m]
    elif modo_m == "🗓️ Mês" and sel_per_m != "Todos os Meses":
        df_m_sub = df_m_sub[df_m_sub["Mes_Ano"] == sel_per_m]

    with mc2:
        disc_m_disp = sorted(df_m_sub["Disciplina"].unique().tolist())
        apc_m_disp = sorted([c for c in df_m_sub["_cod_apc"].unique().tolist() if c and c not in disc_m_disp])
        opcoes_disc_m = ["Todas as Disciplinas"] + disc_m_disp + [f"Código Turma: {a}" for a in apc_m_disp]
        if st.session_state.get("m_disc") not in opcoes_disc_m:
            st.session_state["m_disc"] = "Todas as Disciplinas"
        sel_disc_m = st.selectbox("📘 2. Código da Disciplina:", opcoes_disc_m, key="m_disc")
    with mc5:
        sel_turno_m = st.selectbox("🕒 4. Turno:", ["Todos (M + V)", "M - Manhã", "V - Tarde"], key="m_turno")
    with mc6:
        busca_m = st.text_input("🔍 5. Busca Livre:", placeholder="Jovem, Atividade...", key="m_busca")

    if sel_disc_m != "Todas as Disciplinas":
        if sel_disc_m.startswith("Código Turma: "):
            apc_alvo_m = sel_disc_m.replace("Código Turma: ", "")
            df_m_sub = df_m_sub[df_m_sub["_cod_apc"] == apc_alvo_m]
        else:
            df_m_sub = df_m_sub[df_m_sub["Disciplina"] == sel_disc_m]

    if sel_turno_m != "Todos (M + V)":
        df_m_sub = df_m_sub[df_m_sub["Turno"] == sel_turno_m]
    if busca_m:
        df_m_sub = df_m_sub[df_m_sub["_busca_idx"].str.contains(busca_m.strip().upper(), regex=False, na=False)]

    if df_m_sub.empty:
        st.warning("⚠️ Nenhum registo encontrado para esta combinação de filtros. Clique em '🔄 Limpar Filtros Aplicados'.")
        return

    km1, km2, km3, km4, km5 = st.columns(5)
    km1.metric("Pendências Listadas", len(df_m_sub))
    km2.metric("Disciplinas no Filtro", df_m_sub["Disciplina"].nunique())
    km3.metric("Turmas no Filtro", df_m_sub["Turma"].nunique())
    km4.metric("☀️ Manhã (M)", int((df_m_sub["Turno"] == "M - Manhã").sum()))
    km5.metric("🌇 Tarde (V)", int((df_m_sub["Turno"] == "V - Tarde").sum()))

    sub_m1, sub_m2 = st.tabs([
        "📋 1. PENDÊNCIAS POR INSTRUTOR E DISCIPLINA",
        "📈 2. COMPARATIVO SEMANAL / MENSAL (QUEM REGULARIZOU)"
    ])
    with sub_m1:
        cols_m_ordem = ["Data_Coleta", "Instrutor", "Disciplina", "Turno", "Turma", "Atividade", "Status", "Jovem", "Email_Enviado"]
        cols_m_pres = [c for c in cols_m_ordem if c in df_m_sub.columns]
        df_m_view = df_m_sub[cols_m_pres]
        st.dataframe(df_m_view, use_container_width=True, hide_index=True)

        st.download_button(
            label="📥 Exportar Pendências Filtradas (.xlsx)",
            data=converter_df_para_excel_bytes(df_m_view, "Moodle_Filtrado"),
            file_name=f"Moodle_Filtrado_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with sub_m2:
        datas_m = sorted(df_m["Data_Coleta"].unique().tolist())
        if len(datas_m) < 2:
            st.info("Registe pelo menos 2 datas diferentes de coleta para comparar quem regularizou na semana.")
        else:
            cd1, cd2 = st.columns(2)
            with cd1:
                d_ant = st.selectbox("1ª Coleta (Cobrança Inicial):", datas_m, index=0)
            with cd2:
                d_nov = st.selectbox("2ª Coleta (Conferência):", datas_m, index=len(datas_m)-1)
            df_a = filtrar_rapido_por_instrutor(df_m[df_m["Data_Coleta"] == d_ant], sel_inst_m)
            df_n = filtrar_rapido_por_instrutor(df_m[df_m["Data_Coleta"] == d_nov], sel_inst_m)
            comp = pd.merge(df_a, df_n, on=["Turma", "Atividade", "Jovem"], how="outer", indicator=True)
            st.metric("✅ Jovens que Regularizaram após o E-mail", int((comp["_merge"] == "left_only").sum()))
            st.dataframe(comp[comp["_merge"] == "left_only"][["Turma", "Atividade", "Jovem"]], use_container_width=True, hide_index=True)

# ==============================================================================
# FRAGMENTO 3: PAINEL DE AVALIAÇÃO DE DESEMPENHO (TOTVS RM)
# ==============================================================================
@st.fragment
def renderizar_painel_rm():
    df_r = st.session_state["base_rm"]
    if df_r.empty:
        return

    col_tit_r, col_btn_r = st.columns([3.2, 1])
    with col_tit_r:
        st.markdown("<h4 class='titulo-secao'>⚡ Filtros Instantâneos da Avaliação de Desempenho (RM)</h4>", unsafe_allow_html=True)
    with col_btn_r:
        st.button("🔄 Limpar Filtros Aplicados", on_click=limpar_filtros_rm, key="btn_limpar_r_top", use_container_width=True)

    rc1, rc2, rc3, rc4, rc5 = st.columns([1.4, 1.3, 1.2, 1.3, 1.4])

    with rc1:
        opcoes_inst_r = ["🌟 Todos os Instrutores"] + list(st.session_state["banco_turmas_atual"].keys()) + ["Não Mapeado / Outros"]
        sel_inst_r = st.selectbox("👤 1. Instrutor(a):", opcoes_inst_r, index=0, key="r_inst")
    with rc2:
        status_disp = sorted(df_r["STATUS_PROVA"].unique().tolist())
        padrao_pendentes = [s for s in status_disp if s.upper() != "FINALIZADO"] or status_disp
        sel_status_prova = st.multiselect("📊 2. Status da Prova:", options=status_disp, default=padrao_pendentes, key="r_st_prova")
    with rc3:
        per_status_disp = ["Todos"] + sorted(df_r["STATUS_PERIODO"].unique().tolist())
        sel_status_per = st.selectbox("⏳ 3. Status Período:", per_status_disp, key="r_st_per")
    with rc4:
        periodos_disp = ["Todos os Períodos"] + sorted(df_r["NOMEPERIODO"].unique().tolist())
        sel_nome_per = st.selectbox("🗓️ 4. Ciclo / Período:", periodos_disp, key="r_ciclo")
    with rc5:
        busca_r = st.text_input("🔍 5. Buscar Jovem / Código / Cidade:", placeholder="Nome, Código Acesso, Cidade...", key="r_busca")

    df_r_sub = filtrar_rapido_por_instrutor(df_r, sel_inst_r)
    if sel_status_prova:
        df_r_sub = df_r_sub[df_r_sub["STATUS_PROVA"].isin(sel_status_prova)]
    if sel_status_per != "Todos":
        df_r_sub = df_r_sub[df_r_sub["STATUS_PERIODO"] == sel_status_per]
    if sel_nome_per != "Todos os Períodos":
        df_r_sub = df_r_sub[df_r_sub["NOMEPERIODO"] == sel_nome_per]
    if busca_r:
        df_r_sub = df_r_sub[df_r_sub["_busca_idx"].str.contains(busca_r.strip().upper(), regex=False, na=False)]

    if df_r_sub.empty:
        st.warning("⚠️ Nenhum registo encontrado para esta combinação de filtros. Clique em '🔄 Limpar Filtros Aplicados'.")
        return

    kr1, kr2, kr3, kr4, kr5 = st.columns(5)
    kr1.metric("Registos no Filtro", len(df_r_sub))
    kr2.metric("🚨 Pendentes", int((df_r_sub["STATUS_PROVA"].str.upper() == "PENDENTE").sum()))
    kr3.metric("⏳ Em Andamento", int((df_r_sub["STATUS_PROVA"].str.upper() == "ANDAMENTO").sum()))
    kr4.metric("✅ Finalizados (Geral)", int((df_r["STATUS_PROVA"].str.upper() == "FINALIZADO").sum()))
    kr5.metric("Períodos Ativos", df_r_sub["NOMEPERIODO"].nunique())

    sub_r1, sub_r2, sub_r3 = st.tabs([
        "📋 1. RELAÇÃO DE JOVENS & CÓDIGOS DE ACESSO",
        "📲 2. LISTA PRONTA PARA COBRANÇA (COM CÓDIGO DE ACESSO)",
        "📊 3. RESUMO POR PERÍODO AVALIATIVO E CIDADE"
    ])

    cols_rm_foco = [
        "STATUS_PROVA", "STATUS_PERIODO", "CODPESSOA", "NOME", "CODIGO_ACESSO",
        "NOMEPERIODO", "DATAINICIAL", "DATAFINAL", "CIDADE", "Turma", "Turno", "Instrutor"
    ]
    cols_rm_pres = [c for c in cols_rm_foco if c in df_r_sub.columns]

    with sub_r1:
        df_r_view = df_r_sub[cols_rm_pres]
        st.dataframe(df_r_view, use_container_width=True, hide_index=True)
        st.download_button(
            label="📥 Exportar Avaliação Filtrada (.xlsx)",
            data=converter_df_para_excel_bytes(df_r_view, "Avaliacao_RM_Filtrada"),
            file_name=f"Avaliacao_RM_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with sub_r2:
        st.caption("💡 Lista gerada automaticamente de forma vetorizada com Nome, Código de Acesso e Prazo Final:")
        df_cob = df_r_sub[df_r_sub["STATUS_PROVA"].str.upper() != "FINALIZADO"].head(500)
        if not df_cob.empty:
            cod_ac = np.where(df_cob["CODIGO_ACESSO"] != "", df_cob["CODIGO_ACESSO"], "Sem código")
            serie_linhas = (
                "• " + df_cob["NOME"] +
                " | Código de Acesso: " + cod_ac +
                " | Período: " + df_cob["NOMEPERIODO"] +
                " (Até " + df_cob["DATAFINAL"] + ")" +
                " | Cidade: " + df_cob["CIDADE"]
            )
            texto_cobranca = "\n".join(serie_linhas.tolist())
        else:
            texto_cobranca = "Nenhum jovem pendente no filtro atual."
        st.text_area("📋 Copie as linhas abaixo para cobrar os jovens:", value=texto_cobranca, height=220)

    with sub_r3:
        resumo_ciclo = (
            df_r_sub.groupby(["NOMEPERIODO", "STATUS_PROVA", "STATUS_PERIODO"], as_index=False)
            .agg(Total_Jovens=("NOME", "count"), Cidades_Afetadas=("CIDADE", "nunique"))
            .sort_values(by=["NOMEPERIODO", "Total_Jovens"], ascending=[True, False])
        )
        st.dataframe(resumo_ciclo, use_container_width=True, hide_index=True)

# ==============================================================================
# 6. NAVEGAÇÃO PRINCIPAL POR ABAS NATIVAS (TRANSIÇÃO 0ms + 100% AUTOMÁTICA)
# ==============================================================================
st.markdown("<h3 class='titulo-secao'>⚡ Central de Acompanhamento Demà & RM</h3>", unsafe_allow_html=True)
qtd_faltas = len(st.session_state["base_faltas"])
qtd_moodle = len(st.session_state["base_moodle"])
qtd_rm = len(st.session_state["base_rm"])

aba_mod_faltas, aba_mod_moodle, aba_mod_rm, aba_mod_360 = st.tabs([
    f"📅 1. CONTROLE DE FALTAS ({qtd_faltas})",
    f"📚 2. ATIVIDADES MOODLE ({qtd_moodle})",
    f"📝 3. AVALIAÇÃO RM ({qtd_rm})",
    "🌐 4. VISÃO 360º GERAL"
])

# ------------------------------------------------------------------------------
# ABA 1: CONTROLE DE FALTAS (CARREGAMENTO AUTOMÁTICO)
# ------------------------------------------------------------------------------
with aba_mod_faltas:
    st.markdown("""
    <div class="banner-dema" style="border-left-color:#e65100;">
        <h2>📅 MÓDULO 1: Controle de Faltas (SharePoint ➔ Diário de Classe RM)</h2>
        <p>Carregamento Automático: solte o <b>.ZIP</b> ou as planilhas <b>.XLS / .XLSX</b> e os dados aparecem imediatamente.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR FOLHAS DE CÁLCULO OU PACOTE .ZIP DE FALTAS (Carregamento Automático)", expanded=st.session_state["base_faltas"].empty):
        c_dt, c_up = st.columns([1, 2.5])
        with c_dt:
            data_ref = st.date_input("📅 Data padrão:", value=date.today(), format="DD/MM/YYYY")
            st.button(
                "🔄 Limpar Filtros Aplicados",
                on_click=limpar_filtros_faltas,
                key="btn_limpar_f_exp",
                use_container_width=True
            )

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
                with st.spinner("⚡ Leitura paralela de alta velocidade em curso..."):
                    itens_extraidos = extrair_itens_upload(arquivos_up)
                    df_novos, stats = processar_lote_em_paralelo(itens_extraidos, data_ref.strftime("%Y-%m-%d"))
                    st.session_state["ultimos_arquivos_lidos"] = assinatura_atual
                    st.session_state["ultimo_diagnostico"] = stats

                    if not df_novos.empty:
                        df_acum = pd.concat([st.session_state["base_faltas"], df_novos], ignore_index=True)
                        df_acum = df_acum.drop_duplicates(
                            subset=["Data_Falta", "Disciplina", "Turma", "Matricula", "Nome"], keep="first"
                        ).reset_index(drop=True)
                        st.session_state["base_faltas"] = df_acum
                        st.rerun()

        if "ultimo_diagnostico" in st.session_state:
            st_diag = st.session_state["ultimo_diagnostico"]
            st.markdown(
                f"<div class='visor-sucesso'>✅ Leitura Concluída: {st_diag['total_arquivos']} ficheiros processados "
                f"| {st_diag['com_faltas']} com jovens ausentes | {st_diag['em_branco']} em branco (810 bytes).</div>",
                unsafe_allow_html=True
            )

    renderizar_painel_faltas()

# ------------------------------------------------------------------------------
# ABA 2: ATIVIDADES MOODLE (CARREGAMENTO AUTOMÁTICO SEM CLICAR EM BOTÃO!)
# ------------------------------------------------------------------------------
with aba_mod_moodle:
    st.markdown("""
    <div class="banner-dema">
        <h2>📚 MÓDULO 2: Acompanhamento de Atividades (Moodle Demà Digital)</h2>
        <p>Carregamento Automático: solte as planilhas/ficheiros (<b>.TSV, .CSV, .XLSX, .XLS, .ZIP</b>) ou cole o relatório e os dados aparecem na hora.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR DADOS DO MOODLE (Carregamento Automático ao Soltar ou Colar)", expanded=st.session_state["base_moodle"].empty):
        cm1, cm2, cm3 = st.columns([1, 1.5, 1])
        with cm1:
            dt_moodle = st.date_input("📅 Data da Coleta:", value=date.today(), format="DD/MM/YYYY", key="dt_m_in")
        with cm2:
            disc_moodle_in = st.text_input(
                "📘 Código da Disciplina (Opcional):",
                value="",
                placeholder="Automático pela Extensão/Turma",
                key="disc_m_in"
            )
        with cm3:
            st.write("")
            st.button(
                "🔄 Limpar Filtros Aplicados",
                on_click=limpar_filtros_moodle,
                key="btn_limpar_m_exp",
                use_container_width=True
            )

        col_in_m1, col_in_m2 = st.columns(2)
        with col_in_m1:
            txt_m = st.text_area(
                "Opção A: Cole (Ctrl+V) o relatório da Extensão (processa automaticamente):",
                height=125,
                placeholder="Instrutor\tDisciplina\tTurno\tTurma\tAtividade\tStatus\tJovem\tEmail_Enviado",
                key="txt_moodle_auto"
            )
        with col_in_m2:
            arqs_moodle_up = st.file_uploader(
                "Opção B: Arraste Planilhas / Ficheiros do Moodle (.tsv, .csv, .xlsx, .xls, .zip):",
                type=["tsv", "csv", "txt", "xlsx", "xls", "zip"],
                accept_multiple_files=True,
                key="uploader_moodle_files"
            )

        # PROCESSAMENTO AUTOMÁTICO MOODLE (TEXTO COLADO OU FICHEIROS SOLTOS)
        hash_txt_m = hashlib.md5(txt_m.strip().encode("utf-8")).hexdigest() if txt_m.strip() else ""
        ass_arqs_m = [f"{a.name}_{a.size}" for a in arqs_moodle_up] if arqs_moodle_up else []
        assinatura_moodle_atual = f"{hash_txt_m}_{ass_arqs_m}_{dt_moodle}_{disc_moodle_in.strip()}"

        if (txt_m.strip() or arqs_moodle_up) and st.session_state.get("ultima_assinatura_moodle") != assinatura_moodle_atual:
            novos_m = []
            if txt_m.strip():
                try:
                    df_tm = pd.read_csv(io.StringIO(txt_m.strip()), sep="\t")
                    if not df_tm.empty:
                        novos_m.append(df_tm)
                except Exception as e:
                    st.error(f"Erro ao ler texto colado: {e}")

            if arqs_moodle_up:
                itens_m = extrair_itens_upload(arqs_moodle_up)
                for b_item, nome_item in itens_m:
                    try:
                        nome_m = nome_item.lower()
                        if nome_m.endswith((".xlsx", ".xls")):
                            df_m_arq, _ = converter_bytes_em_dataframe(b_item, nome_item)
                            if df_m_arq is not None and not df_m_arq.empty:
                                prim_linha = [str(x).strip() for x in df_m_arq.iloc[0].values]
                                if any(k in " ".join(prim_linha).upper() for k in ["TURMA", "JOVEM", "ATIVIDADE"]):
                                    df_m_arq.columns = prim_linha
                                    df_m_arq = df_m_arq.iloc[1:].reset_index(drop=True)
                                novos_m.append(df_m_arq)
                        else:
                            conteudo_m = b_item.decode("utf-8-sig", errors="ignore")
                            sep_m = "\t" if "\t" in conteudo_m else (";" if ";" in conteudo_m else ",")
                            df_cm = pd.read_csv(io.StringIO(conteudo_m), sep=sep_m)
                            if not df_cm.empty:
                                novos_m.append(df_cm)
                    except Exception as e:
                        st.error(f"Erro ao ler ficheiro {nome_item}: {e}")

            st.session_state["ultima_assinatura_moodle"] = assinatura_moodle_atual
            if novos_m:
                df_lote = pd.concat(novos_m, ignore_index=True)
                df_lote["Data_Coleta"] = dt_moodle.strftime("%Y-%m-%d")
                if disc_moodle_in.strip():
                    df_lote["Disciplina"] = disc_moodle_in.strip()
                df_lote = indexar_base_moodle(df_lote)
                df_comb_m = pd.concat([st.session_state["base_moodle"], df_lote], ignore_index=True)
                df_comb_m = df_comb_m.drop_duplicates(
                    subset=["Data_Coleta", "Disciplina", "Turma", "Atividade", "Jovem"], keep="last"
                ).reset_index(drop=True)
                st.session_state["base_moodle"] = df_comb_m
                st.rerun()

    renderizar_painel_moodle()

# ------------------------------------------------------------------------------
# ABA 3: AVALIAÇÃO DE DESEMPENHO RM (CARREGAMENTO AUTOMÁTICO SEM CLICAR EM BOTÃO!)
# ------------------------------------------------------------------------------
with aba_mod_rm:
    st.markdown("""
    <div class="banner-dema" style="border-left-color:#1565c0;">
        <h2>📝 MÓDULO 3: Avaliação de Desempenho (Consulta SQL TOTVS RM)</h2>
        <p>Carregamento Automático: solte o ficheiro <b>avaliacao_rm.tsv / .xlsx / .zip</b> ou cole os dados e a curadoria aparece imediatamente.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 IMPORTAR DADOS DA CONSULTA SQL DO RM (Carregamento Automático)", expanded=st.session_state["base_rm"].empty):
        col_rm_in1, col_rm_in2 = st.columns(2)
        with col_rm_in1:
            txt_rm = st.text_area(
                "Opção A: Cole (Ctrl+V) os dados copiados pelo botão da Extensão no RM:",
                height=125,
                placeholder="INSTRUTOR_FILTRO\tSTATUS_PROVA\tSTATUS_PERIODO\tCODPESSOA\tCODPROVA\tCODPERIODO\tNOMEPROVA\tNOMEPERIODO\tDATAINICIAL\tDATAFINAL\tCODIGO_ACESSO\tNOME\tCIDADE",
                key="txt_rm_auto"
            )
        with col_rm_in2:
            arqs_rm_up = st.file_uploader(
                "Opção B: Arraste o ficheiro avaliacao_rm.tsv / .xlsx / .zip baixado:",
                type=["tsv", "csv", "txt", "xlsx", "xls", "zip"],
                accept_multiple_files=True,
                key="uploader_rm_files"
            )

        st.button(
            "🔄 Limpar Filtros Aplicados",
            on_click=limpar_filtros_rm,
            key="btn_limpar_r_exp",
            use_container_width=True
        )

        # PROCESSAMENTO AUTOMÁTICO AVALIAÇÃO RM (TEXTO OU FICHEIROS)
        hash_txt_r = hashlib.md5(txt_rm.strip().encode("utf-8")).hexdigest() if txt_rm.strip() else ""
        ass_arqs_r = [f"{a.name}_{a.size}" for a in arqs_rm_up] if arqs_rm_up else []
        assinatura_rm_atual = f"{hash_txt_r}_{ass_arqs_r}"

        if (txt_rm.strip() or arqs_rm_up) and st.session_state.get("ultima_assinatura_rm") != assinatura_rm_atual:
            novos_rm_auto = []
            if txt_rm.strip():
                df_txt_r = ler_texto_rm_blindado(txt_rm.strip())
                if not df_txt_r.empty:
                    novos_rm_auto.append(df_txt_r)

            if arqs_rm_up:
                itens_r = extrair_itens_upload(arqs_rm_up)
                for b_item, nome_item in itens_r:
                    try:
                        if nome_item.lower().endswith((".xlsx", ".xls")):
                            df_r_temp = pd.read_excel(io.BytesIO(b_item))
                        else:
                            cont_r = b_item.decode("utf-8-sig", errors="ignore")
                            df_r_temp = ler_texto_rm_blindado(cont_r)
                        if not df_r_temp.empty:
                            novos_rm_auto.append(df_r_temp)
                    except Exception as e:
                        st.error(f"Erro ao ler ficheiro {nome_item}: {e}")

            st.session_state["ultima_assinatura_rm"] = assinatura_rm_atual
            if novos_rm_auto:
                df_lote_r = pd.concat(novos_rm_auto, ignore_index=True)
                df_comb_r = pd.concat([st.session_state["base_rm"], df_lote_r], ignore_index=True)
                df_comb_r = indexar_base_rm(df_comb_r, st.session_state["base_faltas"], st.session_state["base_moodle"])
                df_comb_r = df_comb_r.drop_duplicates(
                    subset=["CODPESSOA", "NOMEPERIODO", "NOME"], keep="last"
                ).reset_index(drop=True)
                st.session_state["base_rm"] = df_comb_r
                st.rerun()

    renderizar_painel_rm()

# ------------------------------------------------------------------------------
# ABA 4: VISÃO 360º GERAL
# ------------------------------------------------------------------------------
with aba_mod_360:
    st.markdown("""
    <div class="banner-dema" style="border-left-color:#2e7d32;">
        <h2>🌐 MÓDULO 4: Visão 360º do Jovem (Faltas + Moodle + Avaliação RM)</h2>
        <p>Busca unificada e instantânea nas 3 bases simultaneamente.</p>
    </div>
    """, unsafe_allow_html=True)

    @st.fragment
    def renderizar_busca_360():
        c_b360, c_lim360 = st.columns([3.2, 1])
        with c_b360:
            termo_360 = st.text_input(
                "🔍 Digite o Nome do Jovem, Matrícula, Código de Acesso, Disciplina ou Turma:",
                key="busca_360_input"
            )
        with c_lim360:
            st.write("")
            st.button("🔄 Limpar Filtro de Busca", on_click=limpar_filtros_360, use_container_width=True)

        if termo_360:
            t_up = termo_360.strip().upper()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<h4 class='titulo-secao'>📅 1. Faltas</h4>", unsafe_allow_html=True)
                df_f = st.session_state["base_faltas"]
                if not df_f.empty:
                    res_f = df_f[df_f["_busca_idx"].str.contains(t_up, regex=False, na=False)]
                    cols_360_f = ["Data_Falta", "Matricula", "Nome", "Disciplina", "Turma", "Turno"]
                    st.dataframe(res_f[[c for c in cols_360_f if c in res_f.columns]], use_container_width=True, hide_index=True)
            with c2:
                st.markdown("<h4 class='titulo-secao'>📚 2. Atividades Moodle</h4>", unsafe_allow_html=True)
                df_m = st.session_state["base_moodle"]
                if not df_m.empty:
                    res_m = df_m[df_m["_busca_idx"].str.contains(t_up, regex=False, na=False)]
                    cols_360_m = ["Data_Coleta", "Disciplina", "Turma", "Jovem", "Atividade"]
                    st.dataframe(res_m[[c for c in cols_360_m if c in res_m.columns]], use_container_width=True, hide_index=True)
            with c3:
                st.markdown("<h4 class='titulo-secao'>📝 3. Avaliação RM</h4>", unsafe_allow_html=True)
                df_r = st.session_state["base_rm"]
                if not df_r.empty:
                    res_r = df_r[df_r["_busca_idx"].str.contains(t_up, regex=False, na=False)]
                    cols_360_r = ["NOME", "STATUS_PROVA", "NOMEPERIODO", "CODIGO_ACESSO", "DATAFINAL"]
                    st.dataframe(res_r[[c for c in cols_360_r if c in res_r.columns]], use_container_width=True, hide_index=True)

    renderizar_busca_360()
