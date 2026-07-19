"""style.py - CSS e identidad visual Primax compartida entre paginas."""
import streamlit as st

NARANJA = "#FF5B00"
AZUL = "#002855"
AMARILLO = "#FFC700"
BLANCO = "#FFFFFF"
GRIS = "#F4F6F9"

PLOTLY_COLORS = {"Gasolina": NARANJA, "Diesel": AZUL, "Ingresos": AZUL,
                  "Gastos": NARANJA, "Creditos": AZUL, "Prestamos": AMARILLO}


def inject_css():
    st.markdown(f"""
    <style>
    .stApp {{ background-color: {BLANCO}; }}
    section[data-testid="stSidebar"] {{
        background-color: {AZUL};
    }}
    section[data-testid="stSidebar"] * {{ color: {BLANCO} !important; }}
    h1, h2, h3 {{ color: {AZUL}; }}
    div[data-testid="stMetric"] {{
        background-color: {GRIS};
        border-left: 6px solid {NARANJA};
        border-radius: 6px;
        padding: 12px 16px;
    }}
    div[data-testid="stMetric"] label {{ color: {AZUL} !important; }}
    .stButton>button {{
        background-color: {NARANJA};
        color: {BLANCO};
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }}
    .stButton>button:hover {{
        background-color: #e05200;
        color: {BLANCO};
    }}
    thead tr th {{
        background-color: {AZUL} !important;
        color: {BLANCO} !important;
    }}
    .primax-header {{
        background-color: {AZUL};
        color: {BLANCO};
        padding: 14px 20px;
        border-radius: 8px;
        border-left: 8px solid {NARANJA};
        margin-bottom: 18px;
    }}
    .primax-alert {{
        background-color: #FFF7E0;
        border-left: 6px solid {AMARILLO};
        padding: 10px 14px;
        border-radius: 6px;
        color: {AZUL};
    }}
    </style>
    """, unsafe_allow_html=True)


def header(title, subtitle=""):
    sub = f"<div style='opacity:.85;font-size:.9rem'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"<div class='primax-header'><h2 style='color:#FFFFFF;margin:0'>{title}</h2>{sub}</div>",
                unsafe_allow_html=True)
