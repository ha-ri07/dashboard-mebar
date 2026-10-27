import html
import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from utils.carga import cargar_datos


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Dashboard MEBAR",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent

AZUL = "#12345A"
AZUL_CLARO = "#EAF1F8"
DORADO = "#C5A45B"
FONDO = "#FFFFFF"
TEXTO = "#142B45"
VERDE = "#198754"
ROJO = "#B42332"


def estilizar_grafico(fig, altura_minima=390):
    """Aplica una presentación consistente, legible y de alto contraste a Plotly."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, Arial, sans-serif", size=14, color="#142B45"),
        title=dict(font=dict(size=18, color="#12345A"), x=0.01, xanchor="left"),
        legend=dict(font=dict(size=13, color="#142B45"), title_font=dict(size=13, color="#12345A"),
                    bgcolor="rgba(255,255,255,0.92)", bordercolor="#D7E1EC", borderwidth=1),
        hoverlabel=dict(bgcolor="#12345A", font=dict(color="#FFFFFF", size=14), bordercolor="#12345A"),
        margin=dict(l=24, r=24, t=42, b=30),
        height=max(int(fig.layout.height or 0), altura_minima),
    )
    fig.update_xaxes(
        tickfont=dict(size=13, color="#263B53"),
        title_font=dict(size=14, color="#12345A"),
        gridcolor="#E7EDF4", zerolinecolor="#C9D5E2",
        showline=True, linecolor="#C9D5E2", automargin=True,
    )
    fig.update_yaxes(
        tickfont=dict(size=13, color="#263B53"),
        title_font=dict(size=14, color="#12345A"),
        gridcolor="#E7EDF4", zerolinecolor="#C9D5E2",
        showline=False, automargin=True,
    )
    # Los valores numéricos quedan visibles en barras y líneas, no solo en el hover.
    for tr in fig.data:
        if tr.type == "bar":
            tr.update(textposition="auto", textfont=dict(size=13, color="#142B45"), cliponaxis=False)
        elif tr.type == "scatter" and tr.mode and "lines" in tr.mode and tr.name != "Mapa":
            tr.update(line=dict(width=3), marker=dict(size=8))
    return fig


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', Arial, sans-serif;
        font-size: 15px;
    }}

    .stApp {{
        background: {FONDO};
        color: {TEXTO};
    }}

    /* ============================================================
       SIDEBAR: logo pegado a los bordes superior e izquierdo
       ============================================================ */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {AZUL} 0%, #0B223D 100%);
        padding-top: 0 !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}

    [data-testid="stSidebar"] img {{
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        border-top-left-radius: 0 !important;
        border-top-right-radius: 0 !important;
    }}

    [data-testid="stSidebar"] * {{
        color: #FFFFFF;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        background: rgba(255,255,255,0.06);
        border-radius: 9px;
        padding: 8px 10px;
        margin-bottom: 5px;
    }}

    h1, h2, h3 {{
        color: {AZUL};
        letter-spacing: -0.4px;
    }}

    .encabezado {{
        background: linear-gradient(115deg, {AZUL}, #1D4C78);
        padding: 25px 28px;
        border-radius: 17px;
        color: white;
        margin-bottom: 22px;
        border-bottom: 4px solid {DORADO};
        box-shadow: 0 6px 22px rgba(18,52,90,0.10);
    }}

    .encabezado h1 {{
        color: white;
        font-size: 28px;
        margin: 0;
        font-weight: 800;
    }}

    .encabezado p {{
        color: #E4EDF7;
        margin: 7px 0 0 0;
        font-size: 13px;
    }}

    .tarjeta {{
        background: white;
        padding: 19px 20px;
        border-radius: 14px;
        border: 1px solid #E3EAF2;
        box-shadow: 0 3px 12px rgba(27,53,82,0.04);
        min-height: 118px;
    }}

    .tarjeta .etiqueta {{
        color: #34465C;
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .tarjeta .valor {{
        color: {AZUL};
        font-size: 34px;
        font-weight: 800;
        margin-top: 8px;
        line-height: 1.2;
        overflow-wrap: anywhere;
    }}

    .tarjeta .nota {{
        color: #34465C;
        font-size: 13px;
        margin-top: 7px;
    }}

    .seccion {{
        background: white;
        border: 1px solid #E3EAF2;
        border-left: 4px solid {DORADO};
        border-radius: 10px;
        padding: 13px 16px;
        margin: 19px 0 13px 0;
        color: {AZUL};
        font-size: 18px;
        font-weight: 800;
    }}

    .perfil {{
        background: white;
        border: 1px solid #E1E8F0;
        border-radius: 15px;
        padding: 21px;
        margin-bottom: 14px;
    }}

    .perfil-nombre {{
        color: {AZUL};
        font-size: 20px;
        font-weight: 800;
        margin-bottom: 5px;
    }}

    .perfil-sub {{
        color: #64748B;
        font-size: 12px;
        margin-bottom: 13px;
    }}

    .dato {{
        color: #64748B;
        font-size: 11px;
        text-transform: uppercase;
        margin-top: 9px;
    }}

    .dato-valor {{
        color: {TEXTO};
        font-size: 13px;
        font-weight: 600;
        overflow-wrap: anywhere;
    }}

    .pie {{
        text-align: center;
        color: #7B8796;
        font-size: 11px;
        padding: 25px 0 8px 0;
    }}

    div[data-testid="stMetric"] {{
        background: white;
        border: 1px solid #E3EAF2;
        padding: 14px;
        border-radius: 12px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: #263B53;
        font-size: 14px;
    }}

    /* Paneles desplegables para los tres rankings */
    div[data-testid="stExpander"] {{
        background: #FFFFFF;
        border: 1px solid #DCE5EF;
        border-radius: 15px;
        margin: 12px 0;
        box-shadow: 0 4px 14px rgba(18,52,90,0.055);
        overflow: hidden;
        transition: border-color .2s ease, box-shadow .2s ease;
    }}

    div[data-testid="stExpander"]:hover {{
        border-color: #C5A45B;
        box-shadow: 0 7px 20px rgba(18,52,90,0.10);
    }}

    div[data-testid="stExpander"] details summary {{
        background: linear-gradient(100deg, #FFFFFF 0%, #F1F6FB 100%);
        padding: 16px 18px;
        color: #12345A;
        font-weight: 800;
        font-size: 14px;
    }}

    div[data-testid="stExpander"] details summary:hover {{
        color: #1D4C78;
        background: linear-gradient(100deg, #F8FAFD 0%, #EAF1F8 100%);
    }}

    div[data-testid="stExpander"] details[open] summary {{
        border-bottom: 1px solid #E3EAF2;
        background: linear-gradient(100deg, #EAF1F8 0%, #FFFFFF 100%);
    }}

    div[data-testid="stExpander"] details > div {{
        padding: 14px 16px 18px;
    }}

    .stButton button {{
        border-radius: 9px;
        font-weight: 600;
    }}

    hr {{
        border-color: #E2E8F0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def normalizar_id(valor):
    """Normaliza identificaciones para cruzar las tres fuentes."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.lower() in {"", "nan", "none", "nat"}:
        return ""

    # Corrige IDs numéricos leídos desde Excel como 123456.0
    if re.fullmatch(r"\d+\.0+", texto):
        texto = texto.split(".")[0]

    return re.sub(r"\s+", "", texto).upper()


def numero(valor):
    """Convierte valores numéricos de Excel a un número seguro."""
    if pd.isna(valor):
        return 0

    resultado = pd.to_numeric(valor, errors="coerce")
    return 0 if pd.isna(resultado) else float(resultado)


def suma_columna(df, columna):
    if columna not in df.columns:
        return 0
    return pd.to_numeric(df[columna], errors="coerce").fillna(0).sum()


def limpiar_dataframe(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def preparar_fecha(df):
    df = df.copy()
    if "FECHA_HECHO" in df.columns:
        df["FECHA_HECHO"] = pd.to_datetime(
            df["FECHA_HECHO"],
            errors="coerce",
            dayfirst=True,
        )
    else:
        df["FECHA_HECHO"] = pd.NaT
    return df


def preparar_identificacion(df, columna):
    df = df.copy()
    if columna in df.columns:
        df["_ID_CLAVE"] = df[columna].apply(normalizar_id)
    else:
        df["_ID_CLAVE"] = ""
    return df


def texto_columna(df, columna, defecto="No registrado"):
    if columna not in df.columns or df.empty:
        return defecto

    valores = df[columna].dropna()
    if valores.empty:
        return defecto

    return normalizar_texto(valores.iloc[0]) or defecto


def formatear_entero(valor):
    return f"{int(round(numero(valor))):,}".replace(",", ".")


def fecha_legible(fecha):
    if pd.isna(fecha):
        return "Fecha no disponible"
    return fecha.strftime("%d/%m/%Y")


def titulo_seccion(texto):
    st.markdown(
        f'<div class="seccion">{html.escape(texto)}</div>',
        unsafe_allow_html=True,
    )


def tarjeta(etiqueta, valor, nota=""):
    st.markdown(
        f"""
        <div class="tarjeta">
            <div class="etiqueta">{html.escape(str(etiqueta))}</div>
            <div class="valor">{html.escape(str(valor))}</div>
            <div class="nota">{html.escape(str(nota))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def encabezado(titulo, subtitulo):
    st.markdown(
        f"""
        <div class="encabezado">
            <h1>{html.escape(titulo)}</h1>
            <p>{html.escape(subtitulo)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_tabla(df, columnas, nombres=None):
    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    existentes = [c for c in columnas if c in df.columns]
    vista = df[existentes].copy()

    if nombres:
        vista = vista.rename(
            columns={k: v for k, v in nombres.items() if k in vista.columns}
        )

    st.dataframe(vista, use_container_width=True, hide_index=True)


# ============================================================
# HEADER PRINCIPAL CON RELOJ EN TIEMPO REAL
# ============================================================

import streamlit.components.v1 as components


def header_principal_con_reloj():
    """Muestra el header principal con reloj en tiempo real e indicador LIVE."""

    html_reloj = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            background: transparent;
            font-family: 'Inter', Arial, sans-serif;
            overflow: hidden;
        }
        .header-mebar-container {
            background: linear-gradient(135deg, #0a1628 0%, #1a3a5c 100%);
            border-radius: 12px;
            padding: 20px 28px;
            border: 2px solid #2a4a6c;
            border-bottom: 4px solid #C5A45B;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
            min-height: 120px;
            display: flex;
            align-items: center;
        }
        .header-mebar-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        }
        .header-mebar-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            width: 100%;
            flex-wrap: wrap;
        }
        .header-mebar-text {
            flex: 1;
            min-width: 300px;
        }
        .header-mebar-title {
            color: #ffffff;
            font-size: 32px;
            font-weight: 800;
            margin: 0 0 6px 0;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        .header-mebar-subtitle {
            color: #a0b3c8;
            font-size: 14px;
            margin: 0;
            font-weight: 400;
        }
        .header-mebar-clock {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
        }
        .live-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(25, 135, 84, 0.15);
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(25, 135, 84, 0.3);
        }
        .live-dot {
            width: 8px;
            height: 8px;
            background: #198754;
            border-radius: 50%;
            animation: pulse-live 2s ease-in-out infinite;
            box-shadow: 0 0 8px rgba(25, 135, 84, 0.8);
        }
        @keyframes pulse-live {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(0.95); }
        }
        .live-text {
            color: #198754;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        .clock-time {
            color: #ffffff;
            font-size: 28px;
            font-weight: 700;
            font-family: 'Courier New', monospace;
            letter-spacing: 1px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        .clock-date {
            color: #8b9fb3;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .date-dot {
            width: 6px;
            height: 6px;
            background: #198754;
            border-radius: 50%;
            display: inline-block;
        }
        @media (max-width: 768px) {
            .header-mebar-content {
                flex-direction: column;
                align-items: flex-start;
            }
            .header-mebar-clock {
                align-items: flex-start;
                width: 100%;
            }
            .header-mebar-title {
                font-size: 24px;
            }
            .clock-time {
                font-size: 24px;
            }
        }
    </style>
    </head>
    <body>
        <div class="header-mebar-container">
            <div class="header-mebar-content">
                <div class="header-mebar-text">
                    <h1 class="header-mebar-title">PANEL PRINCIPAL MEBAR</h1>
                    <p class="header-mebar-subtitle">Sistema de evaluacion y seguimiento al rendimiento Policial </p>
                </div>
                <div class="header-mebar-clock">
                    <div class="live-indicator">
                        <span class="live-dot"></span>
                        <span class="live-text">LIVE</span>
                    </div>
                    <div class="clock-time" id="clock-time">--:--:--</div>
                    <div class="clock-date">
                        <span class="date-dot"></span>
                        <span id="clock-date">FECHA: --/--/--</span>
                    </div>
                </div>
            </div>
        </div>
        <script>
            function updateClock() {
                const now = new Date();
                const timeStr = now.toLocaleTimeString('es-CO', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                });
                const dateStr = now.toLocaleDateString('es-CO', {
                    day: '2-digit',
                    month: '2-digit',
                    year: '2-digit'
                });
                const timeEl = document.getElementById('clock-time');
                const dateEl = document.getElementById('clock-date');
                if (timeEl) timeEl.textContent = timeStr;
                if (dateEl) dateEl.textContent = 'FECHA: ' + dateStr;
            }
            updateClock();
            setInterval(updateClock, 1000);
        </script>
    </body>
    </html>
    """

    components.html(html_reloj, height=140, scrolling=False)
# ============================================================
# CARGA Y PREPARACIÓN DE DATOS
# ============================================================

@st.cache_data(show_spinner="Cargando información de los reportes...")
def cargar_y_preparar():
    delitos, operatividad, tahum = cargar_datos()

    delitos = limpiar_dataframe(delitos)
    operatividad = limpiar_dataframe(operatividad)
    tahum = limpiar_dataframe(tahum)

    delitos = preparar_fecha(delitos)
    operatividad = preparar_fecha(operatividad)

    delitos = preparar_identificacion(delitos, "IDENTIFICACION")
    operatividad = preparar_identificacion(operatividad, "IDENTIFICACION")
    tahum = preparar_identificacion(tahum, "Identificacion")

    # Evitar que las columnas de identificación queden vacías
    # si algún archivo tiene una variación en el nombre.
    for df in (delitos, operatividad, tahum):
        if "_ID_CLAVE" not in df.columns:
            df["_ID_CLAVE"] = ""

    # Consolidar datos básicos de funcionarios desde TAHUM.
    funcionarios = []

    if not tahum.empty:
        for _, fila in tahum.iterrows():
            identificacion = fila.get("_ID_CLAVE", "")
            if not identificacion:
                continue

            funcionarios.append({
                "_ID_CLAVE": identificacion,
                "GRADO": normalizar_texto(fila.get("GR", "")),
                "NOMBRE_TAHUM": normalizar_texto(
                    fila.get("APELLIDOS Y NOMBRES", "")
                ),
                "TIEMPO_UNIDAD": fila.get("TIEMPO_UNIDAD", ""),
                "TIEMPO_CARGO": fila.get("TIEMPO_CARGO", ""),
            })

    if funcionarios:
        base_funcionarios = pd.DataFrame(funcionarios)
        base_funcionarios = base_funcionarios.drop_duplicates(
            subset=["_ID_CLAVE"], keep="first"
        )
    else:
        base_funcionarios = pd.DataFrame(
            columns=[
                "_ID_CLAVE", "GRADO", "NOMBRE_TAHUM",
                "TIEMPO_UNIDAD", "TIEMPO_CARGO",
            ]
        )

    # Obtener el universo de funcionarios a partir de las tres fuentes.
    registros_funcionarios = []

    for df, columna_nombre in [
        (delitos, "GR APELLIDOS Y NOMBRES POLICIA_1"),
        (operatividad, "GR APELLIDOS Y NOMBRES POLICIA_1"),
    ]:
        if columna_nombre not in df.columns:
            continue

        columnas = ["_ID_CLAVE", columna_nombre]
        if "ESTACION" in df.columns:
            columnas.append("ESTACION")

        for _, fila in df[columnas].iterrows():
            clave = fila.get("_ID_CLAVE", "")
            if not clave:
                continue

            registros_funcionarios.append({
                "_ID_CLAVE": clave,
                "NOMBRE_REPORTE": normalizar_texto(
                    fila.get(columna_nombre, "")
                ),
                "ESTACION": normalizar_texto(fila.get("ESTACION", "")),
            })

    if registros_funcionarios:
        base_reportes = pd.DataFrame(registros_funcionarios)
        base_reportes = base_reportes[
            base_reportes["_ID_CLAVE"] != ""
        ].copy()

        base_reportes = base_reportes.sort_values(
            "NOMBRE_REPORTE", na_position="last"
        )
        base_reportes = base_reportes.drop_duplicates(
            subset=["_ID_CLAVE"], keep="first"
        )
    else:
        base_reportes = pd.DataFrame(
            columns=["_ID_CLAVE", "NOMBRE_REPORTE", "ESTACION"]
        )

    # Incluir también funcionarios que existan únicamente en TAHUM.
    universo_ids = set(base_reportes.get("_ID_CLAVE", pd.Series(dtype=str)))
    universo_ids.update(base_funcionarios.get("_ID_CLAVE", pd.Series(dtype=str)))
    universo_ids.discard("")

    maestros = pd.DataFrame({"_ID_CLAVE": sorted(universo_ids)})

    if not base_reportes.empty:
        maestros = maestros.merge(
            base_reportes, on="_ID_CLAVE", how="left"
        )

    if not base_funcionarios.empty:
        maestros = maestros.merge(
            base_funcionarios, on="_ID_CLAVE", how="left"
        )

    if "NOMBRE_REPORTE" not in maestros:
        maestros["NOMBRE_REPORTE"] = ""

    if "NOMBRE_TAHUM" not in maestros:
        maestros["NOMBRE_TAHUM"] = ""

    if "ESTACION" not in maestros:
        maestros["ESTACION"] = ""

    if "GRADO" not in maestros:
        maestros["GRADO"] = ""

    if "TIEMPO_UNIDAD" not in maestros:
        maestros["TIEMPO_UNIDAD"] = ""

    if "TIEMPO_CARGO" not in maestros:
        maestros["TIEMPO_CARGO"] = ""

    maestros["NOMBRE"] = maestros["NOMBRE_TAHUM"].where(
        maestros["NOMBRE_TAHUM"].astype(str).str.strip() != "",
        maestros["NOMBRE_REPORTE"],
    )

    maestros["NOMBRE"] = maestros["NOMBRE"].fillna("").astype(str).str.strip()
    maestros["ESTACION"] = maestros["ESTACION"].fillna("").astype(str).str.strip()
    maestros["GRADO"] = maestros["GRADO"].fillna("").astype(str).str.strip()

    return delitos, operatividad, tahum, maestros


try:
    delitos, operatividad, tahum, maestros = cargar_y_preparar()
except Exception as error:
    st.error("No fue posible cargar los archivos de información.")
    st.exception(error)
    st.stop()


# ============================================================
# MENÚ LATERAL Y FILTROS
# ============================================================

with st.sidebar:
    # Logo y encabezado institucional
    ruta_logo = BASE_DIR / "assets" / "LOGO_OFICINA.png"

    if ruta_logo.exists():
        st.image(str(ruta_logo), width="stretch")

    st.markdown(
        """
        <div style="
            text-align:left;
            padding:16px 18px;
            margin-top:12px;
            font-family:'Inter', Arial, sans-serif;
            border-left:3px solid #C5A45B;
            background:rgba(255,255,255,0.04);
            border-radius:0 8px 8px 0;
        ">
            <div style="
                font-size:12px;
                font-weight:600;
                letter-spacing:1.5px;
                color:#FFFFFF;
                margin-bottom:8px;
                text-transform:uppercase;
            ">
                PANEL DE INFORMACIÓN
            </div>
            <div style="
                font-size:11px;
                font-weight:400;
                font-style:italic;
                line-height:1.6;
                color:#B8C9DC;
                letter-spacing:0.3px;
            ">
                Permite navegar entre módulos (Gestión Operativa, Registro Delictivo, Panel Principal) y filtrar o buscar información por periodos, estaciones, grados o funcionarios para actualizar el dashboard.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### NAVEGACIÓN")

    pantalla = st.radio(
        "Selecciona una pantalla",
        ["Panel principal", "Gestión Operativa", "Registro Delictivo"],  # ✅ Nombres nuevos
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### FILTROS GENERALES")

    # Las fechas se basan en la unión de ambos reportes.
    fechas = pd.concat(
        [delitos["FECHA_HECHO"], operatividad["FECHA_HECHO"]],
        ignore_index=True,
    ).dropna()

    if not fechas.empty:
        fecha_min = fechas.min().date()
        fecha_max = fechas.max().date()

        rango_fechas = st.date_input(
            "Periodo de consulta",
            value=(fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max,
            format="DD/MM/YYYY",
        )

        if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
            inicio, fin = rango_fechas
        else:
            inicio = rango_fechas
            fin = rango_fechas
    else:
        inicio = None
        fin = None
        st.warning("No se encontraron fechas válidas en los reportes.")

    estaciones = set()

    for df in (delitos, operatividad):
        if "ESTACION" in df.columns:
            estaciones.update(
                df["ESTACION"].dropna().astype(str).str.strip().tolist()
            )

    estaciones = sorted(x for x in estaciones if x and x.lower() != "nan")

    estaciones_sel = st.multiselect(
        "Estación",
        options=estaciones,
        default=[],
        placeholder="Todas las estaciones",
    )

    grados = sorted(
        x for x in maestros.get("GRADO", pd.Series(dtype=str))
        .dropna().astype(str).str.strip().unique()
        if x and x.lower() != "nan"
    )

    grados_sel = st.multiselect(
        "Grado",
        options=grados,
        default=[],
        placeholder="Todos los grados",
    )

    st.markdown("### BÚSQUEDA DE FUNCIONARIOS")
    cedula_busqueda = st.text_input(
        "Buscar por cédula",
        placeholder="Escribe el número de identificación",
        key="filtro_cedula",
    ).strip()
    nombre_busqueda = st.text_input(
        "Grados, nombres y apellidos",
        placeholder="Ej. SI Alexander Ruiz",
        key="filtro_nombre_funcionario",
    ).strip().casefold()

    st.markdown("---")
    st.caption("Los filtros se aplican a las pantallas y gráficos del dashboard.")
    st.caption("MEBAR · Análisis de información")


# Determinar funcionarios que coinciden con los filtros de búsqueda.
maestros_f = maestros.copy()

if estaciones_sel:
    maestros_f = maestros_f[maestros_f["ESTACION"].isin(estaciones_sel)]

if grados_sel:
    maestros_f = maestros_f[maestros_f["GRADO"].isin(grados_sel)]

if cedula_busqueda:
    maestros_f = maestros_f[
        maestros_f["_ID_CLAVE"].astype(str).str.contains(
            re.escape(normalizar_id(cedula_busqueda)), na=False
        )
    ]

if nombre_busqueda:
    texto_funcionario = (
        maestros_f["GRADO"].fillna("").astype(str) + " "
        + maestros_f["NOMBRE"].fillna("").astype(str)
    ).str.casefold()
    maestros_f = maestros_f[
        texto_funcionario.str.contains(re.escape(nombre_busqueda), na=False)
    ]

ids_visibles = set(maestros_f["_ID_CLAVE"].astype(str))

def aplicar_filtros(df):
    resultado = df.copy()

    if inicio is not None and fin is not None:
        fechas_locales = resultado["FECHA_HECHO"]
        resultado = resultado[
            fechas_locales.isna()
            | (
                (fechas_locales.dt.date >= inicio)
                & (fechas_locales.dt.date <= fin)
            )
        ]

    if estaciones_sel and "ESTACION" in resultado.columns:
        resultado = resultado[
            resultado["ESTACION"].astype(str).str.strip().isin(estaciones_sel)
        ]

    # Aplicar búsqueda por cédula/nombre/grado a los reportes que tienen ID.
    if cedula_busqueda or nombre_busqueda or grados_sel:
        resultado = resultado[resultado["_ID_CLAVE"].astype(str).isin(ids_visibles)]

    return resultado


delitos_f = aplicar_filtros(delitos)
operatividad_f = aplicar_filtros(operatividad)


# ============================================================
# INDICADORES Y AGREGADOS POR FUNCIONARIO
# ============================================================

def agregar_funcionarios(base, df_delitos, df_operatividad):
    base = base.copy()

    if base.empty:
        return base

    if not df_delitos.empty:
        casos = (
            df_delitos.groupby("_ID_CLAVE", dropna=False)
            .agg(
                CASOS=("CANTIDAD CASOS", "sum")
                if "CANTIDAD CASOS" in df_delitos.columns
                else ("_ID_CLAVE", "size"),
                VICTIMAS=("CANTIDAD VICTIMA", "sum")
                if "CANTIDAD VICTIMA" in df_delitos.columns
                else ("_ID_CLAVE", "size"),
            )
            .reset_index()
        )
    else:
        casos = pd.DataFrame(
            columns=["_ID_CLAVE", "CASOS", "VICTIMAS"]
        )

    if not df_operatividad.empty:
        df_operatividad = df_operatividad.copy()
        if "TOTAL TIPO DE CAPTURA" in df_operatividad.columns:
            df_operatividad["TOTAL TIPO DE CAPTURA"] = pd.to_numeric(
                df_operatividad["TOTAL TIPO DE CAPTURA"], errors="coerce"
            ).fillna(0)

        ops_agregadas = (
            df_operatividad.groupby("_ID_CLAVE", dropna=False)
            .agg(
                TOTAL_TIPO_CAPTURA=("TOTAL TIPO DE CAPTURA", "sum")
                if "TOTAL TIPO DE CAPTURA" in df_operatividad.columns
                else ("_ID_CLAVE", lambda serie: 0),
                ACTIVIDADES=("TOTAL ACTIVIDAD OPERATIVA", "sum")
                if "TOTAL ACTIVIDAD OPERATIVA" in df_operatividad.columns
                else ("_ID_CLAVE", "size"),
            )
            .reset_index()
        )
    else:
        ops_agregadas = pd.DataFrame(
            columns=["_ID_CLAVE", "TOTAL_TIPO_CAPTURA", "ACTIVIDADES"]
        )

    base = base.drop(
        columns=["CASOS", "VICTIMAS", "CAPTURAS", "TOTAL_TIPO_CAPTURA", "ACTIVIDADES"],
        errors="ignore",
    )

    base = base.merge(casos, on="_ID_CLAVE", how="left")
    base = base.merge(ops_agregadas, on="_ID_CLAVE", how="left")

    for columna in ["CASOS", "VICTIMAS", "TOTAL_TIPO_CAPTURA", "ACTIVIDADES"]:
        base[columna] = pd.to_numeric(
            base.get(columna, 0), errors="coerce"
        )
        base[columna] = base[columna].fillna(0)

    return base


ranking = agregar_funcionarios(
    maestros_f,
    delitos_f,
    operatividad_f,
)


def perfil_funcionario(id_clave):
    registro = maestros[maestros["_ID_CLAVE"] == id_clave]
    if registro.empty:
        return None

    return registro.iloc[0]


def obtener_ultimo_registro(df, id_clave):
    """Obtiene el registro más reciente de un funcionario según FECHA_HECHO."""
    if "_ID_CLAVE" not in df.columns or "FECHA_HECHO" not in df.columns:
        return None

    registros = df[df["_ID_CLAVE"] == id_clave].copy()
    registros = registros.dropna(subset=["FECHA_HECHO"])

    if registros.empty:
        return None

    return registros.sort_values("FECHA_HECHO", ascending=False).iloc[0]


def obtener_tipos_captura(id_clave):
    """Resume los tipos de captura asociados al funcionario."""
    registros = operatividad_f[
        operatividad_f["_ID_CLAVE"] == id_clave
    ].copy()

    if registros.empty or "TIPO DE CAPTURA" not in registros.columns:
        return "Sin tipos registrados"

    if "TOTAL TIPO DE CAPTURA" in registros.columns:
        registros["TOTAL TIPO DE CAPTURA"] = pd.to_numeric(
            registros["TOTAL TIPO DE CAPTURA"], errors="coerce"
        ).fillna(0)
        resumen = (
            registros.groupby("TIPO DE CAPTURA")["TOTAL TIPO DE CAPTURA"]
            .sum()
            .sort_values(ascending=False)
        )
    else:
        resumen = registros["TIPO DE CAPTURA"].value_counts()

    resumen = resumen[resumen.index.notna()]
    resumen = resumen[resumen.index.astype(str).str.strip() != ""]

    if resumen.empty:
        return "Sin tipos registrados"

    return " · ".join(
        f"{nombre}: {formatear_entero(total)}"
        for nombre, total in resumen.head(2).items()
    )


def tarjeta_funcionario(fila, metrica, categoria, posicion):
    """Tarjeta compacta con acceso a la ficha completa del funcionario."""
    id_clave = str(fila["_ID_CLAVE"])
    nombre = str(fila.get("NOMBRE", "") or "Nombre no registrado")
    grado = str(fila.get("GRADO", "") or "Grado no registrado")
    estacion = str(fila.get("ESTACION", "") or "Estación no registrada")

    ultimo_delito = obtener_ultimo_registro(delitos_f, id_clave)
    ultimo_operativo = obtener_ultimo_registro(operatividad_f, id_clave)

    if categoria == "capturas":
        fecha_ultimo = (
            fecha_legible(ultimo_operativo["FECHA_HECHO"])
            if ultimo_operativo is not None else "Sin fecha disponible"
        )
        etiqueta_fecha = "Último registro operativo"
        detalle = obtener_tipos_captura(id_clave)

    elif categoria == "homicidios":
        homicidios_funcionario = delitos_homicidios[
            delitos_homicidios["_ID_CLAVE"] == id_clave
        ]
        if not homicidios_funcionario.empty:
            fecha_homicidio = homicidios_funcionario["FECHA_HECHO"].max()
            fecha_ultimo = fecha_legible(fecha_homicidio)
        else:
            fecha_ultimo = "Sin fecha disponible"

        etiqueta_fecha = "Último homicidio registrado"
        detalle = "Casos de homicidio asociados"

    else:
        fecha_ultimo = (
            fecha_legible(ultimo_delito["FECHA_HECHO"])
            if ultimo_delito is not None else "Sin fecha disponible"
        )
        etiqueta_fecha = "Último delito registrado"
        detalle = "Casos delictivos asociados"

    cantidad = formatear_entero(fila.get(metrica, 0))

    registro_referencia = (
        ultimo_operativo if categoria == "capturas" else ultimo_delito
    )
    if registro_referencia is not None:
        estacion_actual = normalizar_texto(
            registro_referencia.get("ESTACION", "")
        )
        if estacion_actual:
            estacion = estacion_actual

    color_borde = "#9F1239" if categoria in ("delitos", "homicidios") else "#C5A45B"
    color_icono = "#FCE7EF" if categoria in ("delitos", "homicidios") else "#EAF1F8"
    color_texto = "#76112F" if categoria in ("delitos", "homicidios") else "#12345A"
    fondo_metrica = "#FFF1F5" if categoria in ("delitos", "homicidios") else "#F4F7FB"
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF;border:1px solid #E8D4DB;border-radius:15px;
            padding:17px;min-height:220px;
            box-shadow:0 4px 14px rgba(18,52,90,0.06);
            border-top:4px solid {color_borde};
        ">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="
                    min-width:48px;width:48px;height:48px;
                    display:flex;align-items:center;justify-content:center;
                    background:{color_icono};border-radius:13px;font-size:27px;
                ">👮</div>
                <div style="min-width:0;">
                    <div style="color:#9A7937;font-size:10px;
                        font-weight:800;letter-spacing:1px;">
                        PUESTO #{posicion}
                    </div>
                    <div style="color:{color_texto};font-size:15px;font-weight:800;
                        line-height:1.35;overflow-wrap:anywhere;">
                        {html.escape(grado)} {html.escape(nombre)}
                    </div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;
                gap:10px;margin-top:16px;">
                <div>
                    <div style="font-size:10px;color:#64748B;">IDENTIFICACIÓN</div>
                    <div style="font-size:12px;color:#233247;font-weight:700;">
                        {html.escape(id_clave)}
                    </div>
                </div>
                <div>
                    <div style="font-size:10px;color:#64748B;">ESTACIÓN</div>
                    <div style="font-size:12px;color:#233247;font-weight:700;">
                        {html.escape(estacion)}
                    </div>
                </div>
            </div>
            <div style="background:{fondo_metrica};border-radius:10px;
                padding:12px;margin-top:13px;">
                <div style="font-size:11px;color:#64748B;">
                    {html.escape(detalle)}
                </div>
                <div style="font-size:27px;font-weight:800;color:{color_texto};
                    margin-top:2px;">
                    {html.escape(cantidad)}
                </div>
                <div style="font-size:11px;color:#334155;font-weight:600;
                    margin-top:5px;">
                    {html.escape(etiqueta_fecha)}: {html.escape(fecha_ultimo)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Enlace directo a la ficha, abierto en una pestaña nueva del navegador.
    url_ficha = f"?ficha={id_clave}"
    st.markdown(
        f"""
        <a href="{html.escape(url_ficha, quote=True)}" target="_blank"
           rel="noopener noreferrer"
           style="display:block;text-align:center;text-decoration:none;
                  background:#12345A;color:#FFFFFF;font-weight:700;
                  padding:11px 14px;border-radius:9px;margin-top:10px;">
            Ver ficha completa ↗
        </a>
        """,
        unsafe_allow_html=True,
    )


def mostrar_ranking_tarjetas(df, metrica, categoria, titulo_vacio):
    """Presenta hasta diez funcionarios en tarjetas, en dos columnas."""
    if df.empty or metrica not in df.columns or df[metrica].sum() <= 0:
        st.info(titulo_vacio)
        return

    columnas_orden = [metrica]
    if "NOMBRE" in df.columns:
        columnas_orden.append("NOMBRE")

    top = (
        df.sort_values(
            columnas_orden,
            ascending=[False] + ([True] if len(columnas_orden) > 1 else []),
        )
        .head(10)
        .reset_index(drop=True)
    )

    izquierda, derecha = st.columns(2, gap="medium")

    for indice, (_, fila) in enumerate(top.iterrows()):
        columna = izquierda if indice % 2 == 0 else derecha
        with columna:
            tarjeta_funcionario(
                fila=fila,
                metrica=metrica,
                categoria=categoria,
                posicion=indice + 1,
            )
            st.write("")


def mostrar_perfil(id_clave):
    """Muestra la ficha individual y sus registros operativos y delictivos."""
    funcionario = perfil_funcionario(id_clave)

    if funcionario is None:
        st.warning("No fue posible localizar la ficha del funcionario.")
        return

    nombre = str(funcionario.get("NOMBRE", "") or "Nombre no registrado")
    grado = str(funcionario.get("GRADO", "") or "Grado no registrado")
    estacion = str(funcionario.get("ESTACION", "") or "Estación no registrada")

    st.markdown(
        f"""
        <div class="perfil">
            <div class="perfil-nombre">👮 {html.escape(grado)} {html.escape(nombre)}</div>
            <div class="perfil-sub">
                Identificación: {html.escape(str(id_clave))}
                · Estación: {html.escape(estacion)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    delitos_persona = delitos_f[delitos_f["_ID_CLAVE"] == id_clave].copy()
    ops_persona = operatividad_f[operatividad_f["_ID_CLAVE"] == id_clave].copy()

    with c1:
        tarjeta("Casos delictivos", formatear_entero(
            suma_columna(delitos_persona, "CANTIDAD CASOS")
        ))
    with c2:
        tarjeta("Víctimas", formatear_entero(
            suma_columna(delitos_persona, "CANTIDAD VICTIMA")
        ))
    with c3:
        tarjeta("Total tipo de captura", formatear_entero(
            suma_columna(ops_persona, "TOTAL TIPO DE CAPTURA")
        ))
    with c4:
        tarjeta("Actividad operativa", formatear_entero(
            suma_columna(ops_persona, "TOTAL ACTIVIDAD OPERATIVA")
        ))

    titulo_seccion("Registros de operatividad del funcionario")
    mostrar_tabla(
        ops_persona.sort_values(
            "FECHA_HECHO", ascending=False, na_position="last"
        ) if "FECHA_HECHO" in ops_persona.columns else ops_persona,
        [
            "FECHA_HECHO", "BOLETIN", "ESTACION", "CAI",
            "TIPO DE CAPTURA", "TOTAL TIPO DE CAPTURA",
            "TOTAL PERSONAS CAPTURADAS", "DELITO DE CAPTURA",
            "ACTIVIDAD OPERATIVA", "TOTAL ACTIVIDAD OPERATIVA",
        ],
        {
            "FECHA_HECHO": "Fecha",
            "BOLETIN": "Boletín",
            "ESTACION": "Estación",
            "CAI": "CAI",
            "TIPO DE CAPTURA": "Tipo de captura",
            "TOTAL TIPO DE CAPTURA": "Total tipo de captura",
            "TOTAL PERSONAS CAPTURADAS": "Personas capturadas",
            "DELITO DE CAPTURA": "Delito de captura",
            "ACTIVIDAD OPERATIVA": "Actividad operativa",
            "TOTAL ACTIVIDAD OPERATIVA": "Total actividad",
        },
    )

    titulo_seccion("Registros delictivos del funcionario")
    mostrar_tabla(
        delitos_persona.sort_values(
            "FECHA_HECHO", ascending=False, na_position="last"
        ) if "FECHA_HECHO" in delitos_persona.columns else delitos_persona,
        [
            "FECHA_HECHO", "BOLETIN", "MUNICIPIO", "DISTRITO",
            "ESTACION", "CAI", "CUADRANTE", "DELITO",
            "CANTIDAD CASOS", "CANTIDAD VICTIMA",
        ],
        {
            "FECHA_HECHO": "Fecha",
            "BOLETIN": "Boletín",
            "MUNICIPIO": "Municipio",
            "DISTRITO": "Distrito",
            "ESTACION": "Estación",
            "CAI": "CAI",
            "CUADRANTE": "Cuadrante",
            "DELITO": "Delito",
            "CANTIDAD CASOS": "Casos",
            "CANTIDAD VICTIMA": "Víctimas",
        },
    )


def selector_funcionario():
    if ranking.empty:
        st.info("No hay funcionarios que coincidan con los filtros.")
        return

    opciones = {}
    for _, fila in ranking.iterrows():
        clave = fila["_ID_CLAVE"]
        nombre = fila.get("NOMBRE", "") or "Nombre no registrado"
        grado = fila.get("GRADO", "") or ""
        estacion = fila.get("ESTACION", "") or "Estación no registrada"
        etiqueta = f"{grado} {nombre} · {estacion} · ID {clave}".strip()
        opciones[etiqueta] = clave

    etiqueta_seleccionada = st.selectbox(
        "Selecciona un funcionario para consultar su ficha",
        options=list(opciones.keys()),
        index=None,
        placeholder="Buscar por nombre, estación o identificación...",
    )

    if etiqueta_seleccionada:
        mostrar_perfil(opciones[etiqueta_seleccionada])


def mostrar_ficha_seleccionada():
    """Muestra la ficha completa seleccionada desde cualquier pantalla."""
    id_seleccionado = st.session_state.get("funcionario_seleccionado")
    if not id_seleccionado:
        return

    st.markdown("---")
    titulo_seccion("FICHA INTEGRAL DEL FUNCIONARIO")
    funcionario = perfil_funcionario(id_seleccionado)

    if funcionario is None:
        st.warning("No fue posible localizar la ficha del funcionario seleccionado.")
        if st.button("Cerrar ficha", key="cerrar_ficha_no_encontrada"):
            st.session_state.pop("funcionario_seleccionado", None)
            st.session_state.pop("origen_ficha", None)
            st.rerun()
        return

    nombre = (
        str(funcionario.get("GRADO", "") or "") + " " +
        str(funcionario.get("NOMBRE", "") or "")
    ).strip()
    st.markdown(f"### 👮 {html.escape(nombre)}")
    st.caption(
        "Consulta consolidada de todos los registros operativos y delictivos "
        "del funcionario, dentro del periodo y filtros seleccionados."
    )

    if st.button("✕ Cerrar ficha completa", key="cerrar_ficha_compartida"):
        st.session_state.pop("funcionario_seleccionado", None)
        st.session_state.pop("origen_ficha", None)
        st.rerun()

    mostrar_perfil(str(id_seleccionado))


# ============================================================
# VISTA INDEPENDIENTE DE FICHA (se abre en una pestaña nueva)
# ============================================================

id_ficha_url = st.query_params.get("ficha")
if id_ficha_url:
    st.markdown(
        "<div style='padding:8px 0 14px;border-bottom:2px solid #C5A45B;'>"
        "<div style='font-size:13px;font-weight:800;letter-spacing:1px;color:#C5A45B;'>"
        "POLICÍA NACIONAL · MEBAR</div></div>",
        unsafe_allow_html=True,
    )
    st.title("Ficha completa del funcionario")
    st.caption("Vista independiente · Registros de operatividad y gestión delictiva")
    if st.button("← Volver al dashboard"):
        st.markdown("<script>window.close();</script>", unsafe_allow_html=True)
        st.info("Puedes cerrar esta pestaña para regresar al dashboard.")
    mostrar_perfil(str(id_ficha_url))
    st.stop()


# ============================================================
# PANTALLA 1: PANEL PRINCIPAL
# ============================================================


if pantalla == "Panel principal":
    # Header principal con reloj en tiempo real e indicador LIVE
    header_principal_con_reloj()

    # Indicadores generales del periodo seleccionado
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tarjeta(
            "Casos delictivos",
            formatear_entero(suma_columna(delitos_f, "CANTIDAD CASOS")),
            "Total del periodo filtrado",
        )

    with c2:
        tarjeta(
            "Víctimas registradas",
            formatear_entero(suma_columna(delitos_f, "CANTIDAD VICTIMA")),
            "Según el reporte delictivo",
        )

    with c3:
        tarjeta(
            "Total tipo de captura",
            formatear_entero(
                suma_columna(operatividad_f, "TOTAL TIPO DE CAPTURA")
            ),
            "Suma de la columna TOTAL TIPO DE CAPTURA",
        )

    with c4:
        tarjeta(
            "Funcionarios identificados",
            formatear_entero(ranking["_ID_CLAVE"].nunique()),
            "Con identificación disponible",
        )

    # --------------------------------------------------------
    # PREPARAR RANKING DE HOMICIDIOS
    # --------------------------------------------------------

    if "DELITO" in delitos_f.columns:
        delitos_homicidios = delitos_f[
            delitos_f["DELITO"]
            .fillna("")
            .astype(str)
            .str.contains(r"\bhomicidio\b", case=False, regex=True)
        ].copy()
    else:
        delitos_homicidios = delitos_f.iloc[0:0].copy()

    ranking_homicidios = agregar_funcionarios(
        maestros_f,
        delitos_homicidios,
        operatividad_f.iloc[0:0].copy(),
    )

    # --------------------------------------------------------
    # RANKINGS EN TARJETAS INTERACTIVAS
    # --------------------------------------------------------
    st.markdown("""
    <style>
    .ranking-intro { margin: 8px 0 12px; color:#526174; font-size:14px; }

    /* Descripciones inferiores: tipografía elegante con degradado animado. */
    .ranking-card-description {
        box-sizing:border-box; min-height:154px; margin:9px 0 8px; padding:14px 15px;
        border:1px solid #DCE5EF; border-radius:14px;
        background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(240,245,250,.96));
        box-shadow:0 5px 16px rgba(20,42,68,.06);
        font-size:13px; line-height:1.65; color:#435268;
        transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease;
    }
    .ranking-card-description:hover { transform:translateY(-2px); box-shadow:0 9px 22px rgba(20,42,68,.11); }
    .ranking-card-description .description-label {
        display:block; margin-bottom:6px; font-size:11px; font-weight:900;
        letter-spacing:1.35px; text-transform:uppercase;
        background:linear-gradient(90deg,#12345A,#3D79A8,#12345A,#C49A55);
        background-size:240% auto; color:#12345A;
        -webkit-background-clip:text; background-clip:text;
        -webkit-text-fill-color:transparent; animation:rankingGradientFlow 5s linear infinite;
    }
    .ranking-card-description.carmesi {
        border-color:#E5CDD2;
        background:linear-gradient(145deg,#FFFCFC 0%,#F8EFF1 100%);
    }
    .ranking-card-description.carmesi .description-label {
        background:linear-gradient(90deg,#651525,#B13A52,#8A1C34,#C49A55,#651525);
        background-size:260% auto; -webkit-background-clip:text; background-clip:text;
        -webkit-text-fill-color:transparent; animation:rankingGradientFlow 4.6s linear infinite;
    }
    @keyframes rankingGradientFlow { 0% {background-position:0% center;} 100% {background-position:260% center;} }
    @media (prefers-reduced-motion: reduce) {
        .ranking-card-description .description-label { animation:none; }
        .ranking-card-description, .ranking-card-description:hover { transition:none; transform:none; }
    }

    /* Las tarjetas mantienen su aspecto; cada una tiene su propia identidad. */
    div.st-key-ranking_card_capturas button {
        min-height:112px; width:100%; white-space:pre-wrap; text-align:left;
        border-radius:18px; border:1px solid #D6E2EF;
        background:linear-gradient(145deg,#FFFFFF 0%,#EEF4FA 100%);
        color:#12345A; font-size:15px; font-weight:800; line-height:1.45;
        padding:18px 16px; box-shadow:0 6px 18px rgba(18,52,90,.08);
        transition:all .2s ease;
    }
    div.st-key-ranking_card_capturas button:hover {
        border-color:#12345A; transform:translateY(-3px);
        box-shadow:0 12px 24px rgba(18,52,90,.15);
    }

    /* Carmesí profundo y elegante: solo para las tarjetas 02 y 03. */
    div.st-key-ranking_card_delitos button,
    div.st-key-ranking_card_homicidios button {
        min-height:112px; width:100%; white-space:pre-wrap; text-align:left;
        border-radius:18px; border:1px solid #6E1727;
        background:linear-gradient(135deg,#651525 0%,#851D32 58%,#3D101B 100%);
        color:#FFFFFF; font-size:15px; font-weight:800; line-height:1.45;
        padding:18px 16px; box-shadow:0 7px 20px rgba(72,12,28,.19);
        transition:all .2s ease;
    }
    div.st-key-ranking_card_delitos button:hover,
    div.st-key-ranking_card_homicidios button:hover {
        border-color:#B88A50; transform:translateY(-3px);
        box-shadow:0 13px 27px rgba(72,12,28,.27);
        background:linear-gradient(135deg,#7A192C 0%,#9A2439 58%,#4A111F 100%);
        color:#FFFFFF;
    }

    .ranking-panel-carmesi {
        border:1px solid #D9B7BE; border-left:5px solid #7A192C;
        background:linear-gradient(135deg,#F7F0F1 0%,#FFFFFF 78%);
        border-radius:16px; padding:17px 18px 8px; margin:8px 0 18px;
    }
    .ranking-panel-azul {
        border:1px solid #D6E2EF; border-left:5px solid #12345A;
        background:linear-gradient(135deg,#F1F5FA 0%,#FFFFFF 78%);
        border-radius:16px; padding:17px 18px 8px; margin:8px 0 18px;
    }
    .ranking-panel-title {font-size:19px;font-weight:800;color:#651525;margin:0 0 5px;}
    .ranking-panel-sub {font-size:13px;color:#4D2630;margin:0 0 12px;}
    </style>
    <div class="ranking-intro">Selecciona una tarjeta para desplegar su ranking. Pulsa de nuevo la misma tarjeta para recoger la información.</div>
    """, unsafe_allow_html=True)

    if "ranking_principal_activo" not in st.session_state:
        st.session_state["ranking_principal_activo"] = None

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        if st.button("  01 · TOP 10\nFuncionarios por total de tipo de captura", key="ranking_card_capturas", use_container_width=True):
            st.session_state["ranking_principal_activo"] = None if st.session_state["ranking_principal_activo"] == "capturas" else "capturas"
        st.markdown("""
        <div class="ranking-card-description">
          <span class="description-label">¿Qué encontrará en esta opción?</span>
          Visualice el listado del personal policial destacado por el total de procedimientos de captura realizados. Esta métrica permite reconocer a los funcionarios con mayor aporte a la operatividad en calle, tanto en capturas en flagrancia como por orden judicial.
        </div>
        """, unsafe_allow_html=True)
    with r2:
        if st.button("02 · TOP 10\nFUNCIONARIOS CON MÁS DELITOS", key="ranking_card_delitos", use_container_width=True):
            st.session_state["ranking_principal_activo"] = None if st.session_state["ranking_principal_activo"] == "delitos" else "delitos"
        st.markdown("""
        <div class="ranking-card-description carmesi">
          <span class="description-label">¿Qué encontrará en esta opción?</span>
          Consulte el Top 10 de funcionarios asociados con el mayor número de registros de hechos delictivos reportados. Esta vista facilita el análisis de los casos registrados y el seguimiento de la gestión de incidentes en las estaciones y jurisdicciones correspondientes.
        </div>
        """, unsafe_allow_html=True)
    with r3:
        if st.button("03 · TOP 10\nFUNCIONARIOS CON MÁS HOMICIDIOS", key="ranking_card_homicidios", use_container_width=True):
            st.session_state["ranking_principal_activo"] = None if st.session_state["ranking_principal_activo"] == "homicidios" else "homicidios"
        st.markdown("""
        <div class="ranking-card-description carmesi">
          <span class="description-label">¿Qué encontrará en esta opción?</span>
          Identifique a los funcionarios vinculados con el mayor número de registros de homicidio. Esta herramienta apoya el análisis de los delitos contra la vida, permite reconocer concentraciones de casos y facilita la revisión de la información según los filtros activos.
        </div>
        """, unsafe_allow_html=True)

    ranking_activo = st.session_state["ranking_principal_activo"]
    if ranking_activo == "capturas":
        st.markdown("""
        <div class="ranking-panel-azul">
          <div style="font-size:19px;font-weight:800;color:#12345A;">01 · TOP 10 FUNCIONARIOS POR TOTAL DE TIPO DE CAPTURA</div>
          <div style="font-size:13px;color:#526174;margin-top:5px;">Ordenado exclusivamente por la suma de TOTAL TIPO DE CAPTURA del reporte de operatividad.</div>
        </div>
        """, unsafe_allow_html=True)
        mostrar_ranking_tarjetas(
            ranking, "TOTAL_TIPO_CAPTURA", "capturas",
            "No se encontraron valores en TOTAL TIPO DE CAPTURA para el periodo y los filtros seleccionados.",
        )
    elif ranking_activo == "delitos":
        st.markdown("""
        <div class="ranking-panel-carmesi">
          <div class="ranking-panel-title">02 · TOP 10 FUNCIONARIOS CON MÁS DELITOS</div>
          <div class="ranking-panel-sub">Casos delictivos reportados por funcionario, según filtros activos.</div>
        </div>
        """, unsafe_allow_html=True)
        mostrar_ranking_tarjetas(
            ranking, "CASOS", "delitos",
            "No se encontraron casos delictivos para el periodo y los filtros seleccionados.",
        )
    elif ranking_activo == "homicidios":
        st.markdown("""
        <div class="ranking-panel-carmesi">
          <div class="ranking-panel-title">03 · TOP 10 FUNCIONARIOS CON MÁS HOMICIDIOS</div>
          <div class="ranking-panel-sub">Registros cuyo campo DELITO contiene la palabra homicidio.</div>
        </div>
        """, unsafe_allow_html=True)
        mostrar_ranking_tarjetas(
            ranking_homicidios, "CASOS", "homicidios",
            "No se encontraron registros de homicidio para los filtros seleccionados.",
        )

    mostrar_ficha_seleccionada()

# PANTALLA 2: OPERATIVIDAD
# ============================================================

elif pantalla == "Gestión Operativa":
    encabezado(
        "GESTIÓN OPERATIVA",
        "Panel interactivo de capturas, cuadrantes, funcionarios, estaciones y actividad operativa",
    )

    ops = operatividad_f.copy()
    if not ops.empty:
        for col in [
            "TOTAL TIPO DE CAPTURA", "TOTAL PERSONAS CAPTURADAS",
            "TOTAL DELITO DE CAPTURA", "TOTAL ACTIVIDAD OPERATIVA",
        ]:
            if col in ops.columns:
                ops[col] = pd.to_numeric(ops[col], errors="coerce").fillna(0)

    # --------------------------------------------------------
    # TABLA PRINCIPAL INTERACTIVA DE FUNCIONARIOS
    # La tabla se construye antes de aplicar la selección para que
    # siempre permita elegir a otro funcionario.
    # --------------------------------------------------------
    titulo_seccion("Funcionarios · Capturas por modalidad")
    st.markdown("""<style>
        /* ============================================================
           TABLA DE FUNCIONARIOS - DISEÑO ENTERPRISE DE CLASE MUNDIAL
           ============================================================ */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Contenedor estético general con profundidad y sombra flotante */
        div[data-testid="stDataFrame"] {
            font-family: 'Inter', sans-serif !important;
            border: 1px solid rgba(226, 232, 240, 0.9) !important;
            border-radius: 20px !important;
            overflow: hidden !important;
            background: #ffffff !important;
            box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.07), 
                        0 0 0 1px rgba(197, 164, 91, 0.25) !important;
            padding: 6px !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        div[data-testid="stDataFrame"]:hover {
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.12), 
                        0 0 0 2px rgba(197, 164, 91, 0.45) !important;
            transform: translateY(-2px);
        }

        /* Estructura del grid interno */
        div[data-testid="stDataFrame"] [role="grid"] {
            font-size: 13.5px !important;
            color: #1e293b !important;
            border: 0 !important;
            outline: none !important;
        }

        /* Encabezado Ejecutivo (Estilo Deep Navy & Gold Accent) */
        div[data-testid="stDataFrame"] [role="columnheader"] {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 11.5px !important;
            letter-spacing: 0.9px !important;
            text-transform: uppercase !important;
            border-bottom: 3px solid #C5A45B !important;
            padding: 16px 14px !important;
            position: relative;
        }

        div[data-testid="stDataFrame"] [role="columnheader"] * {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* Efecto de brillo de luz superior en el encabezado */
        div[data-testid="stDataFrame"] [role="columnheader"]::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        }

        /* Celdas del cuerpo con diseño ultra limpio */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            color: #334155 !important;
            font-size: 13.5px !important;
            border-bottom: 1px solid #f1f5f9 !important;
            background: #ffffff !important;
            padding: 14px 14px !important;
            transition: all 0.2s ease;
        }

        /* Filas con efecto cebra moderno (sutilísimo) */
        div[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] {
            background: #f8fafc !important;
        }

        /* Efecto Dinámico Hover: Iluminación de fila de alta calidad */
        div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
            background: linear-gradient(90deg, #eff6ff 0%, #f0fdf4 100%) !important;
            color: #0f172a !important;
            border-bottom-color: #cbd5e1 !important;
        }

        /* Fila seleccionada con indicador elegante */
        div[data-testid="stDataFrame"] [role="row"]:focus-within [role="gridcell"],
        div[data-testid="stDataFrame"] [role="gridcell"]:focus {
            background: #dbeafe !important;
            outline: 2px solid #C5A45B !important;
            outline-offset: -2px !important;
            color: #1e3a8a !important;
            font-weight: 600 !important;
        }

        /* Alineación y estilo sofisticado para columnas numéricas */
        div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(4),
        div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(5),
        div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(6) {
            text-align: center !important;
            font-variant-numeric: tabular-nums !important;
            font-family: 'JetBrains Mono', 'Courier New', monospace !important;
            font-weight: 600 !important;
        }

        div[data-testid="stDataFrame"] [role="columnheader"]:nth-child(4),
        div[data-testid="stDataFrame"] [role="columnheader"]:nth-child(5),
        div[data-testid="stDataFrame"] [role="columnheader"]:nth-child(6) {
            text-align: center !important;
        }

        /* Celda estrella "Total tipo de captura" convertida en una insignia de impacto */
        div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(6) {
            color: #926d18 !important;
            font-weight: 800 !important;
            background: rgba(197, 164, 91, 0.12) !important;
            border-radius: 6px !important;
        }

        div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"]:nth-child(6) {
            background: rgba(197, 164, 91, 0.25) !important;
            color: #785307 !important;
        }

        /* Scrollbar minimalista y estilizado */
        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar {
            height: 6px;
            width: 6px;
        }

        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 10px;
        }

        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }

        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar-track {
            background: transparent;
        }

        /* Botón superior ("Mostrar todos") de categoría Premium */
        div.st-key-operatividad_mostrar_todos button {
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid #C5A45B !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            letter-spacing: 0.6px !important;
            padding: 12px 22px !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            box-shadow: 0 4px 15px rgba(30, 58, 138, 0.25) !important;
        }

        div.st-key-operatividad_mostrar_todos button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%) !important;
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 25px rgba(30, 58, 138, 0.4) !important;
            border-color: #e2b963 !important;
        }
    </style>""", unsafe_allow_html=True)

    st.markdown(
        '<div class="operatividad-tabla-ayuda">'
        '<strong>Seleccione un funcionario</strong> haciendo clic en su fila para filtrar '
        'los indicadores, gráficos y registros que aparecen debajo. '
        'Use <strong>Mostrar todos</strong> para retirar la selección.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="operatividad-tabla-ayuda">'
        '<strong>Seleccione un funcionario</strong> haciendo clic en su fila para filtrar '
        'los indicadores, gráficos y registros que aparecen debajo. '
        'Use <strong>Mostrar todos</strong> para retirar la selección.'
        '</div>',
        unsafe_allow_html=True,
    )

    columna_funcionario = "GR APELLIDOS Y NOMBRES POLICIA_1"
    if not ops.empty and columna_funcionario in ops.columns:
        base_func = ops.copy()
        base_func["FUNCIONARIO"] = (
            base_func[columna_funcionario].fillna("No registrado").astype(str).str.strip()
        )
        base_func["CEDULA"] = (
            base_func["IDENTIFICACION"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            if "IDENTIFICACION" in base_func.columns else ""
        )
        base_func["ESTACION_RESUMEN"] = (
            base_func["ESTACION"].fillna("No especificada").astype(str).str.strip()
            if "ESTACION" in base_func.columns else "No especificada"
        )
        base_func["TIPO_NORMALIZADO"] = (
            base_func["TIPO DE CAPTURA"].fillna("").astype(str).str.casefold()
            if "TIPO DE CAPTURA" in base_func.columns else ""
        )
        base_func["VALOR_CAPTURA"] = (
            pd.to_numeric(base_func["TOTAL TIPO DE CAPTURA"], errors="coerce").fillna(0)
            if "TOTAL TIPO DE CAPTURA" in base_func.columns else 0
        )
        base_func["FLAG"] = base_func["TIPO_NORMALIZADO"].str.contains("flagrancia", na=False)
        base_func["ORDEN"] = base_func["TIPO_NORMALIZADO"].str.contains("orden judicial", na=False)
        resumen = base_func.groupby(["FUNCIONARIO", "CEDULA", "ESTACION_RESUMEN"], dropna=False).agg(
            **{
                "Capturas flagrancia": ("VALOR_CAPTURA", lambda x: float(x[base_func.loc[x.index, "FLAG"]].sum())),
                "Capturas orden judicial": ("VALOR_CAPTURA", lambda x: float(x[base_func.loc[x.index, "ORDEN"]].sum())),
                "Total tipo de captura": ("VALOR_CAPTURA", "sum"),
            }
        ).reset_index()
        resumen = resumen.rename(columns={
            "FUNCIONARIO": "Grado, nombres y apellidos",
            "CEDULA": "Cédula",
            "ESTACION_RESUMEN": "Estación",
        }).sort_values(["Total tipo de captura", "Grado, nombres y apellidos"], ascending=[False, True])
        resumen["Capturas flagrancia"] = resumen["Capturas flagrancia"].round(0).astype(int)
        resumen["Capturas orden judicial"] = resumen["Capturas orden judicial"].round(0).astype(int)
        resumen["Total tipo de captura"] = resumen["Total tipo de captura"].round(0).astype(int)

        clave_estado = "operatividad_funcionario_cedula"
        seleccionado = st.session_state.get(clave_estado, "")
        btn_col, info_col = st.columns([1, 4])
        with btn_col:
            if st.button("Mostrar todos", key="operatividad_mostrar_todos", use_container_width=True):
                st.session_state.pop(clave_estado, None)
                st.rerun()
        with info_col:
            if seleccionado:
                st.info(f"Filtro activo · Cédula: {seleccionado}")
            else:
                st.caption("Sin funcionario seleccionado · se muestran los datos de todos los funcionarios.")

        # Estilo de celdas aplicado al DataFrame: encabezado institucional,
        # bandas discretas y énfasis visual en las cifras, conservando selección por fila.
        tabla_estilizada = (
            resumen.style
            .set_table_styles([
                {"selector": "th", "props": [
                    ("background-color", "#102A4A"), ("color", "#FFFFFF"),
                    ("font-weight", "800"), ("font-size", "13px"),
                    ("border-bottom", "3px solid #C49A55"), ("padding", "12px 10px")
                ]},
                {"selector": "td", "props": [
                    ("color", "#1C3048"), ("font-size", "13px"),
                    ("padding", "10px"), ("border-bottom", "1px solid #E5EBF2")
                ]},
                {"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#F4F7FB")]},
                {"selector": "tbody tr:hover", "props": [("background-color", "#E7EFF9")]},
                {"selector": "table", "props": [
                    ("border-collapse", "separate"), ("border-spacing", "0"),
                    ("border", "1px solid #D5DFEB"), ("border-radius", "12px"),
                    ("overflow", "hidden")
                ]},
            ])
            .format(precision=0, thousands=".", decimal=",")
        )
        evento_tabla = st.dataframe(
            tabla_estilizada,
            use_container_width=True,
            hide_index=True,
            height=min(440, 46 + 35 * min(len(resumen), 11)),
            on_select="rerun",
            selection_mode="single-row",
            key="tabla_funcionarios_operatividad",
            column_config={
                "Grado, nombres y apellidos": st.column_config.TextColumn(
                    "Grado, nombres y apellidos",
                    width="large",
                ),
                "Cédula": st.column_config.TextColumn(
                    "Cédula",
                    width="medium",
                ),
                "Estación": st.column_config.TextColumn(
                    "Estación",
                    width="medium",
                ),
                "Capturas flagrancia": st.column_config.NumberColumn(
                    "Capturas flagrancia",
                    format="%d",
                    width="small",
                ),
                "Capturas orden judicial": st.column_config.NumberColumn(
                    "Capturas orden judicial",
                    format="%d",
                    width="small",
                ),
                "Total tipo de captura": st.column_config.NumberColumn(
                    "Total tipo de captura",
                    format="%d",
                    width="small",
                ),
            },
        )

        filas_seleccionadas = evento_tabla.selection.rows if hasattr(evento_tabla, "selection") else []
        if filas_seleccionadas:
            fila_idx = filas_seleccionadas[0]
            if 0 <= fila_idx < len(resumen):
                cedula_elegida = str(resumen.iloc[fila_idx]["Cédula"]).strip()
                if cedula_elegida:
                    st.session_state[clave_estado] = cedula_elegida
                    seleccionado = cedula_elegida

        if seleccionado and "IDENTIFICACION" in ops.columns:
            ids_limpios = ops["IDENTIFICACION"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            filtrada = ops.loc[ids_limpios == str(seleccionado)].copy()
            if not filtrada.empty:
                ops = filtrada
                st.markdown(
                    f'<div style="background:#F3F7FC;border-left:4px solid {AZUL};padding:10px 14px;border-radius:8px;margin:8px 0 18px 0;color:#12345A;font-weight:600;">'
                    f'Vista filtrada · {filtrada[columna_funcionario].dropna().astype(str).iloc[0]} · Cédula {seleccionado}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning("No se encontraron registros operativos para la cédula seleccionada en los filtros actuales.")
        elif seleccionado:
            st.warning("No se puede aplicar el filtro porque el reporte no contiene la columna IDENTIFICACION.")
    else:
        st.info("No hay datos suficientes para construir la tabla interactiva de funcionarios.")

    total_tipo = suma_columna(ops, "TOTAL TIPO DE CAPTURA")
    total_personas = suma_columna(ops, "TOTAL PERSONAS CAPTURADAS")
    total_actividad = suma_columna(ops, "TOTAL ACTIVIDAD OPERATIVA")
    cantidad_estaciones = ops["ESTACION"].nunique() if "ESTACION" in ops.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta("Total tipo de captura", formatear_entero(total_tipo), "Suma de TOTAL TIPO DE CAPTURA")
    with c2:
        tarjeta("Personas capturadas", formatear_entero(total_personas), "Según el reporte de operatividad")
    with c3:
        tarjeta("Actividades operativas", formatear_entero(total_actividad), "Suma de actividades registradas")
    with c4:
        tarjeta("Estaciones con registros", formatear_entero(cantidad_estaciones), "En los filtros seleccionados")

    if ops.empty:
        st.info("No hay registros de operatividad para los filtros seleccionados.")
    else:
        # 1. Línea de tiempo mensual de tipos de captura.
        titulo_seccion("Línea de tiempo mensual · Tipo de captura")
        if "FECHA_HECHO" in ops.columns and "TOTAL TIPO DE CAPTURA" in ops.columns:
            temporal = ops.dropna(subset=["FECHA_HECHO"]).copy()
            if not temporal.empty:
                temporal["MES_FECHA"] = temporal["FECHA_HECHO"].dt.to_period("M").dt.to_timestamp()
                mensual = temporal.groupby("MES_FECHA", as_index=False)["TOTAL TIPO DE CAPTURA"].sum()
                mensual = mensual.sort_values("MES_FECHA")
                fig = px.line(
                    mensual, x="MES_FECHA", y="TOTAL TIPO DE CAPTURA",
                    markers=True, line_shape="spline",
                    labels={"MES_FECHA": "Mes", "TOTAL TIPO DE CAPTURA": "Total tipo de captura"},
                    hover_data={"MES_FECHA": "|%B %Y", "TOTAL TIPO DE CAPTURA": ":,.0f"},
                )
                fig.update_traces(line=dict(color=AZUL, width=3), marker=dict(size=8, color=DORADO))
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", hovermode="x unified", xaxis=dict(tickformat="%b %Y"), margin=dict(l=10,r=10,t=25,b=10))
                st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
            else:
                st.info("No hay fechas válidas para construir la línea de tiempo mensual.")
        else:
            st.info("Faltan FECHA_HECHO o TOTAL TIPO DE CAPTURA para la línea de tiempo.")

        # Gráficos de cuadrante y estación en dos columnas.
        izq, der = st.columns(2, gap="large")
        with izq:
            titulo_seccion("Distribución por IND CUADRANTE")
            if "IND CUADRANTE" in ops.columns:
                campo = ops.copy()
                campo["IND CUADRANTE"] = campo["IND CUADRANTE"].fillna("No especificado").astype(str).str.strip()
                campo.loc[campo["IND CUADRANTE"] == "", "IND CUADRANTE"] = "No especificado"
                if "TOTAL TIPO DE CAPTURA" in campo.columns:
                    agregado = campo.groupby("IND CUADRANTE", as_index=False)["TOTAL TIPO DE CAPTURA"].sum().rename(columns={"TOTAL TIPO DE CAPTURA":"CAPTURAS"})
                else:
                    agregado = campo.groupby("IND CUADRANTE").size().reset_index(name="CAPTURAS")
                agregado = agregado.sort_values("CAPTURAS", ascending=False).head(20)
                fig = px.bar(agregado, x="IND CUADRANTE", y="CAPTURAS", text="CAPTURAS", labels={"CAPTURAS":"Total tipo de captura"}, color_discrete_sequence=[DORADO])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-30, margin=dict(l=10,r=10,t=20,b=10))
                st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
            else:
                st.info("El reporte no contiene la columna IND CUADRANTE.")

        with der:
            titulo_seccion("Actividad operativa por estación")
            if "ESTACION" in ops.columns and "TOTAL TIPO DE CAPTURA" in ops.columns:
                por_estacion = ops.copy()
                por_estacion["ESTACION"] = por_estacion["ESTACION"].fillna("No especificada").astype(str)
                por_estacion["TOTAL TIPO DE CAPTURA"] = pd.to_numeric(por_estacion["TOTAL TIPO DE CAPTURA"], errors="coerce").fillna(0)
                est = (
                    por_estacion.groupby("ESTACION", as_index=False)["TOTAL TIPO DE CAPTURA"]
                    .sum()
                    .rename(columns={"TOTAL TIPO DE CAPTURA": "TOTAL"})
                    .sort_values("TOTAL", ascending=False)
                    .head(15)
                )
                fig = px.bar(
                    est, x="TOTAL", y="ESTACION", orientation="h", text="TOTAL",
                    labels={"TOTAL": "Total de tipos de captura", "ESTACION": "Estación"},
                    color_discrete_sequence=[AZUL]
                )
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=35, t=20, b=10))
                st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
            elif "ESTACION" not in ops.columns:
                st.info("El reporte no contiene la columna ESTACION.")
            else:
                st.info("El reporte no contiene la columna TOTAL TIPO DE CAPTURA.")

        # Capturas de homicidio por funcionario.
        titulo_seccion("Funcionarios con capturas asociadas a homicidio")
        if "DELITO DE CAPTURA" in ops.columns:
            homic = ops[ops["DELITO DE CAPTURA"].astype(str).str.contains("homicidio", case=False, na=False)].copy()
            if not homic.empty:
                campos = [c for c in ["GR APELLIDOS Y NOMBRES POLICIA_1", "IDENTIFICACION", "ESTACION", "DELITO DE CAPTURA", "TOTAL TIPO DE CAPTURA", "TOTAL PERSONAS CAPTURADAS", "FECHA_HECHO"] if c in homic.columns]
                if "TOTAL TIPO DE CAPTURA" in homic.columns:
                    homic = homic.sort_values("TOTAL TIPO DE CAPTURA", ascending=False)
                mostrar_tabla(homic[campos], campos, {
                    "GR APELLIDOS Y NOMBRES POLICIA_1":"Grado, nombres y apellidos",
                    "IDENTIFICACION":"Cédula", "ESTACION":"Estación", "DELITO DE CAPTURA":"Delito de captura",
                    "TOTAL TIPO DE CAPTURA":"Total tipo de captura", "TOTAL PERSONAS CAPTURADAS":"Personas capturadas", "FECHA_HECHO":"Fecha",
                })
            else:
                st.info("No se encontraron registros cuyo delito de captura contenga 'homicidio'.")
        else:
            st.info("El reporte no contiene la columna DELITO DE CAPTURA.")

        # Comparativo de flagrancia y orden judicial por funcionario.
        titulo_seccion("Capturas por funcionario · Flagrancia y orden judicial")
        if "TIPO DE CAPTURA" in ops.columns:
            tipo = ops["TIPO DE CAPTURA"].fillna("").astype(str).str.casefold()
            subset = ops[tipo.str.contains("flagrancia|orden judicial", regex=True, na=False)].copy()
            if not subset.empty:
                subset["TIPO_NORMALIZADO"] = subset["TIPO DE CAPTURA"].astype(str).str.casefold().apply(
                    lambda x: "Flagrancia" if "flagrancia" in x else "Orden judicial"
                )
                columna_metrica = "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in subset.columns else None
                if columna_metrica:
                    subset[columna_metrica] = pd.to_numeric(subset[columna_metrica], errors="coerce").fillna(0)
                    resumen_func = subset.groupby(["GR APELLIDOS Y NOMBRES POLICIA_1", "TIPO_NORMALIZADO"], dropna=False)[columna_metrica].sum().reset_index(name="TOTAL") if "GR APELLIDOS Y NOMBRES POLICIA_1" in subset.columns else subset.groupby("TIPO_NORMALIZADO")[columna_metrica].sum().reset_index(name="TOTAL")
                    if "GR APELLIDOS Y NOMBRES POLICIA_1" in resumen_func.columns:
                        resumen_func["FUNCIONARIO"] = resumen_func["GR APELLIDOS Y NOMBRES POLICIA_1"].fillna("No registrado").astype(str)
                        fig = px.bar(resumen_func, x="FUNCIONARIO", y="TOTAL", color="TIPO_NORMALIZADO", barmode="group", labels={"TOTAL":"Total tipo de captura", "FUNCIONARIO":"Grado, nombres y apellidos", "TIPO_NORMALIZADO":"Tipo de captura"}, color_discrete_map={"Flagrancia":AZUL,"Orden judicial":DORADO})
                        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-35, margin=dict(l=10,r=10,t=20,b=10))
                        st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
                    mostrar_tabla(resumen_func, list(resumen_func.columns), {"GR APELLIDOS Y NOMBRES POLICIA_1":"Grado, nombres y apellidos", "TIPO_NORMALIZADO":"Tipo de captura", "TOTAL":"Total tipo de captura"})
                else:
                    st.info("Falta TOTAL TIPO DE CAPTURA para comparar flagrancia y orden judicial.")
            else:
                st.info("No se encontraron tipos de captura de flagrancia u orden judicial en los filtros actuales.")
        else:
            st.info("El reporte no contiene la columna TIPO DE CAPTURA.")

        # Delitos de captura.
        titulo_seccion("Distribución por delito de captura")
        if "DELITO DE CAPTURA" in ops.columns:
            delitos_cap = ops.copy()
            delitos_cap["DELITO DE CAPTURA"] = delitos_cap["DELITO DE CAPTURA"].fillna("No especificado").astype(str)
            metrica_delito = "TOTAL DELITO DE CAPTURA" if "TOTAL DELITO DE CAPTURA" in delitos_cap.columns else "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in delitos_cap.columns else None
            if metrica_delito:
                delitos_cap[metrica_delito] = pd.to_numeric(delitos_cap[metrica_delito], errors="coerce").fillna(0)
                por_delito = delitos_cap.groupby("DELITO DE CAPTURA", as_index=False)[metrica_delito].sum().rename(columns={metrica_delito:"TOTAL"}).sort_values("TOTAL", ascending=False).head(20)
                fig = px.bar(por_delito, x="TOTAL", y="DELITO DE CAPTURA", orientation="h", text="TOTAL", labels={"TOTAL":"Total registrado"}, color_discrete_sequence=[DORADO])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis={"categoryorder":"total ascending"}, margin=dict(l=10,r=10,t=20,b=10))
                st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
            else:
                st.info("Falta una columna numérica para resumir los delitos de captura.")
        else:
            st.info("El reporte no contiene la columna DELITO DE CAPTURA.")

        # Actividad operativa.
        titulo_seccion("Tipos de actividad operativa")
        if "ACTIVIDAD OPERATIVA" in ops.columns:
            actividades = ops.copy()
            actividades["ACTIVIDAD OPERATIVA"] = actividades["ACTIVIDAD OPERATIVA"].fillna("No especificada").astype(str)
            metrica_actividad = "TOTAL ACTIVIDAD OPERATIVA" if "TOTAL ACTIVIDAD OPERATIVA" in actividades.columns else "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in actividades.columns else None
            if metrica_actividad:
                actividades[metrica_actividad] = pd.to_numeric(actividades[metrica_actividad], errors="coerce").fillna(0)
                por_actividad = actividades.groupby("ACTIVIDAD OPERATIVA", as_index=False)[metrica_actividad].sum().rename(columns={metrica_actividad:"TOTAL"}).sort_values("TOTAL", ascending=False).head(20)
                fig = px.bar(por_actividad, x="TOTAL", y="ACTIVIDAD OPERATIVA", orientation="h", text="TOTAL", labels={"TOTAL":"Total registrado"}, color_discrete_sequence=[AZUL])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", yaxis={"categoryorder":"total ascending"}, margin=dict(l=10,r=10,t=20,b=10))
                st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
            else:
                st.info("Falta una columna numérica para resumir la actividad operativa.")
        else:
            st.info("El reporte no contiene la columna ACTIVIDAD OPERATIVA.")

        # Mapa interactivo con latitud y longitud.
        titulo_seccion("Mapa georreferenciado de registros operativos")
        if "LATITUD" in ops.columns and "LONGITUD" in ops.columns:
            mapa = ops.copy()
            mapa["LATITUD"] = pd.to_numeric(mapa["LATITUD"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            mapa["LONGITUD"] = pd.to_numeric(mapa["LONGITUD"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            mapa = mapa.dropna(subset=["LATITUD", "LONGITUD"])
            mapa = mapa[mapa["LATITUD"].between(-90, 90) & mapa["LONGITUD"].between(-180, 180)]
            if not mapa.empty:
                hover_cols = [c for c in ["ESTACION", "CAI", "CUADRANTE", "IND CUADRANTE", "TIPO DE CAPTURA", "DELITO DE CAPTURA", "ACTIVIDAD OPERATIVA", "FECHA_HECHO", "GR APELLIDOS Y NOMBRES POLICIA_1"] if c in mapa.columns]
                color_col = "TIPO DE CAPTURA" if "TIPO DE CAPTURA" in mapa.columns else None
                size_col = "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in mapa.columns and (mapa["TOTAL TIPO DE CAPTURA"] > 0).any() else None
                fig = px.scatter_mapbox(
                    mapa, lat="LATITUD", lon="LONGITUD", hover_name="ESTACION" if "ESTACION" in mapa.columns else None,
                    hover_data=hover_cols, color=color_col, size=size_col, size_max=18, zoom=9,
                    mapbox_style="open-street-map", center={"lat": float(mapa["LATITUD"].median()), "lon": float(mapa["LONGITUD"].median())},
                )
                fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=560, legend_title_text="Tipo de captura")
                st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
                st.caption(f"Se muestran {len(mapa):,} registros con coordenadas válidas. Verifica que las coordenadas del archivo estén en grados decimales.")
            else:
                st.info("No se encontraron coordenadas válidas en LATITUD y LONGITUD.")
        else:
            st.info("El reporte no contiene las columnas LATITUD y LONGITUD.")

        titulo_seccion("Registros detallados de operatividad")
        columnas_ops = [
            "FECHA_HECHO", "BOLETIN", "MUNICIPIO", "DISTRITO", "ESTACION", "CAI",
            "CUADRANTE", "IND CUADRANTE", "GR APELLIDOS Y NOMBRES POLICIA_1", "IDENTIFICACION",
            "TIPO DE CAPTURA", "TOTAL TIPO DE CAPTURA", "TOTAL PERSONAS CAPTURADAS",
            "DELITO DE CAPTURA", "TOTAL DELITO DE CAPTURA", "ACTIVIDAD OPERATIVA",
            "TOTAL ACTIVIDAD OPERATIVA", "LATITUD", "LONGITUD",
        ]
        mostrar_tabla(
            ops.sort_values("FECHA_HECHO", ascending=False, na_position="last"),
            columnas_ops,
            {
                "FECHA_HECHO":"Fecha", "BOLETIN":"Boletín", "MUNICIPIO":"Municipio", "DISTRITO":"Distrito",
                "ESTACION":"Estación", "CAI":"CAI", "CUADRANTE":"Cuadrante", "IND CUADRANTE":"Indicador de cuadrante",
                "GR APELLIDOS Y NOMBRES POLICIA_1":"Grado, nombres y apellidos", "IDENTIFICACION":"Cédula",
                "TIPO DE CAPTURA":"Tipo de captura", "TOTAL TIPO DE CAPTURA":"Total tipo de captura",
                "TOTAL PERSONAS CAPTURADAS":"Personas capturadas", "DELITO DE CAPTURA":"Delito de captura",
                "TOTAL DELITO DE CAPTURA":"Total delito de captura", "ACTIVIDAD OPERATIVA":"Actividad operativa",
                "TOTAL ACTIVIDAD OPERATIVA":"Total actividad", "LATITUD":"Latitud", "LONGITUD":"Longitud",
            },
        )

    titulo_seccion("Ficha individual del funcionario")
    selector_funcionario()
    mostrar_ficha_seleccionada()


# ============================================================
# PANTALLA 3: GESTIÓN DELICTIVA
# ============================================================

elif pantalla == "Registro Delictivo":
    ROJO_CARMESI = "#9F1239"
    ROJO_CARMESI_CLARO = "#BE123C"
    ROJO_SUAVE = "#FFF1F2"

    encabezado(
        "GESTIÓN DELICTIVA",
        "Análisis de delitos, comportamiento mensual y desempeño por funcionario",
    )

    # Preparar la tabla maestra de funcionarios a partir de los registros delictivos.
    base_gestion = delitos_f.copy()
    if "CANTIDAD CASOS" in base_gestion.columns:
        base_gestion["CANTIDAD CASOS"] = pd.to_numeric(
            base_gestion["CANTIDAD CASOS"], errors="coerce"
        ).fillna(0)
    else:
        base_gestion["CANTIDAD CASOS"] = 1

    if not base_gestion.empty and "_ID_CLAVE" in base_gestion.columns:
        cantidades = (
            base_gestion.groupby("_ID_CLAVE", dropna=False)["CANTIDAD CASOS"]
            .sum().reset_index(name="CANTIDAD DELITOS")
        )
        tabla_funcionarios = maestros_f.merge(cantidades, on="_ID_CLAVE", how="left")
        tabla_funcionarios["CANTIDAD DELITOS"] = tabla_funcionarios["CANTIDAD DELITOS"].fillna(0)

        # La estación se toma del registro delictivo más reciente del funcionario.
        if "FECHA_HECHO" in base_gestion.columns and "ESTACION" in base_gestion.columns:
            estaciones_func = (
                base_gestion.sort_values("FECHA_HECHO", ascending=False, na_position="last")
                .drop_duplicates("_ID_CLAVE")[["_ID_CLAVE", "ESTACION"]]
                .rename(columns={"ESTACION": "ESTACIÓN DEL REGISTRO"})
            )
            tabla_funcionarios = tabla_funcionarios.drop(
                columns=["ESTACIÓN DEL REGISTRO"], errors="ignore"
            ).merge(estaciones_func, on="_ID_CLAVE", how="left")
        else:
            tabla_funcionarios["ESTACIÓN DEL REGISTRO"] = tabla_funcionarios.get("ESTACION", "")

        tabla_funcionarios["GRADO Y NOMBRE"] = (
            tabla_funcionarios.get("GRADO", "").fillna("").astype(str).str.strip()
            + " " + tabla_funcionarios.get("NOMBRE", "").fillna("").astype(str).str.strip()
        ).str.strip()
        tabla_funcionarios["CÉDULA"] = tabla_funcionarios["_ID_CLAVE"].astype(str)
        tabla_funcionarios["ESTACIÓN"] = tabla_funcionarios["ESTACIÓN DEL REGISTRO"].fillna("").astype(str).str.strip()
        tabla_funcionarios = tabla_funcionarios.sort_values("CANTIDAD DELITOS", ascending=False)
    else:
        tabla_funcionarios = pd.DataFrame(columns=["GRADO Y NOMBRE", "CÉDULA", "ESTACIÓN", "CANTIDAD DELITOS", "_ID_CLAVE"])

    titulo_seccion("01 · Funcionarios y cantidad de delitos")
    st.markdown(
        f"""<div style="background:linear-gradient(115deg,{ROJO_CARMESI},#701A35);color:#fff;
        border-radius:14px;padding:15px 19px;margin:0 0 12px 0;box-shadow:0 6px 18px rgba(159,18,57,.14);">
        <div style="font-size:16px;font-weight:800;letter-spacing:.2px;">SELECCIÓN DE FUNCIONARIO</div>
        <div style="font-size:13px;color:#FFE4E9;margin-top:4px;">Selecciona un funcionario para filtrar todos los indicadores y gráficos de este panel.</div></div>""",
        unsafe_allow_html=True,
    )

    if not tabla_funcionarios.empty:
        # La tabla superior es interactiva: al hacer clic en una fila se filtra
        # todo el panel, igual que en la tabla del panel Operatividad.
        clave_estado_g = "gestion_delictiva_funcionario_cedula"
        seleccionado_g = str(st.session_state.get(clave_estado_g, "") or "").strip()

        controles_g, estado_g = st.columns([1, 4])
        with controles_g:
            if st.button("Mostrar todos", key="gestion_delictiva_mostrar_todos", use_container_width=True):
                st.session_state.pop(clave_estado_g, None)
                st.session_state.pop("tabla_funcionarios_gestion_delictiva", None)
                st.rerun()
        with estado_g:
            if seleccionado_g:
                fila_activa = tabla_funcionarios[tabla_funcionarios["CÉDULA"].astype(str) == seleccionado_g]
                nombre_activo = fila_activa.iloc[0]["GRADO Y NOMBRE"] if not fila_activa.empty else seleccionado_g
                st.info(f"Filtro activo · {nombre_activo} · C.C. {seleccionado_g}")
            else:
                st.caption("Haz clic en cualquier fila de la tabla para seleccionar un funcionario y filtrar los gráficos de abajo.")

        vista_funcionarios = tabla_funcionarios[[
            "GRADO Y NOMBRE", "CÉDULA", "ESTACIÓN", "CANTIDAD DELITOS"
        ]].copy().reset_index(drop=True)
        vista_funcionarios = vista_funcionarios.rename(columns={
            "GRADO Y NOMBRE": "Grado, nombres y apellidos",
            "CÉDULA": "Cédula",
            "ESTACIÓN": "Estación",
            "CANTIDAD DELITOS": "Cantidad de delitos",
        })
        evento_tabla_g = st.dataframe(
            vista_funcionarios,
            use_container_width=True,
            hide_index=True,
            height=min(440, 46 + 35 * min(len(vista_funcionarios), 11)),
            on_select="rerun",
            selection_mode="single-row",
            key="tabla_funcionarios_gestion_delictiva",
            column_config={
                "Grado, nombres y apellidos": st.column_config.TextColumn("Grado, nombres y apellidos", width="large"),
                "Cédula": st.column_config.TextColumn("Cédula", width="medium"),
                "Estación": st.column_config.TextColumn("Estación", width="medium"),
                "Cantidad de delitos": st.column_config.NumberColumn("Cantidad de delitos", format="%d", width="small"),
            },
        )
        filas_g = evento_tabla_g.selection.rows if hasattr(evento_tabla_g, "selection") else []
        if filas_g:
            idx_g = filas_g[0]
            if 0 <= idx_g < len(vista_funcionarios):
                cedula_elegida_g = str(vista_funcionarios.iloc[idx_g]["Cédula"]).strip()
                if cedula_elegida_g:
                    st.session_state[clave_estado_g] = cedula_elegida_g
                    seleccionado_g = cedula_elegida_g

        if seleccionado_g:
            delitos_g = base_gestion[base_gestion["_ID_CLAVE"].astype(str) == seleccionado_g].copy()
        else:
            delitos_g = base_gestion.copy()
    else:
        delitos_g = base_gestion.copy()
        st.info("No hay registros de funcionarios para los filtros actuales.")

    # Métricas y gráficos de Gestión delictiva utilizan la selección anterior.
    total_casos_g = float(pd.to_numeric(delitos_g.get("CANTIDAD CASOS", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    total_victimas_g = float(pd.to_numeric(delitos_g.get("CANTIDAD VICTIMA", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if "CANTIDAD VICTIMA" in delitos_g.columns else 0
    tipos_g = int(delitos_g["DELITO"].nunique()) if "DELITO" in delitos_g.columns else 0
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta("Casos registrados", formatear_entero(total_casos_g))
    with c2:
        tarjeta("Víctimas registradas", formatear_entero(total_victimas_g))
    with c3:
        tarjeta("Tipos de delito", formatear_entero(tipos_g))

    # Colores carmesí consistentes para todas las visualizaciones de este panel.
    titulo_seccion("02 · Evolución mensual de delitos")
    con_fecha_g = delitos_g.dropna(subset=["FECHA_HECHO"]).copy() if "FECHA_HECHO" in delitos_g.columns else pd.DataFrame()
    if not con_fecha_g.empty:
        con_fecha_g["MES_ANIO"] = con_fecha_g["FECHA_HECHO"].dt.to_period("M").astype(str)
        if "CANTIDAD CASOS" in con_fecha_g.columns:
            tendencia_g = con_fecha_g.groupby("MES_ANIO")["CANTIDAD CASOS"].sum().reset_index(name="CASOS")
        else:
            tendencia_g = con_fecha_g.groupby("MES_ANIO").size().reset_index(name="CASOS")
        fig = px.line(
            tendencia_g, x="MES_ANIO", y="CASOS", markers=True, text="CASOS",
            color_discrete_sequence=[ROJO_CARMESI],
            labels={"MES_ANIO": "Mes", "CASOS": "Cantidad de delitos"},
        )
        fig.update_traces(line=dict(width=4, color=ROJO_CARMESI), marker=dict(size=10, color=ROJO_CARMESI),
                          textposition="top center", textfont=dict(size=13, color=ROJO_CARMESI))
        fig.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de delitos")
        st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
    else:
        st.info("No hay fechas válidas para mostrar la evolución mensual.")

    col_est, col_tipo = st.columns(2)
    with col_est:
        titulo_seccion("03 · Delitos por estación")
        if not delitos_g.empty and "ESTACION" in delitos_g.columns:
            metrica_casos = "CANTIDAD CASOS" if "CANTIDAD CASOS" in delitos_g.columns else "DELITO"
            if metrica_casos == "CANTIDAD CASOS":
                estacion_g = delitos_g.groupby("ESTACION", dropna=False)[metrica_casos].sum().reset_index(name="CASOS")
            else:
                estacion_g = delitos_g.groupby("ESTACION", dropna=False).size().reset_index(name="CASOS")
            estacion_g["ESTACION"] = estacion_g["ESTACION"].fillna("No especificada").astype(str)
            estacion_g = estacion_g.sort_values("CASOS", ascending=False).head(12).sort_values("CASOS")
            fig = px.bar(estacion_g, x="CASOS", y="ESTACION", orientation="h", text="CASOS",
                         color_discrete_sequence=[ROJO_CARMESI], labels={"CASOS": "Cantidad de delitos", "ESTACION": "Estación"})
            fig.update_traces(textposition="outside", marker_color=ROJO_CARMESI)
            fig.update_layout(xaxis_title="Cantidad de delitos", yaxis_title="")
            st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
        else:
            st.info("No hay información de estación para la selección actual.")

    with col_tipo:
        titulo_seccion("04 · Tipos de delitos")
        if not delitos_g.empty and "DELITO" in delitos_g.columns:
            metrica_tipo = "CANTIDAD CASOS" if "CANTIDAD CASOS" in delitos_g.columns else "DELITO"
            if metrica_tipo == "CANTIDAD CASOS":
                tipos_delito_g = delitos_g.groupby("DELITO", dropna=False)[metrica_tipo].sum().reset_index(name="CASOS")
            else:
                tipos_delito_g = delitos_g.groupby("DELITO", dropna=False).size().reset_index(name="CASOS")
            tipos_delito_g["DELITO"] = tipos_delito_g["DELITO"].fillna("No especificado").astype(str)
            tipos_delito_g = tipos_delito_g.sort_values("CASOS", ascending=False).head(12).sort_values("CASOS")
            fig = px.bar(tipos_delito_g, x="CASOS", y="DELITO", orientation="h", text="CASOS",
                         color_discrete_sequence=[ROJO_CARMESI_CLARO], labels={"CASOS": "Cantidad de delitos", "DELITO": "Tipo de delito"})
            fig.update_traces(textposition="outside", marker_color=ROJO_CARMESI_CLARO)
            fig.update_layout(xaxis_title="Cantidad de delitos", yaxis_title="")
            st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
        else:
            st.info("No hay tipos de delitos para la selección actual.")

    titulo_seccion("05 · Funcionarios con más delitos de homicidio")
    if not delitos_g.empty and "DELITO" in delitos_g.columns:
        homicidios_g = delitos_g[delitos_g["DELITO"].astype(str).str.contains(r"\bhomicidio\b", case=False, regex=True, na=False)].copy()
        if not homicidios_g.empty:
            if "CANTIDAD CASOS" in homicidios_g.columns:
                homicidios_g["CANTIDAD CASOS"] = pd.to_numeric(homicidios_g["CANTIDAD CASOS"], errors="coerce").fillna(0)
                ranking_hom_g = homicidios_g.groupby("_ID_CLAVE")["CANTIDAD CASOS"].sum().reset_index(name="HOMICIDIOS")
            else:
                ranking_hom_g = homicidios_g.groupby("_ID_CLAVE").size().reset_index(name="HOMICIDIOS")
            ranking_hom_g = ranking_hom_g.merge(maestros[["_ID_CLAVE", "GRADO", "NOMBRE"]], on="_ID_CLAVE", how="left")
            ranking_hom_g["FUNCIONARIO"] = (ranking_hom_g["GRADO"].fillna("").astype(str) + " " + ranking_hom_g["NOMBRE"].fillna("").astype(str)).str.strip()
            ranking_hom_g = ranking_hom_g.sort_values("HOMICIDIOS", ascending=False).head(10).sort_values("HOMICIDIOS")
            fig = px.bar(ranking_hom_g, x="HOMICIDIOS", y="FUNCIONARIO", orientation="h", text="HOMICIDIOS",
                         color_discrete_sequence=[ROJO_CARMESI], labels={"HOMICIDIOS": "Casos de homicidio", "FUNCIONARIO": "Funcionario"})
            fig.update_traces(textposition="outside", marker_color=ROJO_CARMESI)
            fig.update_layout(xaxis_title="Casos de homicidio", yaxis_title="")
            st.plotly_chart(estilizar_grafico(fig), use_container_width=True)
        else:
            st.info("No se encontraron delitos cuyo nombre contenga 'homicidio' para la selección actual.")

    titulo_seccion("06 · Registros delictivos")
    columnas_tabla_g = [
        "FECHA_HECHO", "BOLETIN", "MUNICIPIO", "DISTRITO", "ESTACION", "CAI", "CUADRANTE",
        "GR APELLIDOS Y NOMBRES POLICIA_1", "IDENTIFICACION", "DELITO", "CANTIDAD CASOS", "CANTIDAD VICTIMA",
    ]
    mostrar_tabla(
        delitos_g.sort_values("FECHA_HECHO", ascending=False, na_position="last") if "FECHA_HECHO" in delitos_g.columns else delitos_g,
        columnas_tabla_g,
        {
            "FECHA_HECHO": "Fecha", "BOLETIN": "Boletín", "MUNICIPIO": "Municipio", "DISTRITO": "Distrito",
            "ESTACION": "Estación", "CAI": "CAI", "CUADRANTE": "Cuadrante",
            "GR APELLIDOS Y NOMBRES POLICIA_1": "Funcionario", "IDENTIFICACION": "Identificación",
            "DELITO": "Delito", "CANTIDAD CASOS": "Casos", "CANTIDAD VICTIMA": "Víctimas",
        },
    )


# ============================================================
# PIE
# ============================================================

st.markdown(
    '<div class="pie">DASHBOARD MEBAR · Panel de análisis institucional · '
    'La información depende de los reportes Excel cargados.</div>',
    unsafe_allow_html=True,
)