import pandas as pd
import streamlit as st

@st.cache_data
def cargar_datos():

    delitos = pd.read_excel(
        "data/REPORTE_DELITOS.xlsx"
    )

    operatividad = pd.read_excel(
        "data/REPORTE_OPERATIVIDAD.xlsx"
    )

    tahum = pd.read_excel(
        "data/REPORTE_TAHUM.xlsx"
    )

    return delitos, operatividad, tahum