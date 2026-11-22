import html
import re
import unicodedata
from pathlib import Path
from time import perf_counter

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.carga import (
    cargar_antecedentes_persona,
    cargar_antecedentes_vehiculo,
    cargar_delitos_operatividad,
    cargar_permisos,
    cargar_rnmc,
    cargar_tahum,
    cargar_turnos,
)

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
    for tr in fig.data:
        if tr.type == "bar":
            tr.update(textposition="auto", textfont=dict(size=13, color="#142B45"), cliponaxis=False)
        elif tr.type == "scatter" and tr.mode and "lines" in tr.mode and tr.name != "Mapa":
            tr.update(line=dict(width=3), marker=dict(size=8))
    return fig


def mostrar_grafico(fig):
    """Muestra un gráfico a todo el ancho, compatible con versiones nuevas y antiguas de Streamlit."""
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def grafico_medidor(valor, maximo, titulo, decimales=0):
    """Medidor: la aguja mide `valor` sobre una escala de 0 a `maximo` (línea dorada)."""
    maximo = max(int(maximo), 1)
    eje_max = max(maximo, float(valor), 1)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(valor),
        number={"valueformat": f",.{decimales}f", "suffix": f" / {maximo}",
                "font": {"size": 32, "color": AZUL}},
        title={"text": titulo, "font": {"size": 14, "color": "#34465C"}},
        gauge={
            "axis": {"range": [0, eje_max], "tickfont": {"size": 11, "color": "#526174"}},
            "bar": {"color": AZUL, "thickness": 0.3},
            "bgcolor": "white", "borderwidth": 1, "bordercolor": "#E3EAF2",
            "steps": [
                {"range": [0, maximo * 0.5], "color": "#F8E4E8"},
                {"range": [maximo * 0.5, maximo * 0.8], "color": "#FBF3DF"},
                {"range": [maximo * 0.8, maximo], "color": "#E3F3EA"},
            ],
            "threshold": {"line": {"color": DORADO, "width": 4}, "thickness": 0.8, "value": maximo},
        },
    ))
    fig.update_layout(height=200, margin=dict(l=25, r=25, t=55, b=5), paper_bgcolor="white",
                      font=dict(family="Inter, Arial, sans-serif"))
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

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h3 {{
        color: #EAF1F8 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.5px !important;
    }}

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] div {{
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }}

    [data-testid="stSidebar"] input::placeholder {{
        color: #8FA3BC !important;
        opacity: 1 !important;
    }}

    [data-testid="stSidebar"] [role="listbox"] div,
    [data-testid="stSidebar"] [data-baseweb="popover"] div {{
        color: #142B45 !important;
    }}

    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        background: rgba(255,255,255,0.06);
        border-radius: 9px;
        padding: 8px 10px;
        margin-bottom: 5px;
        color: #FFFFFF !important;
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

    div[data-testid="stButton"] button[kind="secondary"] {{
        background: linear-gradient(135deg, #1a3a5c 0%, #0f2a4a 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #C5A45B !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(26, 58, 92, 0.3) !important;
    }}
    div[data-testid="stButton"] button[kind="secondary"]:hover {{
        background: linear-gradient(135deg, #244D78 0%, #1a3a5c 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(26, 58, 92, 0.4) !important;
        border-color: #FFD700 !important;
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
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.lower() in {"", "nan", "none", "nat"}:
        return ""
    if re.fullmatch(r"\d+\.0+", texto):
        texto = texto.split(".")[0]
    return re.sub(r"\s+", "", texto).upper()


def normalizar_serie_id(serie):
    """Versión vectorizada de normalizar_id: mucho más rápida que Series.apply/map."""
    s = serie.astype("object").where(serie.notna(), "")
    s = s.astype(str).fillna("").str.strip()
    s = s.where(~s.str.lower().isin({"", "nan", "none", "nat"}), "")
    s = s.str.replace(r"^(\d+)\.0+$", r"\1", regex=True)
    s = s.str.replace(r"\s+", "", regex=True).str.upper()
    return s.fillna("")


def numero(valor):
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


def reparar_codificacion(valor):
    """Corrige texto mal codificado (ej. 'ResoluciÃ³n' -> 'Resolución')."""
    if not isinstance(valor, str) or ("Ã" not in valor and "Â" not in valor):
        return valor
    for codificacion in ("cp1252", "latin-1"):
        try:
            return valor.encode(codificacion).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return valor


def reparar_serie(serie):
    """Aplica la corrección solo a los valores únicos (rápido en columnas grandes)."""
    mapa = {u: reparar_codificacion(u) for u in serie.dropna().unique() if isinstance(u, str)}
    return serie.map(lambda v: mapa.get(v, v))


def preparar_fecha(df):
    df = df.copy()
    if "FECHA_HECHO" in df.columns:
        df["FECHA_HECHO"] = pd.to_datetime(df["FECHA_HECHO"], errors="coerce", dayfirst=True)
    else:
        df["FECHA_HECHO"] = pd.NaT
    return df


def preparar_identificacion(df, columna):
    df = df.copy()
    if columna in df.columns:
        df["_ID_CLAVE"] = normalizar_serie_id(df[columna])
    else:
        df["_ID_CLAVE"] = ""
    return df


def formatear_entero(valor):
    return f"{int(round(numero(valor))):,}".replace(",", ".")


def fecha_legible(fecha):
    if pd.isna(fecha):
        return "Fecha no disponible"
    return fecha.strftime("%d/%m/%Y")


def titulo_seccion(texto):
    st.markdown(f'<div class="seccion">{html.escape(texto)}</div>', unsafe_allow_html=True)


def tarjeta(etiqueta, valor, nota="", alto=None):
    estilo = f' style="min-height:{alto}px;"' if alto else ""
    st.markdown(
        f"""
        <div class="tarjeta"{estilo}>
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
        vista = vista.rename(columns={k: v for k, v in nombres.items() if k in vista.columns})
    limite_filas = 2000
    truncada = len(vista) > limite_filas
    st.dataframe(vista.head(limite_filas), width="stretch", hide_index=True)
    if truncada:
        st.caption(f"Se muestran {limite_filas:,} de {len(vista):,} registros.")


@st.cache_resource(show_spinner=False, max_entries=10)
def construir_resumen_funcionarios(_ops, firma, columna_funcionario):
    """Resumen por funcionario. `_ops` no se hashea; `firma` identifica los filtros activos."""
    base = _ops.copy()
    base["FUNCIONARIO"] = (base[columna_funcionario].astype(object).where(
        base[columna_funcionario].notna(), "No registrado"
    ).astype(str).str.strip())
    base["CEDULA"] = (base["IDENTIFICACION"].astype(object).where(
        base["IDENTIFICACION"].notna(), ""
    ).astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
                      if "IDENTIFICACION" in base.columns else "")
    base["ESTACION_RESUMEN"] = (base["ESTACION"].astype(object).where(
        base["ESTACION"].notna(), "No especificada"
    ).astype(str).str.strip()
                                if "ESTACION" in base.columns else "No especificada")
    tipo = (base["TIPO DE CAPTURA"].astype(object).where(
        base["TIPO DE CAPTURA"].notna(), ""
    ).astype(str).str.casefold()
            if "TIPO DE CAPTURA" in base.columns else pd.Series("", index=base.index))
    valor = (pd.to_numeric(base["TOTAL TIPO DE CAPTURA"], errors="coerce").fillna(0)
             if "TOTAL TIPO DE CAPTURA" in base.columns else pd.Series(0, index=base.index))
    base["VALOR_CAPTURA"] = valor
    base["CAPTURAS_FLAGRANCIA"] = valor.where(tipo.str.contains("flagrancia", na=False), 0)
    base["CAPTURAS_ORDEN"] = valor.where(tipo.str.contains("orden judicial", na=False), 0)

    resumen = base.groupby(["FUNCIONARIO", "CEDULA", "ESTACION_RESUMEN"], dropna=False).agg(
        **{
            "Capturas flagrancia": ("CAPTURAS_FLAGRANCIA", "sum"),
            "Capturas orden judicial": ("CAPTURAS_ORDEN", "sum"),
            "Total tipo de captura": ("VALOR_CAPTURA", "sum"),
        }
    ).reset_index()
    resumen = resumen.rename(columns={"FUNCIONARIO": "Grado, nombres y apellidos", "CEDULA": "Cédula",
                                      "ESTACION_RESUMEN": "Estación"}).sort_values(
        ["Total tipo de captura", "Grado, nombres y apellidos"], ascending=[False, True])
    for c in ("Capturas flagrancia", "Capturas orden judicial", "Total tipo de captura"):
        resumen[c] = resumen[c].round(0).astype(int)
    return resumen.reset_index(drop=True)


# ============================================================
# HEADER PRINCIPAL CON RELOJ EN TIEMPO REAL
# ============================================================

import streamlit.components.v1 as components


def header_principal_con_reloj():
    html_reloj = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: transparent; font-family: 'Inter', Arial, sans-serif; overflow: hidden; }
        .header-mebar-container {
            background: linear-gradient(135deg, #0a1628 0%, #1a3a5c 100%);
            border-radius: 12px; padding: 20px 28px; border: 2px solid #2a4a6c;
            border-bottom: 4px solid #C5A45B; box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
            position: relative; overflow: hidden; min-height: 120px; display: flex; align-items: center;
        }
        .header-mebar-container::before {
            content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        }
        .header-mebar-content { display: flex; justify-content: space-between; align-items: center; gap: 20px; width: 100%; flex-wrap: wrap; }
        .header-mebar-text { flex: 1; min-width: 300px; }
        .header-mebar-title { color: #ffffff; font-size: 32px; font-weight: 800; margin: 0 0 6px 0; letter-spacing: 0.5px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        .header-mebar-subtitle { color: #a0b3c8; font-size: 14px; margin: 0; font-weight: 400; }
        .header-mebar-clock { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
        .live-indicator { display: flex; align-items: center; gap: 6px; background: rgba(25, 135, 84, 0.15); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(25, 135, 84, 0.3); }
        .live-dot { width: 8px; height: 8px; background: #198754; border-radius: 50%; animation: pulse-live 2s ease-in-out infinite; box-shadow: 0 0 8px rgba(25, 135, 84, 0.8); }
        @keyframes pulse-live { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(0.95); } }
        .live-text { color: #198754; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
        .clock-time { color: #ffffff; font-size: 28px; font-weight: 700; font-family: 'Courier New', monospace; letter-spacing: 1px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        .clock-date { color: #8b9fb3; font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px; }
        .date-dot { width: 6px; height: 6px; background: #198754; border-radius: 50%; display: inline-block; }
        @media (max-width: 768px) {
            .header-mebar-content { flex-direction: column; align-items: flex-start; }
            .header-mebar-clock { align-items: flex-start; width: 100%; }
            .header-mebar-title, .clock-time { font-size: 24px; }
        }
    </style>
    </head>
    <body>
        <div class="header-mebar-container">
            <div class="header-mebar-content">
                <div class="header-mebar-text">
                    <h1 class="header-mebar-title">PANEL PRINCIPAL MEBAR</h1>
                    <p class="header-mebar-subtitle">Sistema de evaluacion y seguimiento al rendimiento Policial</p>
                </div>
                <div class="header-mebar-clock">
                    <div class="live-indicator"><span class="live-dot"></span><span class="live-text">LIVE</span></div>
                    <div class="clock-time" id="clock-time">--:--:--</div>
                    <div class="clock-date"><span class="date-dot"></span><span id="clock-date">FECHA: --/--/--</span></div>
                </div>
            </div>
        </div>
        <script>
            function updateClock() {
                const now = new Date();
                const timeStr = now.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
                const dateStr = now.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: '2-digit' });
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

@st.cache_resource(show_spinner="Cargando y optimizando información...")
def cargar_y_preparar(pantalla):
    pantalla_normalizada = str(pantalla).strip().casefold()
    es_panel_principal = pantalla_normalizada == "panel principal"
    es_seguimiento = pantalla_normalizada.startswith("seguimiento activ")

    delitos, operatividad = cargar_delitos_operatividad()
    base_tahum = limpiar_dataframe(cargar_tahum())
    tahum = (limpiar_dataframe(cargar_antecedentes_persona())
             if es_panel_principal else pd.DataFrame())
    vehiculos = pd.DataFrame()

    # RNMC: normaliza nombres de columna (quita tildes) y prepara cédula y fecha
    rnmc = pd.DataFrame(columns=["_ID_CLAVE", "FECHA_RNMC"])
    if not rnmc.empty:
        rnmc.columns = [
            re.sub(r"\s+", "_",
                   unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode().strip().upper())
            for c in rnmc.columns
        ]
        rnmc = preparar_identificacion(rnmc, "IDENTIFICACION_POLICIA")
        if "FECHA_HECHOS" in rnmc.columns:
            rnmc["FECHA_RNMC"] = pd.to_datetime(rnmc["FECHA_HECHOS"], errors="coerce", dayfirst=True)
        else:
            rnmc["FECHA_RNMC"] = pd.NaT
    else:
        rnmc = pd.DataFrame(columns=["_ID_CLAVE", "FECHA_RNMC"])

    # TURNOS: cada registro es un turno cumplido por el funcionario
    turnos = (limpiar_dataframe(cargar_turnos())
              if es_seguimiento else pd.DataFrame())
    if not turnos.empty:
        mapa_columnas_turnos = {
            "unidad": "UNIDAD",
            "fechaminuta": "FECHA_TURNO",
            "identificacionempleado": "IDENTIFICACION_TURNO",
            "gradoempleado": "GRADO_TURNO",
            "nombresempleado": "NOMBRES_TURNO",
            "apellidosempleado": "APELLIDOS_TURNO",
            "codigocuadrante": "CODIGO_CUADRANTE",
            "cargosiath": "CARGO_SIATH",
        }
        turnos = turnos.rename(columns={
            c: mapa_columnas_turnos[re.sub(r"[\s_]+", "", c).lower()]
            for c in turnos.columns
            if re.sub(r"[\s_]+", "", c).lower() in mapa_columnas_turnos
        })
        for col in ("UNIDAD", "GRADO_TURNO", "NOMBRES_TURNO", "APELLIDOS_TURNO",
                    "CODIGO_CUADRANTE", "CARGO_SIATH"):
            if col not in turnos.columns:
                turnos[col] = ""
            turnos[col] = turnos[col].astype(object).where(turnos[col].notna(), "").astype(str).str.strip()

        turnos = preparar_identificacion(turnos, "IDENTIFICACION_TURNO")
        if "FECHA_TURNO" in turnos.columns:
            turnos["FECHA_DIA"] = pd.to_datetime(
                turnos["FECHA_TURNO"], errors="coerce", dayfirst=True).dt.normalize()
        else:
            turnos["FECHA_DIA"] = pd.NaT

        turnos["NOMBRE_COMPLETO"] = (
            turnos["GRADO_TURNO"] + " " + turnos["NOMBRES_TURNO"] + " " + turnos["APELLIDOS_TURNO"]
        ).str.replace(r"\s+", " ", regex=True).str.strip()
        # Dos órdenes de texto para que la búsqueda por nombre funcione en ambos sentidos
        turnos["_TEXTO_A"] = turnos["NOMBRE_COMPLETO"].str.casefold()
        turnos["_TEXTO_B"] = (
            turnos["GRADO_TURNO"] + " " + turnos["APELLIDOS_TURNO"] + " " + turnos["NOMBRES_TURNO"]
        ).str.replace(r"\s+", " ", regex=True).str.strip().str.casefold()
    else:
        turnos = pd.DataFrame(columns=["_ID_CLAVE", "FECHA_DIA"])

    # PERMISOS: novedades por funcionario (solo filas donde NO estuvo en servicio)
    permisos = (limpiar_dataframe(cargar_permisos())
                if es_seguimiento else pd.DataFrame())
    if not permisos.empty:
        mapa_columnas_permisos = {
            "unidad": "UNIDAD",
            "fechaminuta": "FECHA_PERMISO",
            "turno": "TURNO",
            "tipominuta": "TIPO_MINUTA",
            "identificacionempleado": "IDENTIFICACION_PERMISO",
            "gradoempleado": "GRADO_PERMISO",
            "nombresempleado": "NOMBRES_PERMISO",
            "apellidosempleado": "APELLIDOS_PERMISO",
            "codigocuadrante": "CODIGO_CUADRANTE",
            "empleadoenservicio": "EN_SERVICIO",
            "descripcionnovedad": "DESCRIPCION_NOVEDAD",
            "cargosiath": "CARGO_SIATH",
            "rolsiath": "ROL_SIATH",
        }
        permisos = permisos.rename(columns={
            c: mapa_columnas_permisos[re.sub(r"[\s_]+", "", c).lower()]
            for c in permisos.columns
            if re.sub(r"[\s_]+", "", c).lower() in mapa_columnas_permisos
        })
        for col in ("UNIDAD", "TURNO", "TIPO_MINUTA", "GRADO_PERMISO", "NOMBRES_PERMISO", "APELLIDOS_PERMISO",
                    "CODIGO_CUADRANTE", "DESCRIPCION_NOVEDAD", "CARGO_SIATH", "ROL_SIATH"):
            if col not in permisos.columns:
                permisos[col] = ""
            permisos[col] = reparar_serie(
                permisos[col].astype(object).where(permisos[col].notna(), "").astype(str).str.strip()
            )

        # Un permiso = fila donde el funcionario NO estuvo en servicio
        if "EN_SERVICIO" in permisos.columns:
            permisos = permisos[permisos["EN_SERVICIO"].astype(str).str.strip().str.upper().eq("NO")]

        permisos = preparar_identificacion(permisos, "IDENTIFICACION_PERMISO")
        permisos = permisos[permisos["_ID_CLAVE"] != ""]
        if "FECHA_PERMISO" in permisos.columns:
            permisos["FECHA_DIA"] = pd.to_datetime(
                permisos["FECHA_PERMISO"], errors="coerce", dayfirst=True).dt.normalize()
        else:
            permisos["FECHA_DIA"] = pd.NaT
    else:
        permisos = pd.DataFrame(columns=["_ID_CLAVE", "FECHA_DIA"])

    # 1. Limpieza básica
    delitos = limpiar_dataframe(delitos)
    operatividad = limpiar_dataframe(operatividad)
    tahum = limpiar_dataframe(tahum)
    base_tahum = limpiar_dataframe(base_tahum)
    vehiculos = limpiar_dataframe(vehiculos)

    delitos = preparar_fecha(delitos)
    operatividad = preparar_fecha(operatividad)

    delitos = preparar_identificacion(delitos, "IDENTIFICACION")
    operatividad = preparar_identificacion(operatividad, "IDENTIFICACION")
    base_tahum = preparar_identificacion(base_tahum, "Identificacion")

    # Cédula del funcionario que hizo la consulta, precalculada una sola vez
    # (evita normalizar tablas enormes cada vez que se abre el modal de antecedentes).
    def _precalcular_id_funcionario(df):
        col = next(
            (c for c in df.columns
             if ("CCFuncionario" in c or "Funcionario" in c or "Cedula" in c or "Identificacion" in c)
             and "Fisica" not in c),
            None,
        )
        df["_ID_FUNC"] = normalizar_serie_id(df[col]) if col else ""

    for _df in (tahum, vehiculos):
        if not _df.empty:
            _precalcular_id_funcionario(_df)

    for df in (delitos, operatividad, tahum, vehiculos):
        if "_ID_CLAVE" not in df.columns:
            df["_ID_CLAVE"] = ""

    # 2. Preparar funcionarios de TAHUM tolerando columnas opcionales ausentes.
    columnas_funcionario = [
        "_ID_CLAVE", "GR", "APELLIDOS Y NOMBRES", "TIEMPO_UNIDAD", "TIEMPO_CARGO"
    ]
    if not base_tahum.empty and "_ID_CLAVE" in base_tahum.columns:
        base_funcionarios = base_tahum.copy()
        for columna in columnas_funcionario:
            if columna not in base_funcionarios.columns:
                base_funcionarios[columna] = ""
        base_funcionarios = base_funcionarios[columnas_funcionario].copy()
        base_funcionarios = base_funcionarios.rename(columns={
            "GR": "GRADO",
            "APELLIDOS Y NOMBRES": "NOMBRE_TAHUM",
        })
        for columna in ["GRADO", "NOMBRE_TAHUM", "TIEMPO_UNIDAD", "TIEMPO_CARGO"]:
            base_funcionarios[columna] = (
                base_funcionarios[columna].astype(object).where(
                    base_funcionarios[columna].notna(), ""
                ).astype(str).str.strip()
            )
        base_funcionarios = base_funcionarios[
            base_funcionarios["_ID_CLAVE"].astype(str).str.strip().ne("")
        ].drop_duplicates(subset=["_ID_CLAVE"], keep="first")
    else:
        base_funcionarios = pd.DataFrame(
            columns=["_ID_CLAVE", "GRADO", "NOMBRE_TAHUM", "TIEMPO_UNIDAD", "TIEMPO_CARGO"]
        )

    # Se calcula una sola vez la clave usada para cruzar consultas de antecedentes.
    if "FuncionarioFisica" in tahum.columns:
        tahum["_ID_CLAVE_ANT"] = normalizar_serie_id(tahum["FuncionarioFisica"])
    else:
        tahum["_ID_CLAVE_ANT"] = ""

    # 3. Extraer reportes (vectorizado)
    registros_list = []
    for df, col_nom in [(delitos, "GR APELLIDOS Y NOMBRES POLICIA_1"),
                        (operatividad, "GR APELLIDOS Y NOMBRES POLICIA_1")]:
        if col_nom in df.columns:
            cols_to_keep = ["_ID_CLAVE", col_nom]
            if "ESTACION" in df.columns:
                cols_to_keep.append("ESTACION")

            temp_df = df[cols_to_keep].copy()
            temp_df = temp_df.rename(columns={col_nom: "NOMBRE_REPORTE"})

            temp_df["_ID_CLAVE"] = temp_df["_ID_CLAVE"].astype(object).where(
                temp_df["_ID_CLAVE"].notna(), "").astype(str).str.strip()
            temp_df["NOMBRE_REPORTE"] = temp_df["NOMBRE_REPORTE"].astype(object).where(
                temp_df["NOMBRE_REPORTE"].notna(), "").astype(str).str.strip()
            if "ESTACION" in temp_df.columns:
                temp_df["ESTACION"] = temp_df["ESTACION"].astype(object).where(
                    temp_df["ESTACION"].notna(), "").astype(str).str.strip()

            temp_df = temp_df[temp_df["_ID_CLAVE"] != ""].drop_duplicates(subset=["_ID_CLAVE"], keep="first")
            registros_list.append(temp_df)

    if registros_list:
        base_reportes = pd.concat(registros_list, ignore_index=True).drop_duplicates(subset=["_ID_CLAVE"], keep="first")
    else:
        base_reportes = pd.DataFrame(columns=["_ID_CLAVE", "NOMBRE_REPORTE", "ESTACION"])

    # 4. Unir maestros
    universo_ids = set(base_reportes["_ID_CLAVE"].dropna().astype(str).tolist())
    universo_ids.update(base_funcionarios["_ID_CLAVE"].dropna().astype(str).tolist())
    universo_ids.discard("")

    maestros = pd.DataFrame({"_ID_CLAVE": sorted(list(universo_ids))})

    if not base_reportes.empty:
        maestros = maestros.merge(base_reportes, on="_ID_CLAVE", how="left")
    if not base_funcionarios.empty:
        maestros = maestros.merge(base_funcionarios, on="_ID_CLAVE", how="left")

    for col in ["NOMBRE_REPORTE", "NOMBRE_TAHUM", "ESTACION", "GRADO", "TIEMPO_UNIDAD", "TIEMPO_CARGO"]:
        if col not in maestros:
            maestros[col] = ""

    maestros["NOMBRE_TAHUM"] = maestros["NOMBRE_TAHUM"].fillna("").astype(str)
    maestros["NOMBRE_REPORTE"] = maestros["NOMBRE_REPORTE"].fillna("").astype(str)
    maestros["NOMBRE"] = maestros["NOMBRE_TAHUM"].where(maestros["NOMBRE_TAHUM"].str.strip() != "",
                                                        maestros["NOMBRE_REPORTE"])
    maestros["NOMBRE"] = maestros["NOMBRE"].fillna("").astype(str).str.strip()
    maestros["ESTACION"] = maestros["ESTACION"].fillna("").astype(str).str.strip()
    maestros["GRADO"] = maestros["GRADO"].fillna("").astype(str).str.strip()

    return delitos, operatividad, tahum, vehiculos, maestros, rnmc, turnos, permisos


def _precalcular_id_funcionario(df):
    """Precalcula la identificación del funcionario para filtrar antecedentes."""
    col = next(
        (c for c in df.columns
         if ("CCFuncionario" in c or "Funcionario" in c or "Cedula" in c or "Identificacion" in c)
         and "Fisica" not in c),
        None,
    )
    df["_ID_FUNC"] = normalizar_serie_id(df[col]) if col else ""


def _asegurar_antecedentes_bajo_demanda():
    """Carga antecedentes solo cuando se abre el diálogo correspondiente."""
    global tahum, vehiculos
    if tahum.empty:
        tahum = limpiar_dataframe(cargar_antecedentes_persona())
        _precalcular_id_funcionario(tahum)
        tahum["_ID_CLAVE_ANT"] = normalizar_serie_id(
            tahum["FuncionarioFisica"]
            if "FuncionarioFisica" in tahum.columns
            else pd.Series("", index=tahum.index, dtype="string")
        )
    if vehiculos.empty:
        vehiculos = limpiar_dataframe(cargar_antecedentes_vehiculo())
        _precalcular_id_funcionario(vehiculos)


def _asegurar_rnmc_bajo_demanda():
    """Carga y prepara RNMC únicamente al abrir el diálogo de comparendos."""
    global rnmc
    if not rnmc.empty and "FECHA_RNMC" in rnmc.columns:
        return
    rnmc = limpiar_dataframe(cargar_rnmc())
    if rnmc.empty:
        rnmc = pd.DataFrame(columns=["_ID_CLAVE", "FECHA_RNMC"])
        return
    rnmc.columns = [
        re.sub(r"\s+", "_",
               unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode().strip().upper())
        for c in rnmc.columns
    ]
    rnmc = preparar_identificacion(rnmc, "IDENTIFICACION_POLICIA")
    rnmc["FECHA_RNMC"] = (pd.to_datetime(rnmc["FECHA_HECHOS"], errors="coerce", dayfirst=True)
                           if "FECHA_HECHOS" in rnmc.columns else pd.NaT)


# ============================================================
# MENÚ LATERAL Y FILTROS
# ============================================================

with st.sidebar:
    ruta_logo = BASE_DIR / "assets" / "LOGO_OFICINA.png"
    if ruta_logo.exists():
        st.image(str(ruta_logo), width="stretch")

    st.markdown(
        """
        <div style="text-align:left; padding:16px 18px; margin-top:12px; font-family:'Inter', Arial, sans-serif; border-left:3px solid #C5A45B; background:rgba(255,255,255,0.04); border-radius:0 8px 8px 0;">
            <div style="font-size:12px; font-weight:600; letter-spacing:1.5px; color:#FFFFFF; margin-bottom:8px; text-transform:uppercase;">PANEL DE INFORMACIÓN</div>
            <div style="font-size:11px; font-weight:400; font-style:italic; line-height:1.6; color:#B8C9DC; letter-spacing:0.3px;">
                Permite navegar entre módulos (Panel Principal, Gestión Operativa, Registro Delictivo y Seguimiento activación al servicio) y filtrar o buscar información por periodos, estaciones, grados o funcionarios para actualizar el dashboard.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### NAVEGACIÓN")
    pantalla = st.radio("Selecciona una pantalla",
                        ["Panel principal", "Gestión Operativa", "Registro Delictivo",
                         "Seguimiento activación al servicio"],
                        label_visibility="collapsed")

    inicio_carga = perf_counter()
    try:
        delitos, operatividad, tahum, vehiculos, maestros, rnmc, turnos, permisos = cargar_y_preparar(pantalla)
    except Exception as error:
        st.error("No fue posible cargar los archivos de informaciÃ³n.")
        st.exception(error)
        st.stop()
    tiempo_carga = perf_counter() - inicio_carga

    st.markdown("---")
    st.markdown("### FILTROS GENERALES")

    fechas = pd.concat(
        [delitos["FECHA_HECHO"].dropna(), operatividad["FECHA_HECHO"].dropna()],
        ignore_index=True,
    )
    if not fechas.empty:
        fecha_min = fechas.min().date()
        fecha_max = fechas.max().date()
        rango_fechas = st.date_input("Periodo de consulta", value=(fecha_min, fecha_max), min_value=fecha_min,
                                     max_value=fecha_max, format="DD/MM/YYYY")
        if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
            inicio, fin = rango_fechas
        elif isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 1:
            inicio = fin = rango_fechas[0]
        else:
            inicio = fin = rango_fechas
    else:
        inicio, fin = None, None
        st.warning("No se encontraron fechas válidas en los reportes.")

    estaciones = set()
    for df in (delitos, operatividad):
        if "ESTACION" in df.columns:
            estaciones.update(df["ESTACION"].dropna().astype(str).str.strip().tolist())
    estaciones = sorted(x for x in estaciones if x and x.lower() != "nan")
    estaciones_sel = st.multiselect("Estación", options=estaciones, default=[], placeholder="Todas las estaciones")

    grados = sorted(x for x in maestros.get("GRADO", pd.Series(dtype=str)).dropna().astype(str).str.strip().unique() if
                    x and x.lower() != "nan")
    grados_sel = st.multiselect("Grado", options=grados, default=[], placeholder="Todos los grados")

    st.markdown("### BÚSQUEDA DE FUNCIONARIOS")
    cedula_busqueda = st.text_input("Buscar por cédula", placeholder="Escribe el número de identificación",
                                    key="filtro_cedula").strip()
    nombre_busqueda = st.text_input("Grados, nombres y apellidos", placeholder="Ej. SI Alexander Ruiz",
                                    key="filtro_nombre_funcionario").strip().casefold()

    st.markdown("---")
    st.caption("Los filtros se aplican a las pantallas y gráficos del dashboard.")
    st.caption("MEBAR · Análisis de información")
    st.caption(f"⏱ Carga de datos: {tiempo_carga:.1f}s")


# ============================================================
# INDICADORES Y AGREGADOS POR FUNCIONARIO
# ============================================================

def agregar_funcionarios(base, df_delitos, df_operatividad):
    base = base.copy()
    if base.empty:
        return base

    if not df_delitos.empty:
        casos = df_delitos.groupby("_ID_CLAVE", dropna=False).agg(
            CASOS=("CANTIDAD CASOS", "sum") if "CANTIDAD CASOS" in df_delitos.columns else ("_ID_CLAVE", "size"),
            VICTIMAS=("CANTIDAD VICTIMA", "sum") if "CANTIDAD VICTIMA" in df_delitos.columns else ("_ID_CLAVE", "size"),
        ).reset_index()
    else:
        casos = pd.DataFrame(columns=["_ID_CLAVE", "CASOS", "VICTIMAS"])

    if not df_operatividad.empty:
        df_operatividad = df_operatividad.copy()
        if "TOTAL TIPO DE CAPTURA" in df_operatividad.columns:
            df_operatividad["TOTAL TIPO DE CAPTURA"] = pd.to_numeric(df_operatividad["TOTAL TIPO DE CAPTURA"],
                                                                     errors="coerce").fillna(0)
        ops_agregadas = df_operatividad.groupby("_ID_CLAVE", dropna=False).agg(
            TOTAL_TIPO_CAPTURA=("TOTAL TIPO DE CAPTURA",
                                "sum") if "TOTAL TIPO DE CAPTURA" in df_operatividad.columns else ("_ID_CLAVE",
                                                                                                   lambda serie: 0),
            ACTIVIDADES=("TOTAL ACTIVIDAD OPERATIVA",
                         "sum") if "TOTAL ACTIVIDAD OPERATIVA" in df_operatividad.columns else ("_ID_CLAVE", "size"),
        ).reset_index()
    else:
        ops_agregadas = pd.DataFrame(columns=["_ID_CLAVE", "TOTAL_TIPO_CAPTURA", "ACTIVIDADES"])

    base = base.drop(columns=["CASOS", "VICTIMAS", "CAPTURAS", "TOTAL_TIPO_CAPTURA", "ACTIVIDADES"], errors="ignore")
    base = base.merge(casos, on="_ID_CLAVE", how="left").merge(ops_agregadas, on="_ID_CLAVE", how="left")

    for columna in ["CASOS", "VICTIMAS", "TOTAL_TIPO_CAPTURA", "ACTIVIDADES"]:
        base[columna] = pd.to_numeric(base.get(columna, 0), errors="coerce").fillna(0)
    return base


def agregar_consultas_antecedentes(base, df_antecedentes):
    base = base.copy()
    if df_antecedentes.empty or base.empty:
        base["CONSULTAS_ANTECEDENTES"] = 0
        base["ANTECEDENTES_ENCONTRADOS"] = 0
        return base

    if "_ID_CLAVE_ANT" not in df_antecedentes.columns:
        if "FuncionarioFisica" not in df_antecedentes.columns:
            base["CONSULTAS_ANTECEDENTES"] = 0
            base["ANTECEDENTES_ENCONTRADOS"] = 0
            return base
        df_antecedentes = df_antecedentes.copy()
        df_antecedentes["_ID_CLAVE_ANT"] = normalizar_serie_id(df_antecedentes["FuncionarioFisica"])

    if "_ID_CLAVE_ANT" in df_antecedentes.columns:
        consultas = df_antecedentes.groupby("_ID_CLAVE_ANT", dropna=False).size().reset_index(
            name="CONSULTAS_ANTECEDENTES")
        if "TieneAnt" in df_antecedentes.columns:
            con_antecedentes = df_antecedentes[df_antecedentes["TieneAnt"].astype(str).str.upper() == "SI"].groupby(
                "_ID_CLAVE_ANT", dropna=False).size().reset_index(name="ANTECEDENTES_ENCONTRADOS")
            consultas = consultas.merge(con_antecedentes, on="_ID_CLAVE_ANT", how="left")
            consultas["ANTECEDENTES_ENCONTRADOS"] = consultas["ANTECEDENTES_ENCONTRADOS"].fillna(0).astype(int)
        else:
            consultas["ANTECEDENTES_ENCONTRADOS"] = 0
        base = base.merge(consultas, left_on="_ID_CLAVE", right_on="_ID_CLAVE_ANT", how="left")
        base["CONSULTAS_ANTECEDENTES"] = pd.to_numeric(base["CONSULTAS_ANTECEDENTES"], errors="coerce").fillna(
            0).astype(int)
        if "_ID_CLAVE_ANT" in base.columns:
            base = base.drop(columns=["_ID_CLAVE_ANT"])
    else:
        base["CONSULTAS_ANTECEDENTES"] = 0
        base["ANTECEDENTES_ENCONTRADOS"] = 0
    return base


def perfil_funcionario(id_clave):
    registro = maestros[maestros["_ID_CLAVE"] == id_clave]
    return registro.iloc[0] if not registro.empty else None


def crear_indice_ultimo_registro(df):
    """Índice vectorizado (sin iterrows): último registro fechado por identificación."""
    if df.empty or "_ID_CLAVE" not in df.columns or "FECHA_HECHO" not in df.columns:
        return pd.DataFrame()
    validos = df.dropna(subset=["FECHA_HECHO"])
    validos = validos[validos["_ID_CLAVE"].astype(str).str.strip().ne("")]
    if validos.empty:
        return pd.DataFrame()
    ultimos = validos.sort_values("FECHA_HECHO", kind="stable").drop_duplicates("_ID_CLAVE", keep="last")
    return ultimos.set_index("_ID_CLAVE", drop=False)


@st.cache_resource(show_spinner="Aplicando filtros...", max_entries=10)
def calcular_vista(inicio, fin, estaciones_sel, grados_sel, cedula_busqueda, nombre_busqueda):
    """Se recalcula solo cuando cambian los filtros, no en cada clic.

    Los DataFrames devueltos se comparten entre reruns: NO modificarlos in-place
    (siempre usar .copy() antes de escribir en ellos).
    """
    maestros_f = maestros.copy()
    if estaciones_sel:
        maestros_f = maestros_f[maestros_f["ESTACION"].isin(estaciones_sel)]
    if grados_sel:
        maestros_f = maestros_f[maestros_f["GRADO"].isin(grados_sel)]
    if cedula_busqueda:
        maestros_f = maestros_f[
            maestros_f["_ID_CLAVE"].astype(str).str.contains(re.escape(normalizar_id(cedula_busqueda)), na=False)]
    if nombre_busqueda:
        # Convert to pandas' nullable string dtype before filling nulls. This
        # also works when the source columns arrive as categorical data.
        texto = (maestros_f["GRADO"].astype("string").fillna("") + " " +
                 maestros_f["NOMBRE"].astype("string").fillna("")).str.casefold()
        maestros_f = maestros_f[texto.str.contains(re.escape(nombre_busqueda), na=False)]

    ids_visibles = set(maestros_f["_ID_CLAVE"].astype(str))
    filtrar_ids = bool(cedula_busqueda or nombre_busqueda or grados_sel)

    def aplicar(df):
        mask = pd.Series(True, index=df.index)
        if inicio is not None and fin is not None:
            f = df["FECHA_HECHO"]
            mask &= f.isna() | ((f >= pd.Timestamp(inicio)) & (f < pd.Timestamp(fin) + pd.Timedelta(days=1)))
        if estaciones_sel and "ESTACION" in df.columns:
            mask &= df["ESTACION"].astype(str).str.strip().isin(estaciones_sel)
        if filtrar_ids:
            mask &= df["_ID_CLAVE"].astype(str).isin(ids_visibles)
        return df[mask]

    delitos_f = aplicar(delitos)
    operatividad_f = aplicar(operatividad)

    if "DELITO" in delitos_f.columns:
        delitos_homicidios = delitos_f[
            delitos_f["DELITO"].astype("string").fillna("").str.contains(
                r"\bhomicidio\b", case=False, regex=True, na=False
            )
        ].copy()
    else:
        delitos_homicidios = delitos_f.iloc[0:0].copy()

    ranking = agregar_funcionarios(maestros_f, delitos_f, operatividad_f)
    ranking = agregar_consultas_antecedentes(ranking, tahum)
    ranking_homicidios = agregar_funcionarios(maestros_f, delitos_homicidios, operatividad_f.iloc[0:0].copy())

    return (maestros_f, delitos_f, operatividad_f, delitos_homicidios,
            ranking, ranking_homicidios,
            crear_indice_ultimo_registro(delitos_f),
            crear_indice_ultimo_registro(operatividad_f))


(maestros_f, delitos_f, operatividad_f, delitos_homicidios,
 ranking, ranking_homicidios,
 INDICE_ULTIMO_DELITO, INDICE_ULTIMA_OPERATIVIDAD) = calcular_vista(
    inicio, fin, tuple(estaciones_sel), tuple(grados_sel), cedula_busqueda, nombre_busqueda
)


def obtener_ultimo_registro(df, id_clave):
    """Recupera el último registro sin ordenar la tabla en cada consulta."""
    clave = str(id_clave)
    if df is delitos_f:
        idx = INDICE_ULTIMO_DELITO
        return idx.loc[clave] if clave in idx.index else None
    if df is operatividad_f:
        idx = INDICE_ULTIMA_OPERATIVIDAD
        return idx.loc[clave] if clave in idx.index else None
    if "_ID_CLAVE" not in df.columns or "FECHA_HECHO" not in df.columns:
        return None
    registros = df.loc[
        (df["_ID_CLAVE"].astype(str) == clave) & df["FECHA_HECHO"].notna()
    ]
    if registros.empty:
        return None
    return registros.loc[registros["FECHA_HECHO"].idxmax()]


def obtener_tipos_captura(id_clave):
    registros = operatividad_f[operatividad_f["_ID_CLAVE"] == id_clave].copy()
    if registros.empty or "TIPO DE CAPTURA" not in registros.columns:
        return "Sin tipos registrados"
    if "TOTAL TIPO DE CAPTURA" in registros.columns:
        registros["TOTAL TIPO DE CAPTURA"] = pd.to_numeric(registros["TOTAL TIPO DE CAPTURA"], errors="coerce").fillna(
            0)
        resumen = registros.groupby("TIPO DE CAPTURA")["TOTAL TIPO DE CAPTURA"].sum().sort_values(ascending=False)
    else:
        resumen = registros["TIPO DE CAPTURA"].value_counts()
    resumen = resumen[resumen.index.notna() & (resumen.index.astype(str).str.strip() != "")]
    return " · ".join(f"{nombre}: {formatear_entero(total)}" for nombre, total in
                      resumen.head(2).items()) if not resumen.empty else "Sin tipos registrados"


def tarjeta_funcionario(fila, metrica, categoria, posicion):
    id_clave = str(fila["_ID_CLAVE"])
    nombre = str(fila.get("NOMBRE", "") or "Nombre no registrado")
    grado = str(fila.get("GRADO", "") or "Grado no registrado")
    estacion = str(fila.get("ESTACION", "") or "Estación no registrada")

    ultimo_delito = obtener_ultimo_registro(delitos_f, id_clave)
    ultimo_operativo = obtener_ultimo_registro(operatividad_f, id_clave)

    if categoria == "capturas":
        fecha_ultimo = fecha_legible(
            ultimo_operativo["FECHA_HECHO"]) if ultimo_operativo is not None else "Sin fecha disponible"
        etiqueta_fecha = "Último registro operativo"
        detalle = obtener_tipos_captura(id_clave)
    elif categoria == "homicidios":
        hf = delitos_homicidios[delitos_homicidios["_ID_CLAVE"] == id_clave]
        fecha_ultimo = fecha_legible(hf["FECHA_HECHO"].max()) if not hf.empty else "Sin fecha disponible"
        etiqueta_fecha = "Último homicidio registrado"
        detalle = "Casos de homicidio asociados"
    else:
        fecha_ultimo = fecha_legible(
            ultimo_delito["FECHA_HECHO"]) if ultimo_delito is not None else "Sin fecha disponible"
        etiqueta_fecha = "Último delito registrado"
        detalle = "Casos delictivos asociados"

    cantidad = formatear_entero(fila.get(metrica, 0))
    color_borde = "#9F1239" if categoria in ("delitos", "homicidios") else "#C5A45B"
    color_icono = "#FCE7EF" if categoria in ("delitos", "homicidios") else "#EAF1F8"
    color_texto = "#76112F" if categoria in ("delitos", "homicidios") else "#12345A"
    fondo_metrica = "#FFF1F5" if categoria in ("delitos", "homicidios") else "#F4F7FB"

    st.markdown(
        f"""
        <div style="background:#FFFFFF;border:1px solid #E8D4DB;border-radius:15px;padding:17px;min-height:220px;box-shadow:0 4px 14px rgba(18,52,90,0.06);border-top:4px solid {color_borde};">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="min-width:48px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;background:{color_icono};border-radius:13px;font-size:27px;">👮</div>
                <div style="min-width:0;">
                    <div style="color:#9A7937;font-size:10px;font-weight:800;letter-spacing:1px;">PUESTO #{posicion}</div>
                    <div style="color:{color_texto};font-size:15px;font-weight:800;line-height:1.35;overflow-wrap:anywhere;">{html.escape(grado)} {html.escape(nombre)}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px;">
                <div><div style="font-size:10px;color:#64748B;">IDENTIFICACIÓN</div><div style="font-size:12px;color:#233247;font-weight:700;">{html.escape(id_clave)}</div></div>
                <div><div style="font-size:10px;color:#64748B;">ESTACIÓN</div><div style="font-size:12px;color:#233247;font-weight:700;">{html.escape(estacion)}</div></div>
            </div>
            <div style="background:{fondo_metrica};border-radius:10px;padding:12px;margin-top:13px;">
                <div style="font-size:11px;color:#64748B;">{html.escape(detalle)}</div>
                <div style="font-size:27px;font-weight:800;color:{color_texto};margin-top:2px;">{html.escape(cantidad)}</div>
                <div style="font-size:11px;color:#334155;font-weight:600;margin-top:5px;">{html.escape(etiqueta_fecha)}: {html.escape(fecha_ultimo)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<a href="?ficha={id_clave}" target="_blank" rel="noopener noreferrer" style="display:block;text-align:center;text-decoration:none;background:#12345A;color:#FFFFFF;font-weight:700;padding:11px 14px;border-radius:9px;margin-top:10px;">Ver ficha completa ↗</a>',
        unsafe_allow_html=True)


def mostrar_ranking_tarjetas(df, metrica, categoria, titulo_vacio):
    if df.empty or metrica not in df.columns or df[metrica].sum() <= 0:
        st.info(titulo_vacio)
        return
    columnas_orden = [metrica]
    if "NOMBRE" in df.columns:
        columnas_orden.append("NOMBRE")
    top = df.sort_values(columnas_orden, ascending=[False] + ([True] if len(columnas_orden) > 1 else [])).head(
        10).reset_index(drop=True)
    izquierda, derecha = st.columns(2, gap="medium")
    for indice, (_, fila) in enumerate(top.iterrows()):
        with (izquierda if indice % 2 == 0 else derecha):
            tarjeta_funcionario(fila=fila, metrica=metrica, categoria=categoria, posicion=indice + 1)
            st.write("")


# ============================================================
# VENTANA EMERGENTE (MODAL) DE ANTECEDENTES - PERSONAS + VEHÍCULOS
# ============================================================

@st.dialog("📋 Detalle de Antecedentes", width="medium")
def mostrar_dialogo_antecedentes(id_clave, nombre_funcionario):
    _asegurar_antecedentes_bajo_demanda()
    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] { background: #0F172A !important; }
        div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3, div[data-testid="stDialog"] span, div[data-testid="stDialog"] label { color: #FFFFFF !important; font-weight: 700 !important; }
        div[data-testid="stDialog"] .stMetric { background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%) !important; border: 2px solid #E2E8F0 !important; border-radius: 12px !important; padding: 16px !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important; }
        div[data-testid="stDialog"] .stMetric label { color: #1E293B !important; font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
        div[data-testid="stDialog"] .stMetric [data-testid="stMetricValue"] { color: #0F172A !important; font-size: 32px !important; font-weight: 800 !important; }
        div[data-testid="stDialog"] hr { border-color: #334155 !important; opacity: 0.5 !important; }
        div[data-testid="stDialog"] .stAlert { background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%) !important; border: 2px solid #0EA5E9 !important; border-radius: 10px !important; color: #0C4A6E !important; }
        div[data-testid="stDialog"] .stAlert * { color: #0C4A6E !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%); padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; border-left: 5px solid #F59E0B; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);">
            <div style="color: #FFFFFF; font-size: 17px; font-weight: 800; margin-bottom: 8px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">👮 {html.escape(nombre_funcionario)}</div>
            <div style="color: #BFDBFE; font-size: 14px; font-weight: 600;">
                <span style="color: #FCD34D; font-weight: 700;">🆔 Identificación:</span> 
                <span style="background: rgba(251, 191, 36, 0.25); padding: 3px 10px; border-radius: 6px; font-family: 'Courier New', monospace; font-weight: 700; color: #FEF3C7;">{html.escape(str(id_clave))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    def buscar_funcionario_en_df(df):
        # Usa la cédula precalculada (_ID_FUNC) en lugar de normalizar toda la tabla.
        if "_ID_FUNC" not in df.columns:
            return df.iloc[0:0]
        return df[df["_ID_FUNC"] == normalizar_id(str(id_clave))]

    def mostrar_cuadricula_meses(df_filtrado, titulo):
        if df_filtrado.empty or "MES_CONSULTA" not in df_filtrado.columns:
            return
        st.markdown(f"### {titulo}")
        orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE",
                       "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        consultas_por_mes = df_filtrado["MES_CONSULTA"].value_counts().to_dict()
        filas_meses = [orden_meses[0:4], orden_meses[4:8], orden_meses[8:12]]
        for fila in filas_meses:
            cols = st.columns(4, gap="small")
            for i, mes in enumerate(fila):
                cantidad = consultas_por_mes.get(mes, 0)
                with cols[i]:
                    if cantidad > 0:
                        bg_color, border_color, text_color, num_color = "linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%)", "#3B82F6", "#FFFFFF", "#60A5FA"
                    else:
                        bg_color, border_color, text_color, num_color = "rgba(255, 255, 255, 0.03)", "#334155", "#64748B", "#475569"
                    st.markdown(
                        f"""
                        <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; padding: 10px 8px; text-align: center; min-height: 65px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                            <div style="color: {text_color}; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 5px;">📆 {mes}</div>
                            <div style="color: {num_color}; font-size: 16px; font-weight: 800;">{cantidad}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        st.divider()

    st.markdown("## 🧍 Consultas a Personas")
    total_persona, con_ant_persona = 0, 0
    if not tahum.empty and "_ID_FUNC" in tahum.columns:
        persona_filtrada = buscar_funcionario_en_df(tahum)
        total_persona = len(persona_filtrada)
        if "TieneAnt" in persona_filtrada.columns:
            con_ant_persona = len(persona_filtrada[persona_filtrada["TieneAnt"].astype(str).str.upper() == "SI"])
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total Consultas", total_persona)
        with col2:
            st.metric("⚠️ Con Antecedentes", con_ant_persona)
        st.divider()
        mostrar_cuadricula_meses(persona_filtrada, "📅 Consultas a personas por mes")
    else:
        st.info("No hay registros de antecedentes de persona.")

    st.markdown("## 🚗 Consultas a Vehículos")
    total_vehiculo, carros, motos, otros_veh = 0, 0, 0, 0
    if not vehiculos.empty and "_ID_FUNC" in vehiculos.columns:
        vehiculo_filtrado = buscar_funcionario_en_df(vehiculos)
        total_vehiculo = len(vehiculo_filtrado)
        if "Clase" in vehiculo_filtrado.columns:
            clase_upper = vehiculo_filtrado["Clase"].astype(str).str.upper()
            carros = len(clase_upper[clase_upper.str.contains("CARRO", na=False)])
            motos = len(clase_upper[clase_upper.str.contains("MOTO", na=False)])
            otros_veh = max(0, total_vehiculo - carros - motos)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🚗 Total Vehículos", total_vehiculo)
        with col2:
            st.metric("🚙 Carros", carros)
        with col3:
            st.metric("🏍️ Motos", motos)
        with col4:
            st.metric("📋 Otros", otros_veh)
        st.divider()
        mostrar_cuadricula_meses(vehiculo_filtrado, "📅 Consultas a vehículos por mes")
    else:
        st.info("No hay registros de antecedentes de vehículos.")

    total_general = total_persona + total_vehiculo
    st.markdown("## 📊 Resumen Total de Consultas")
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); padding: 18px 22px; border-radius: 12px; margin-top: 12px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); text-align: center;">
            <div style="color: #FEF3C7; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">TOTAL DE CONSULTAS REALIZADAS</div>
            <div style="color: #FFFFFF; font-size: 42px; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{total_general:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); border: 2px solid #0EA5E9; border-radius: 10px; padding: 16px 18px; margin-top: 16px; box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);">
            <div style="color: #0369A1; font-size: 14px; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;"><span style="font-size: 16px;">📌</span> Información disponible</div>
            <div style="color: #0C4A6E; font-size: 13px; line-height: 1.6; font-weight: 500;">Esta sección muestra el detalle completo de las consultas de antecedentes realizadas por el funcionario, incluyendo personas y vehículos (carros y motos), desglosado por mes.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# VENTANA EMERGENTE (MODAL) DE COMPARENDOS RNMC
# ============================================================

def obtener_rnmc_funcionario(id_clave):
    if rnmc.empty or "_ID_CLAVE" not in rnmc.columns:
        return rnmc.iloc[0:0]
    return rnmc[rnmc["_ID_CLAVE"] == normalizar_id(str(id_clave))]


@st.dialog("📄 Comparendos RNMC", width="large")
def mostrar_dialogo_rnmc(id_clave, nombre_funcionario):
    _asegurar_rnmc_bajo_demanda()
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #12345A 0%, #1D4C78 100%); padding: 18px 22px; border-radius: 12px; margin-bottom: 18px; border-left: 5px solid #C5A45B; box-shadow: 0 4px 12px rgba(18,52,90,0.25);">
            <div style="color: #FFFFFF; font-size: 17px; font-weight: 800; margin-bottom: 6px;">👮 {html.escape(nombre_funcionario)}</div>
            <div style="color: #D6E2F0; font-size: 13px; font-weight: 600;">🆔 Identificación: {html.escape(str(id_clave))} · Comparendos del Registro Nacional de Medidas Correctivas (RNMC)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    registros = obtener_rnmc_funcionario(id_clave)
    if registros.empty:
        st.info("No se encontraron comparendos RNMC registrados para este funcionario.")
        return

    registros = registros.sort_values("FECHA_RNMC", ascending=False, na_position="last")
    total = len(registros)
    articulos = registros["ARTICULO"].nunique() if "ARTICULO" in registros.columns else 0
    ultima = registros["FECHA_RNMC"].max()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("📋 Total comparendos RNMC", f"{total:,}".replace(",", "."))
    with m2:
        st.metric("⚖️ Artículos distintos", articulos)
    with m3:
        st.metric("📅 Último comparendo", fecha_legible(ultima) if pd.notna(ultima) else "Sin fecha")

    con_fecha = registros.dropna(subset=["FECHA_RNMC"])
    if not con_fecha.empty:
        st.markdown("### 📅 Comparendos por mes")
        mensual = con_fecha.groupby(con_fecha["FECHA_RNMC"].dt.to_period("M").astype(str)).size().reset_index()
        mensual.columns = ["MES", "COMPARENDOS"]
        fig = px.bar(mensual, x="MES", y="COMPARENDOS", text="COMPARENDOS",
                     color_discrete_sequence=[AZUL],
                     labels={"MES": "Mes", "COMPARENDOS": "Comparendos"})
        mostrar_grafico(estilizar_grafico(fig, altura_minima=320))

    if "ARTICULO" in registros.columns:
        st.markdown("### ⚖️ Comparendos por artículo")
        por_articulo = (registros["ARTICULO"].astype("string").fillna("No especificado").str.strip()
                        .value_counts().reset_index())
        por_articulo.columns = ["Artículo", "Comparendos"]
        st.dataframe(por_articulo, width="stretch", hide_index=True)

    st.markdown("### 🗂️ Detalle de comparendos")
    detalle = registros.copy()
    detalle["FECHA"] = detalle["FECHA_RNMC"].dt.strftime("%d/%m/%Y").fillna("")
    columnas_detalle = ["FECHA", "HORA_HECHOS", "DIA_HECHOS", "ESTACION", "LUGAR", "UNIDAD_LABORA_POL",
                        "ARTICULO", "COMPORTAMIENTO"]
    existentes = [c for c in columnas_detalle if c in detalle.columns]
    vista = detalle[existentes].fillna("").astype(str).rename(columns={
        "HORA_HECHOS": "HORA", "DIA_HECHOS": "DÍA", "ESTACION": "ESTACIÓN",
        "UNIDAD_LABORA_POL": "UNIDAD", "ARTICULO": "ARTÍCULO",
    })
    st.dataframe(vista, width="stretch", hide_index=True)
    st.caption("Se muestran todos los comparendos del archivo REPORTE_RNMC para este funcionario (sin filtro de periodo).")


def mostrar_perfil(id_clave):
    funcionario = perfil_funcionario(id_clave)
    if funcionario is None:
        st.warning("No fue posible localizar la ficha del funcionario.")
        return

    nombre = str(funcionario.get("NOMBRE", "") or "Nombre no registrado")
    grado = str(funcionario.get("GRADO", "") or "Grado no registrado")
    estacion = str(funcionario.get("ESTACION", "") or "Estación no registrada")
    nombre_completo = f"{grado} {nombre}".strip()

    st.markdown(
        f"""
        <div class="perfil">
            <div class="perfil-nombre">👮 {html.escape(nombre_completo)}</div>
            <div class="perfil-sub">Identificación: {html.escape(str(id_clave))} · Estación: {html.escape(estacion)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b_ant, b_rnmc = st.columns(2)
    with b_ant:
        if st.button("🔍 Ver Detalle de Antecedentes", key=f"btn_antecedentes_{id_clave}", width="stretch"):
            mostrar_dialogo_antecedentes(id_clave, nombre_completo)
    with b_rnmc:
        if st.button("📄 Ver Comparendos RNMC", key=f"btn_rnmc_{id_clave}", width="stretch"):
            mostrar_dialogo_rnmc(id_clave, nombre_completo)

    c1, c2, c3, c4 = st.columns(4)
    delitos_persona = delitos_f[delitos_f["_ID_CLAVE"] == id_clave].copy()
    ops_persona = operatividad_f[operatividad_f["_ID_CLAVE"] == id_clave].copy()

    with c1:
        tarjeta("Casos delictivos", formatear_entero(suma_columna(delitos_persona, "CANTIDAD CASOS")))
    with c2:
        tarjeta("Víctimas", formatear_entero(suma_columna(delitos_persona, "CANTIDAD VICTIMA")))
    with c3:
        tarjeta("Total tipo de captura", formatear_entero(suma_columna(ops_persona, "TOTAL TIPO DE CAPTURA")))
    with c4:
        tarjeta("Actividad operativa", formatear_entero(suma_columna(ops_persona, "TOTAL ACTIVIDAD OPERATIVA")))

    titulo_seccion("Registros de operatividad del funcionario")
    mostrar_tabla(
        ops_persona.sort_values("FECHA_HECHO", ascending=False,
                                na_position="last") if "FECHA_HECHO" in ops_persona.columns else ops_persona,
        ["FECHA_HECHO", "BOLETIN", "ESTACION", "CAI", "TIPO DE CAPTURA", "TOTAL TIPO DE CAPTURA",
         "TOTAL PERSONAS CAPTURADAS", "DELITO DE CAPTURA", "ACTIVIDAD OPERATIVA", "TOTAL ACTIVIDAD OPERATIVA"],
        {"FECHA_HECHO": "Fecha", "BOLETIN": "Boletín", "ESTACION": "Estación", "CAI": "CAI",
         "TIPO DE CAPTURA": "Tipo de captura", "TOTAL TIPO DE CAPTURA": "Total tipo de captura",
         "TOTAL PERSONAS CAPTURADAS": "Personas capturadas", "DELITO DE CAPTURA": "Delito de captura",
         "ACTIVIDAD OPERATIVA": "Actividad operativa", "TOTAL ACTIVIDAD OPERATIVA": "Total actividad"},
    )

    titulo_seccion("Registros delictivos del funcionario")
    mostrar_tabla(
        delitos_persona.sort_values("FECHA_HECHO", ascending=False,
                                    na_position="last") if "FECHA_HECHO" in delitos_persona.columns else delitos_persona,
        ["FECHA_HECHO", "BOLETIN", "MUNICIPIO", "DISTRITO", "ESTACION", "CAI", "CUADRANTE", "DELITO", "CANTIDAD CASOS",
         "CANTIDAD VICTIMA"],
        {"FECHA_HECHO": "Fecha", "BOLETIN": "Boletín", "MUNICIPIO": "Municipio", "DISTRITO": "Distrito",
         "ESTACION": "Estación", "CAI": "CAI", "CUADRANTE": "Cuadrante", "DELITO": "Delito", "CANTIDAD CASOS": "Casos",
         "CANTIDAD VICTIMA": "Víctimas"},
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
        opciones[f"{grado} {nombre} · {estacion} · ID {clave}".strip()] = clave

    etiqueta_seleccionada = st.selectbox("Selecciona un funcionario para consultar su ficha",
                                         options=list(opciones.keys()), index=None,
                                         placeholder="Buscar por nombre, estación o identificación...")
    if etiqueta_seleccionada:
        mostrar_perfil(opciones[etiqueta_seleccionada])


def mostrar_ficha_seleccionada():
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

    nombre = (str(funcionario.get("GRADO", "") or "") + " " + str(funcionario.get("NOMBRE", "") or "")).strip()
    st.markdown(f"### 👮 {html.escape(nombre)}")
    st.caption(
        "Consulta consolidada de todos los registros operativos y delictivos del funcionario, dentro del periodo y filtros seleccionados.")

    if st.button("✕ Cerrar ficha completa", key="cerrar_ficha_compartida"):
        st.session_state.pop("funcionario_seleccionado", None)
        st.session_state.pop("origen_ficha", None)
        st.rerun()
    mostrar_perfil(str(id_seleccionado))


@st.cache_resource(show_spinner=False, max_entries=10)
def calcular_turnos(inicio_t, fin_t, unidades_sel_t, cargos_sel_t, cedula_busqueda, nombre_busqueda):
    """Filtra los turnos y arma el resumen por funcionario. Se recalcula solo si cambian los filtros."""
    t = turnos
    mask = t["_ID_CLAVE"].ne("")
    if inicio_t is not None and fin_t is not None:
        f = t["FECHA_DIA"]
        mask &= f.isna() | ((f >= pd.Timestamp(inicio_t)) & (f <= pd.Timestamp(fin_t)))
    if unidades_sel_t:
        mask &= t["UNIDAD"].isin(unidades_sel_t)
    if cargos_sel_t:
        mask &= t["CARGO_SIATH"].isin(cargos_sel_t)
    if cedula_busqueda:
        mask &= t["_ID_CLAVE"].str.contains(re.escape(normalizar_id(cedula_busqueda)), na=False)
    if nombre_busqueda:
        patron = re.escape(nombre_busqueda)
        mask &= (t["_TEXTO_A"].str.contains(patron, na=False) | t["_TEXTO_B"].str.contains(patron, na=False))
    turnos_f = t[mask]

    columnas = ["Grado, nombres y apellidos", "Cédula", "Unidad", "Turnos", "Días con servicio",
                "Primer turno", "Último turno"]
    if turnos_f.empty:
        return turnos_f, pd.DataFrame(columns=columnas)

    ordenado = turnos_f.sort_values("FECHA_DIA", kind="stable")
    resumen = ordenado.groupby("_ID_CLAVE", dropna=False).agg(**{
        "Grado, nombres y apellidos": ("NOMBRE_COMPLETO", "last"),
        "Unidad": ("UNIDAD", "last"),
        "Turnos": ("UNIDAD", "size"),
        "Días con servicio": ("FECHA_DIA", "nunique"),
        "Primer turno": ("FECHA_DIA", "min"),
        "Último turno": ("FECHA_DIA", "max"),
    }).reset_index().rename(columns={"_ID_CLAVE": "Cédula"})
    for c in ("Primer turno", "Último turno"):
        resumen[c] = resumen[c].dt.strftime("%d/%m/%Y").fillna("")
    resumen = resumen[columnas].sort_values(
        ["Turnos", "Grado, nombres y apellidos"], ascending=[False, True]).reset_index(drop=True)
    return turnos_f, resumen


# ============================================================
# VISTA INDEPENDIENTE DE FICHA (se abre en una pestaña nueva)
# ============================================================

id_ficha_url = st.query_params.get("ficha")
if id_ficha_url:
    st.markdown(
        "<div style='padding:8px 0 14px;border-bottom:2px solid #C5A45B;'><div style='font-size:13px;font-weight:800;letter-spacing:1px;color:#C5A45B;'>POLICÍA NACIONAL · MEBAR</div></div>",
        unsafe_allow_html=True)
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
    header_principal_con_reloj()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta("Casos delictivos", formatear_entero(suma_columna(delitos_f, "CANTIDAD CASOS")),
                "Total del periodo filtrado")
    with c2:
        tarjeta("Víctimas registradas", formatear_entero(suma_columna(delitos_f, "CANTIDAD VICTIMA")),
                "Según el reporte delictivo")
    with c3:
        tarjeta("Total tipo de captura", formatear_entero(suma_columna(operatividad_f, "TOTAL TIPO DE CAPTURA")),
                "Suma de la columna TOTAL TIPO DE CAPTURA")
    with c4:
        tarjeta("Funcionarios identificados", formatear_entero(ranking["_ID_CLAVE"].nunique()),
                "Con identificación disponible")

    st.markdown("""
    <style>
    .ranking-intro { margin: 8px 0 12px; color:#526174; font-size:14px; }
    .ranking-card-description { box-sizing:border-box; min-height:154px; margin:9px 0 8px; padding:14px 15px; border:1px solid #DCE5EF; border-radius:14px; background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(240,245,250,.96)); box-shadow:0 5px 16px rgba(20,42,68,.06); font-size:13px; line-height:1.65; color:#435268; transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
    .ranking-card-description:hover { transform:translateY(-2px); box-shadow:0 9px 22px rgba(20,42,68,.11); }
    .ranking-card-description .description-label { display:block; margin-bottom:6px; font-size:11px; font-weight:900; letter-spacing:1.35px; text-transform:uppercase; background:linear-gradient(90deg,#12345A,#3D79A8,#12345A,#C49A55); background-size:240% auto; color:#12345A; -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; animation:rankingGradientFlow 5s linear infinite; }
    .ranking-card-description.carmesi { border-color:#E5CDD2; background:linear-gradient(145deg,#FFFCFC 0%,#F8EFF1 100%); }
    .ranking-card-description.carmesi .description-label { background:linear-gradient(90deg,#651525,#B13A52,#8A1C34,#C49A55,#651525); background-size:260% auto; -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; animation:rankingGradientFlow 4.6s linear infinite; }
    @keyframes rankingGradientFlow { 0% {background-position:0% center;} 100% {background-position:260% center;} }
    @media (prefers-reduced-motion: reduce) { .ranking-card-description .description-label { animation:none; } .ranking-card-description, .ranking-card-description:hover { transition:none; transform:none; } }
    div.st-key-ranking_card_capturas button { min-height:112px; width:100%; white-space:pre-wrap; text-align:left; border-radius:18px; border:1px solid #D6E2EF; background:linear-gradient(145deg,#FFFFFF 0%,#EEF4FA 100%); color:#12345A; font-size:15px; font-weight:800; line-height:1.45; padding:18px 16px; box-shadow:0 6px 18px rgba(18,52,90,.08); transition:all .2s ease; }
    div.st-key-ranking_card_capturas button:hover { border-color:#12345A; transform:translateY(-3px); box-shadow:0 12px 24px rgba(18,52,90,.15); }
    div.st-key-ranking_card_delitos button, div.st-key-ranking_card_homicidios button { min-height:112px; width:100%; white-space:pre-wrap; text-align:left; border-radius:18px; border:1px solid #6E1727; background:linear-gradient(135deg,#651525 0%,#851D32 58%,#3D101B 100%); color:#FFFFFF; font-size:15px; font-weight:800; line-height:1.45; padding:18px 16px; box-shadow:0 7px 20px rgba(72,12,28,.19); transition:all .2s ease; }
    div.st-key-ranking_card_delitos button:hover, div.st-key-ranking_card_homicidios button:hover { border-color:#B88A50; transform:translateY(-3px); box-shadow:0 13px 27px rgba(72,12,28,.27); background:linear-gradient(135deg,#7A192C 0%,#9A2439 58%,#4A111F 100%); color:#FFFFFF; }
    .ranking-panel-carmesi { border:1px solid #D9B7BE; border-left:5px solid #7A192C; background:linear-gradient(135deg,#F7F0F1 0%,#FFFFFF 78%); border-radius:16px; padding:17px 18px 8px; margin:8px 0 18px; }
    .ranking-panel-azul { border:1px solid #D6E2EF; border-left:5px solid #12345A; background:linear-gradient(135deg,#F1F5FA 0%,#FFFFFF 78%); border-radius:16px; padding:17px 18px 8px; margin:8px 0 18px; }
    .ranking-panel-title {font-size:19px;font-weight:800;color:#651525;margin:0 0 5px;}
    .ranking-panel-sub {font-size:13px;color:#4D2630;margin:0 0 12px;}
    </style>
    <div class="ranking-intro">Selecciona una tarjeta para desplegar su ranking. Pulsa de nuevo la misma tarjeta para recoger la información.</div>
    """, unsafe_allow_html=True)

    if "ranking_principal_activo" not in st.session_state:
        st.session_state["ranking_principal_activo"] = None

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        if st.button("  01 · TOP 10\nFuncionarios por total de tipo de captura", key="ranking_card_capturas",
                     width="stretch"):
            st.session_state["ranking_principal_activo"] = None if st.session_state[
                                                                       "ranking_principal_activo"] == "capturas" else "capturas"
        st.markdown(
            "<div class='ranking-card-description'><span class='description-label'>¿Qué encontrará en esta opción?</span>Visualice el listado del personal policial destacado por el total de procedimientos de captura realizados.</div>",
            unsafe_allow_html=True)
    with r2:
        if st.button("02 · TOP 10\nFUNCIONARIOS CON MÁS DELITOS", key="ranking_card_delitos", width="stretch"):
            st.session_state["ranking_principal_activo"] = None if st.session_state[
                                                                       "ranking_principal_activo"] == "delitos" else "delitos"
        st.markdown(
            "<div class='ranking-card-description carmesi'><span class='description-label'>¿Qué encontrará en esta opción?</span>Consulte el Top 10 de funcionarios asociados con el mayor número de registros de hechos delictivos reportados.</div>",
            unsafe_allow_html=True)
    with r3:
        if st.button("03 · TOP 10\nFUNCIONARIOS CON MÁS HOMICIDIOS", key="ranking_card_homicidios",
                     width="stretch"):
            st.session_state["ranking_principal_activo"] = None if st.session_state[
                                                                       "ranking_principal_activo"] == "homicidios" else "homicidios"
        st.markdown(
            "<div class='ranking-card-description carmesi'><span class='description-label'>¿Qué encontrará en esta opción?</span>Identifique a los funcionarios vinculados con el mayor número de registros de homicidio.</div>",
            unsafe_allow_html=True)

    ranking_activo = st.session_state["ranking_principal_activo"]
    if ranking_activo == "capturas":
        st.markdown(
            "<div class='ranking-panel-azul'><div style='font-size:19px;font-weight:800;color:#12345A;'>01 · TOP 10 FUNCIONARIOS POR TOTAL DE TIPO DE CAPTURA</div></div>",
            unsafe_allow_html=True)
        mostrar_ranking_tarjetas(ranking, "TOTAL_TIPO_CAPTURA", "capturas",
                                 "No se encontraron valores en TOTAL TIPO DE CAPTURA.")
    elif ranking_activo == "delitos":
        st.markdown(
            "<div class='ranking-panel-carmesi'><div class='ranking-panel-title'>02 · TOP 10 FUNCIONARIOS CON MÁS DELITOS</div></div>",
            unsafe_allow_html=True)
        mostrar_ranking_tarjetas(ranking, "CASOS", "delitos", "No se encontraron casos delictivos.")
    elif ranking_activo == "homicidios":
        st.markdown(
            "<div class='ranking-panel-carmesi'><div class='ranking-panel-title'>03 · TOP 10 FUNCIONARIOS CON MÁS HOMICIDIOS</div></div>",
            unsafe_allow_html=True)
        mostrar_ranking_tarjetas(ranking_homicidios, "CASOS", "homicidios", "No se encontraron registros de homicidio.")

    mostrar_ficha_seleccionada()


# ============================================================
# PANTALLA 2: GESTIÓN OPERATIVA
# ============================================================

elif pantalla == "Gestión Operativa":
    encabezado("GESTIÓN OPERATIVA",
               "Panel interactivo de capturas, cuadrantes, funcionarios, estaciones y actividad operativa")

    ops = operatividad_f.copy()
    if not ops.empty:
        for col in ["TOTAL TIPO DE CAPTURA", "TOTAL PERSONAS CAPTURADAS", "TOTAL DELITO DE CAPTURA",
                    "TOTAL ACTIVIDAD OPERATIVA"]:
            if col in ops.columns:
                ops[col] = pd.to_numeric(ops[col], errors="coerce").fillna(0)

    titulo_seccion("Funcionarios · Capturas por modalidad")
    st.markdown("""<style>
        div[data-testid="stDataFrame"] { font-family: 'Inter', sans-serif !important; border: 1px solid rgba(226, 232, 240, 0.9) !important; border-radius: 20px !important; overflow: hidden !important; background: #ffffff !important; box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.07), 0 0 0 1px rgba(197, 164, 91, 0.25) !important; padding: 6px !important; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        div[data-testid="stDataFrame"]:hover { box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.12), 0 0 0 2px rgba(197, 164, 91, 0.45) !important; transform: translateY(-2px); }
        div[data-testid="stDataFrame"] [role="grid"] { font-size: 13.5px !important; color: #1e293b !important; border: 0 !important; outline: none !important; }
        div[data-testid="stDataFrame"] [role="columnheader"] { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%) !important; color: #ffffff !important; font-weight: 700 !important; font-size: 11.5px !important; letter-spacing: 0.9px !important; text-transform: uppercase !important; border-bottom: 3px solid #C5A45B !important; padding: 16px 14px !important; position: relative; }
        div[data-testid="stDataFrame"] [role="columnheader"] * { color: #ffffff !important; font-weight: 700 !important; }
        div[data-testid="stDataFrame"] [role="columnheader"]::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent); }
        div[data-testid="stDataFrame"] [role="gridcell"] { color: #334155 !important; font-size: 13.5px !important; border-bottom: 1px solid #f1f5f9 !important; background: #ffffff !important; padding: 14px 14px !important; transition: all 0.2s ease; }
        div[data-testid="stDataFrame"] [role="row"]:nth-child(even) [role="gridcell"] { background: #f8fafc !important; }
        div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] { background: linear-gradient(90deg, #eff6ff 0%, #f0fdf4 100%) !important; color: #0f172a !important; border-bottom-color: #cbd5e1 !important; }
        div[data-testid="stDataFrame"] [role="row"]:focus-within [role="gridcell"], div[data-testid="stDataFrame"] [role="gridcell"]:focus { background: #dbeafe !important; outline: 2px solid #C5A45B !important; outline-offset: -2px !important; color: #1e3a8a !important; font-weight: 600 !important; }
        div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(4), div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(5), div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(6) { text-align: center !important; font-variant-numeric: tabular-nums !important; font-family: 'JetBrains Mono', 'Courier New', monospace !important; font-weight: 600 !important; }
        div[data-testid="stDataFrame"] [role="columnheader"]:nth-child(4), div[data-testid="stDataFrame"] [role="columnheader"]:nth-child(5), div[data-testid="stDataFrame"] [role="columnheader"]:nth-child(6) { text-align: center !important; }
        div[data-testid="stDataFrame"] [role="row"] [role="gridcell"]:nth-child(6) { color: #926d18 !important; font-weight: 800 !important; background: rgba(197, 164, 91, 0.12) !important; border-radius: 6px !important; }
        div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"]:nth-child(6) { background: rgba(197, 164, 91, 0.25) !important; color: #785307 !important; }
        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar { height: 6px; width: 6px; }
        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        div[data-testid="stDataFrame"] [role="grid"]::-webkit-scrollbar-track { background: transparent; }
        div.st-key-operatividad_mostrar_todos button { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important; color: #FFFFFF !important; border: 1px solid #C5A45B !important; border-radius: 12px !important; font-weight: 700 !important; font-size: 13px !important; letter-spacing: 0.6px !important; padding: 12px 22px !important; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important; box-shadow: 0 4px 15px rgba(30, 58, 138, 0.25) !important; }
        div.st-key-operatividad_mostrar_todos button:hover { background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%) !important; transform: translateY(-2px) scale(1.02) !important; box-shadow: 0 8px 25px rgba(30, 58, 138, 0.4) !important; border-color: #e2b963 !important; }
    </style>""", unsafe_allow_html=True)

    st.markdown(
        '<div class="operatividad-tabla-ayuda"><strong>Seleccione un funcionario</strong> haciendo clic en su fila para filtrar los indicadores, gráficos y registros que aparecen debajo. Use <strong>Mostrar todos</strong> para retirar la selección.</div>',
        unsafe_allow_html=True)

    columna_funcionario = "GR APELLIDOS Y NOMBRES POLICIA_1"
    if not ops.empty and columna_funcionario in ops.columns:
        resumen = construir_resumen_funcionarios(
            ops,
            (inicio, fin, tuple(estaciones_sel), tuple(grados_sel), cedula_busqueda, nombre_busqueda),
            columna_funcionario,
        )

        clave_estado = "operatividad_funcionario_cedula"
        seleccionado = st.session_state.get(clave_estado, "")
        btn_col, info_col = st.columns([1, 4])
        with btn_col:
            if st.button("Mostrar todos", key="operatividad_mostrar_todos", width="stretch"):
                st.session_state.pop(clave_estado, None)
                st.session_state.pop("tabla_funcionarios_operatividad", None)
                st.rerun()
        with info_col:
            if seleccionado:
                st.info(f"Filtro activo · Cédula: {seleccionado}")
            else:
                st.caption("Sin funcionario seleccionado · se muestran los datos de todos los funcionarios.")

        resumen_mostrar = resumen.head(2000)
        evento_tabla = st.dataframe(
            resumen_mostrar, width="stretch", hide_index=True,
            height=min(440, 46 + 35 * min(len(resumen_mostrar), 11)),
            on_select="rerun", selection_mode="single-row", key="tabla_funcionarios_operatividad",
            column_config={
                "Grado, nombres y apellidos": st.column_config.TextColumn("Grado, nombres y apellidos", width="large"),
                "Cédula": st.column_config.TextColumn("Cédula", width="medium"),
                "Estación": st.column_config.TextColumn("Estación", width="medium"),
                "Capturas flagrancia": st.column_config.NumberColumn("Capturas flagrancia", format="%d", width="small"),
                "Capturas orden judicial": st.column_config.NumberColumn("Capturas orden judicial", format="%d",
                                                                         width="small"),
                "Total tipo de captura": st.column_config.NumberColumn("Total tipo de captura", format="%d",
                                                                       width="small"),
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
            ids_limpios = ops["IDENTIFICACION"].astype("string").fillna("").str.replace(
                r"\.0$", "", regex=True
            ).str.strip()
            filtrada = ops.loc[ids_limpios == str(seleccionado)].copy()
            if not filtrada.empty:
                ops = filtrada
                nombre_funcionario_filtrado = filtrada[columna_funcionario].dropna().astype(str).iloc[0]

                st.markdown(
                    f'''
                    <div style="background: linear-gradient(135deg, #F3F7FC 0%, #E8F0F8 100%); border-left: 4px solid {AZUL}; padding: 14px 18px; border-radius: 10px; margin: 8px 0 18px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                            <div style="color: #12345A; font-weight: 600; font-size: 14px;">👮 Vista filtrada · {html.escape(nombre_funcionario_filtrado)} · Cédula {html.escape(seleccionado)}</div>
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

                funcionario_info = maestros[maestros["_ID_CLAVE"] == seleccionado]
                if not funcionario_info.empty:
                    grado = str(funcionario_info["GRADO"].iloc[0]) if "GRADO" in funcionario_info.columns else ""
                    nombre = str(funcionario_info["NOMBRE"].iloc[0]) if "NOMBRE" in funcionario_info.columns else ""
                    nombre_completo = f"{grado} {nombre}".strip()
                else:
                    nombre_completo = nombre_funcionario_filtrado

                b_ant, b_rnmc = st.columns(2)
                with b_ant:
                    if st.button("🔍 Ver Detalle de Antecedentes", key=f"btn_antecedentes_ops_{seleccionado}",
                                 width="stretch"):
                        mostrar_dialogo_antecedentes(seleccionado, nombre_completo)
                with b_rnmc:
                    if st.button("📄 Ver Comparendos RNMC", key=f"btn_rnmc_ops_{seleccionado}",
                                 width="stretch"):
                        mostrar_dialogo_rnmc(seleccionado, nombre_completo)
            else:
                st.warning(
                    "No se encontraron registros operativos para la cédula seleccionada en los filtros actuales.")
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
        titulo_seccion("Línea de tiempo mensual · Tipo de captura")
        if "FECHA_HECHO" in ops.columns and "TOTAL TIPO DE CAPTURA" in ops.columns:
            temporal = ops.dropna(subset=["FECHA_HECHO"]).copy()
            if not temporal.empty:
                temporal["MES_FECHA"] = temporal["FECHA_HECHO"].dt.to_period("M").dt.to_timestamp()
                mensual = temporal.groupby("MES_FECHA", as_index=False)["TOTAL TIPO DE CAPTURA"].sum().sort_values(
                    "MES_FECHA")
                fig = px.line(mensual, x="MES_FECHA", y="TOTAL TIPO DE CAPTURA", markers=True, line_shape="spline",
                              labels={"MES_FECHA": "Mes", "TOTAL TIPO DE CAPTURA": "Total tipo de captura"},
                              hover_data={"MES_FECHA": "|%B %Y", "TOTAL TIPO DE CAPTURA": ":,.0f"})
                fig.update_traces(line=dict(color=AZUL, width=3), marker=dict(size=8, color=DORADO))
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", hovermode="x unified",
                                  xaxis=dict(tickformat="%b %Y"), margin=dict(l=10, r=10, t=25, b=10))
                mostrar_grafico(estilizar_grafico(fig))
            else:
                st.info("No hay fechas válidas para construir la línea de tiempo mensual.")
        else:
            st.info("Faltan FECHA_HECHO o TOTAL TIPO DE CAPTURA para la línea de tiempo.")

        izq, der = st.columns(2, gap="large")
        with izq:
            titulo_seccion("Distribución por IND CUADRANTE")
            if "IND CUADRANTE" in ops.columns:
                campo = ops.copy()
                campo["IND CUADRANTE"] = campo["IND CUADRANTE"].astype(object).where(
                    campo["IND CUADRANTE"].notna(), "No especificado"
                ).astype(str).str.strip()
                campo.loc[campo["IND CUADRANTE"] == "", "IND CUADRANTE"] = "No especificado"
                if "TOTAL TIPO DE CAPTURA" in campo.columns:
                    agregado = campo.groupby("IND CUADRANTE", as_index=False)["TOTAL TIPO DE CAPTURA"].sum().rename(
                        columns={"TOTAL TIPO DE CAPTURA": "CAPTURAS"})
                else:
                    agregado = campo.groupby("IND CUADRANTE").size().reset_index(name="CAPTURAS")
                agregado = agregado.sort_values("CAPTURAS", ascending=False).head(20)
                fig = px.bar(agregado, x="IND CUADRANTE", y="CAPTURAS", text="CAPTURAS",
                             labels={"CAPTURAS": "Total tipo de captura"}, color_discrete_sequence=[DORADO])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-30,
                                  margin=dict(l=10, r=10, t=20, b=10))
                mostrar_grafico(estilizar_grafico(fig))
            else:
                st.info("El reporte no contiene la columna IND CUADRANTE.")

        with der:
            titulo_seccion("Actividad operativa por estación")
            if "ESTACION" in ops.columns and "TOTAL TIPO DE CAPTURA" in ops.columns:
                por_estacion = ops.copy()
                por_estacion["ESTACION"] = por_estacion["ESTACION"].astype(object).where(
                    por_estacion["ESTACION"].notna(), "No especificada"
                ).astype(str)
                por_estacion["TOTAL TIPO DE CAPTURA"] = pd.to_numeric(por_estacion["TOTAL TIPO DE CAPTURA"],
                                                                      errors="coerce").fillna(0)
                est = por_estacion.groupby("ESTACION", as_index=False)["TOTAL TIPO DE CAPTURA"].sum().rename(
                    columns={"TOTAL TIPO DE CAPTURA": "TOTAL"}).sort_values("TOTAL", ascending=False).head(15)
                fig = px.bar(est, x="TOTAL", y="ESTACION", orientation="h", text="TOTAL",
                             labels={"TOTAL": "Total de tipos de captura", "ESTACION": "Estación"},
                             color_discrete_sequence=[AZUL])
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                  yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=35, t=20, b=10))
                mostrar_grafico(estilizar_grafico(fig))
            elif "ESTACION" not in ops.columns:
                st.info("El reporte no contiene la columna ESTACION.")
            else:
                st.info("El reporte no contiene la columna TOTAL TIPO DE CAPTURA.")

        titulo_seccion("Funcionarios con capturas asociadas a homicidio")
        if "DELITO DE CAPTURA" in ops.columns:
            homic = ops[ops["DELITO DE CAPTURA"].astype(str).str.contains("homicidio", case=False, na=False)].copy()
            if not homic.empty:
                campos = [c for c in
                          ["GR APELLIDOS Y NOMBRES POLICIA_1", "IDENTIFICACION", "ESTACION", "DELITO DE CAPTURA",
                           "TOTAL TIPO DE CAPTURA", "TOTAL PERSONAS CAPTURADAS", "FECHA_HECHO"] if c in homic.columns]
                if "TOTAL TIPO DE CAPTURA" in homic.columns:
                    homic = homic.sort_values("TOTAL TIPO DE CAPTURA", ascending=False)
                mostrar_tabla(homic[campos], campos, {"GR APELLIDOS Y NOMBRES POLICIA_1": "Grado, nombres y apellidos",
                                                      "IDENTIFICACION": "Cédula", "ESTACION": "Estación",
                                                      "DELITO DE CAPTURA": "Delito de captura",
                                                      "TOTAL TIPO DE CAPTURA": "Total tipo de captura",
                                                      "TOTAL PERSONAS CAPTURADAS": "Personas capturadas",
                                                      "FECHA_HECHO": "Fecha"})
            else:
                st.info("No se encontraron registros cuyo delito de captura contenga 'homicidio'.")
        else:
            st.info("El reporte no contiene la columna DELITO DE CAPTURA.")

        titulo_seccion("Capturas por funcionario · Flagrancia y orden judicial")
        if "TIPO DE CAPTURA" in ops.columns:
            tipo = ops["TIPO DE CAPTURA"].astype(object).where(
                ops["TIPO DE CAPTURA"].notna(), ""
            ).astype(str).str.casefold()
            subset = ops[tipo.str.contains("flagrancia|orden judicial", regex=True, na=False)].copy()
            if not subset.empty:
                subset["TIPO_NORMALIZADO"] = subset["TIPO DE CAPTURA"].astype(str).str.casefold().apply(
                    lambda x: "Flagrancia" if "flagrancia" in x else "Orden judicial")
                columna_metrica = "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in subset.columns else None
                if columna_metrica:
                    subset[columna_metrica] = pd.to_numeric(subset[columna_metrica], errors="coerce").fillna(0)
                    if "GR APELLIDOS Y NOMBRES POLICIA_1" in subset.columns:
                        resumen_func = subset.groupby(
                            ["GR APELLIDOS Y NOMBRES POLICIA_1", "TIPO_NORMALIZADO"], dropna=False
                        )[columna_metrica].sum().reset_index(name="TOTAL")
                    else:
                        resumen_func = subset.groupby("TIPO_NORMALIZADO")[columna_metrica].sum().reset_index(
                            name="TOTAL")
                    if "GR APELLIDOS Y NOMBRES POLICIA_1" in resumen_func.columns:
                        resumen_func["FUNCIONARIO"] = resumen_func[
                            "GR APELLIDOS Y NOMBRES POLICIA_1"
                        ].astype(object).where(
                            resumen_func["GR APELLIDOS Y NOMBRES POLICIA_1"].notna(), "No registrado"
                        ).astype(str)
                        fig = px.bar(resumen_func, x="FUNCIONARIO", y="TOTAL", color="TIPO_NORMALIZADO",
                                     barmode="group", labels={"TOTAL": "Total tipo de captura",
                                                              "FUNCIONARIO": "Grado, nombres y apellidos",
                                                              "TIPO_NORMALIZADO": "Tipo de captura"},
                                     color_discrete_map={"Flagrancia": AZUL, "Orden judicial": DORADO})
                        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-35,
                                          margin=dict(l=10, r=10, t=20, b=10))
                        mostrar_grafico(estilizar_grafico(fig))
                    mostrar_tabla(resumen_func, list(resumen_func.columns),
                                  {"GR APELLIDOS Y NOMBRES POLICIA_1": "Grado, nombres y apellidos",
                                   "TIPO_NORMALIZADO": "Tipo de captura", "TOTAL": "Total tipo de captura"})
                else:
                    st.info("Falta TOTAL TIPO DE CAPTURA para comparar flagrancia y orden judicial.")
            else:
                st.info("No se encontraron tipos de captura de flagrancia u orden judicial en los filtros actuales.")
        else:
            st.info("El reporte no contiene la columna TIPO DE CAPTURA.")

        titulo_seccion("Distribución por delito de captura")
        if "DELITO DE CAPTURA" in ops.columns:
            delitos_cap = ops.copy()
            delitos_cap["DELITO DE CAPTURA"] = delitos_cap["DELITO DE CAPTURA"].astype(object).where(
                delitos_cap["DELITO DE CAPTURA"].notna(), "No especificado"
            ).astype(str)
            metrica_delito = "TOTAL DELITO DE CAPTURA" if "TOTAL DELITO DE CAPTURA" in delitos_cap.columns else "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in delitos_cap.columns else None
            if metrica_delito:
                delitos_cap[metrica_delito] = pd.to_numeric(delitos_cap[metrica_delito], errors="coerce").fillna(0)
                por_delito = delitos_cap.groupby("DELITO DE CAPTURA", as_index=False)[metrica_delito].sum().rename(
                    columns={metrica_delito: "TOTAL"}).sort_values("TOTAL", ascending=False).head(20)
                fig = px.bar(por_delito, x="TOTAL", y="DELITO DE CAPTURA", orientation="h", text="TOTAL",
                             labels={"TOTAL": "Total registrado"}, color_discrete_sequence=[DORADO])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                  yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=20, b=10))
                mostrar_grafico(estilizar_grafico(fig))
            else:
                st.info("Falta una columna numérica para resumir los delitos de captura.")
        else:
            st.info("El reporte no contiene la columna DELITO DE CAPTURA.")

        titulo_seccion("Tipos de actividad operativa")
        if "ACTIVIDAD OPERATIVA" in ops.columns:
            actividades = ops.copy()
            actividades["ACTIVIDAD OPERATIVA"] = actividades["ACTIVIDAD OPERATIVA"].astype(object).where(
                actividades["ACTIVIDAD OPERATIVA"].notna(), "No especificada"
            ).astype(str)
            metrica_actividad = "TOTAL ACTIVIDAD OPERATIVA" if "TOTAL ACTIVIDAD OPERATIVA" in actividades.columns else "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in actividades.columns else None
            if metrica_actividad:
                actividades[metrica_actividad] = pd.to_numeric(actividades[metrica_actividad], errors="coerce").fillna(
                    0)
                por_actividad = actividades.groupby("ACTIVIDAD OPERATIVA", as_index=False)[
                    metrica_actividad].sum().rename(columns={metrica_actividad: "TOTAL"}).sort_values(
                    "TOTAL", ascending=False).head(20)
                fig = px.bar(por_actividad, x="TOTAL", y="ACTIVIDAD OPERATIVA", orientation="h", text="TOTAL",
                             labels={"TOTAL": "Total registrado"}, color_discrete_sequence=[AZUL])
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                  yaxis={"categoryorder": "total ascending"}, margin=dict(l=10, r=10, t=20, b=10))
                mostrar_grafico(estilizar_grafico(fig))
            else:
                st.info("Falta una columna numérica para resumir la actividad operativa.")
        else:
            st.info("El reporte no contiene la columna ACTIVIDAD OPERATIVA.")

        titulo_seccion("Mapa georreferenciado de registros operativos")
        if "LATITUD" in ops.columns and "LONGITUD" in ops.columns:
            mapa = ops.copy()
            mapa["LATITUD"] = pd.to_numeric(mapa["LATITUD"].astype(str).str.replace(",", ".", regex=False),
                                            errors="coerce")
            mapa["LONGITUD"] = pd.to_numeric(mapa["LONGITUD"].astype(str).str.replace(",", ".", regex=False),
                                             errors="coerce")
            mapa = mapa.dropna(subset=["LATITUD", "LONGITUD"])
            mapa = mapa[mapa["LATITUD"].between(-90, 90) & mapa["LONGITUD"].between(-180, 180)]
            total_puntos_mapa = len(mapa)
            mapa = mapa.head(5000)  # límite para que el mapa no se vuelva lento
            if not mapa.empty:
                hover_cols = [c for c in
                              ["ESTACION", "CAI", "CUADRANTE", "IND CUADRANTE", "TIPO DE CAPTURA", "DELITO DE CAPTURA",
                               "ACTIVIDAD OPERATIVA", "FECHA_HECHO", "GR APELLIDOS Y NOMBRES POLICIA_1"] if
                              c in mapa.columns]
                color_col = "TIPO DE CAPTURA" if "TIPO DE CAPTURA" in mapa.columns else None
                size_col = "TOTAL TIPO DE CAPTURA" if "TOTAL TIPO DE CAPTURA" in mapa.columns and (
                        mapa["TOTAL TIPO DE CAPTURA"] > 0).any() else None
                parametros_mapa = dict(
                    lat="LATITUD", lon="LONGITUD",
                    hover_name="ESTACION" if "ESTACION" in mapa.columns else None,
                    hover_data=hover_cols, color=color_col, size=size_col, size_max=18, zoom=9,
                    center={"lat": float(mapa["LATITUD"].median()), "lon": float(mapa["LONGITUD"].median())},
                )
                # px.scatter_mapbox está obsoleto en Plotly recientes: se usa scatter_map si existe.
                if hasattr(px, "scatter_map"):
                    fig = px.scatter_map(mapa, map_style="open-street-map", **parametros_mapa)
                else:
                    fig = px.scatter_mapbox(mapa, mapbox_style="open-street-map", **parametros_mapa)
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=560, legend_title_text="Tipo de captura")
                mostrar_grafico(estilizar_grafico(fig))
                st.caption(
                    f"Se muestran {len(mapa):,} de {total_puntos_mapa:,} registros con coordenadas válidas (máximo 5.000 puntos).")
            else:
                st.info("No se encontraron coordenadas válidas en LATITUD y LONGITUD.")
        else:
            st.info("El reporte no contiene las columnas LATITUD y LONGITUD.")

        titulo_seccion("Registros detallados de operatividad")
        columnas_ops = ["FECHA_HECHO", "BOLETIN", "MUNICIPIO", "DISTRITO", "ESTACION", "CAI", "CUADRANTE",
                        "IND CUADRANTE", "GR APELLIDOS Y NOMBRES POLICIA_1", "IDENTIFICACION", "TIPO DE CAPTURA",
                        "TOTAL TIPO DE CAPTURA", "TOTAL PERSONAS CAPTURADAS", "DELITO DE CAPTURA",
                        "TOTAL DELITO DE CAPTURA", "ACTIVIDAD OPERATIVA", "TOTAL ACTIVIDAD OPERATIVA", "LATITUD",
                        "LONGITUD"]
        mostrar_tabla(ops.sort_values("FECHA_HECHO", ascending=False, na_position="last"), columnas_ops,
                      {"FECHA_HECHO": "Fecha", "BOLETIN": "Boletín", "MUNICIPIO": "Municipio", "DISTRITO": "Distrito",
                       "ESTACION": "Estación", "CAI": "CAI", "CUADRANTE": "Cuadrante",
                       "IND CUADRANTE": "Indicador de cuadrante",
                       "GR APELLIDOS Y NOMBRES POLICIA_1": "Grado, nombres y apellidos", "IDENTIFICACION": "Cédula",
                       "TIPO DE CAPTURA": "Tipo de captura", "TOTAL TIPO DE CAPTURA": "Total tipo de captura",
                       "TOTAL PERSONAS CAPTURADAS": "Personas capturadas", "DELITO DE CAPTURA": "Delito de captura",
                       "TOTAL DELITO DE CAPTURA": "Total delito de captura",
                       "ACTIVIDAD OPERATIVA": "Actividad operativa", "TOTAL ACTIVIDAD OPERATIVA": "Total actividad",
                       "LATITUD": "Latitud", "LONGITUD": "Longitud"})

    titulo_seccion("Ficha individual del funcionario")
    selector_funcionario()
    mostrar_ficha_seleccionada()


# ============================================================
# PANTALLA 3: REGISTRO DELICTIVO
# ============================================================

elif pantalla == "Registro Delictivo":
    ROJO_CARMESI = "#9F1239"
    ROJO_CARMESI_CLARO = "#BE123C"

    encabezado("GESTIÓN DELICTIVA", "Análisis de delitos, comportamiento mensual y desempeño por funcionario")

    base_gestion = delitos_f.copy()
    if "CANTIDAD CASOS" in base_gestion.columns:
        base_gestion["CANTIDAD CASOS"] = pd.to_numeric(base_gestion["CANTIDAD CASOS"], errors="coerce").fillna(0)
    else:
        base_gestion["CANTIDAD CASOS"] = 1

    if not base_gestion.empty and "_ID_CLAVE" in base_gestion.columns:
        cantidades = base_gestion.groupby("_ID_CLAVE", dropna=False)["CANTIDAD CASOS"].sum().reset_index(
            name="CANTIDAD DELITOS")
        tabla_funcionarios = maestros_f.merge(cantidades, on="_ID_CLAVE", how="left")
        tabla_funcionarios["CANTIDAD DELITOS"] = tabla_funcionarios["CANTIDAD DELITOS"].fillna(0)

        if "FECHA_HECHO" in base_gestion.columns and "ESTACION" in base_gestion.columns:
            estaciones_func = base_gestion.sort_values(
                "FECHA_HECHO", ascending=False, na_position="last").drop_duplicates("_ID_CLAVE")[
                ["_ID_CLAVE", "ESTACION"]].rename(columns={"ESTACION": "ESTACIÓN DEL REGISTRO"})
            tabla_funcionarios = tabla_funcionarios.drop(columns=["ESTACIÓN DEL REGISTRO"], errors="ignore").merge(
                estaciones_func, on="_ID_CLAVE", how="left")
        else:
            tabla_funcionarios["ESTACIÓN DEL REGISTRO"] = tabla_funcionarios.get("ESTACION", "")

        grado_funcionario = tabla_funcionarios.get("GRADO", pd.Series("", index=tabla_funcionarios.index))
        nombre_funcionario = tabla_funcionarios.get("NOMBRE", pd.Series("", index=tabla_funcionarios.index))
        tabla_funcionarios["GRADO Y NOMBRE"] = (
            grado_funcionario.astype(object).where(grado_funcionario.notna(), "").astype(str).str.strip()
            + " "
            + nombre_funcionario.astype(object).where(nombre_funcionario.notna(), "").astype(str).str.strip()
        ).str.strip()
        tabla_funcionarios["CÉDULA"] = tabla_funcionarios["_ID_CLAVE"].astype(str)
        tabla_funcionarios["ESTACIÓN"] = tabla_funcionarios["ESTACIÓN DEL REGISTRO"].astype(object).where(
            tabla_funcionarios["ESTACIÓN DEL REGISTRO"].notna(), ""
        ).astype(str).str.strip()
        tabla_funcionarios = tabla_funcionarios.sort_values("CANTIDAD DELITOS", ascending=False)
    else:
        tabla_funcionarios = pd.DataFrame(
            columns=["GRADO Y NOMBRE", "CÉDULA", "ESTACIÓN", "CANTIDAD DELITOS", "_ID_CLAVE"])

    titulo_seccion("01 · Funcionarios y cantidad de delitos")
    st.markdown(f"""<div style="background:linear-gradient(115deg,{ROJO_CARMESI},#701A35);color:#fff; border-radius:14px;padding:15px 19px;margin:0 0 12px 0;box-shadow:0 6px 18px rgba(159,18,57,.14);">
    <div style="font-size:16px;font-weight:800;letter-spacing:.2px;">SELECCIÓN DE FUNCIONARIO</div>
    <div style="font-size:13px;color:#FFE4E9;margin-top:4px;">Selecciona un funcionario para filtrar todos los indicadores y gráficos de este panel.</div></div>""",
                unsafe_allow_html=True)

    if not tabla_funcionarios.empty:
        clave_estado_g = "gestion_delictiva_funcionario_cedula"
        seleccionado_g = str(st.session_state.get(clave_estado_g, "") or "").strip()

        controles_g, estado_g = st.columns([1, 4])
        with controles_g:
            if st.button("Mostrar todos", key="gestion_delictiva_mostrar_todos", width="stretch"):
                st.session_state.pop(clave_estado_g, None)
                st.session_state.pop("tabla_funcionarios_gestion_delictiva", None)
                st.rerun()
        with estado_g:
            if seleccionado_g:
                fila_activa = tabla_funcionarios[tabla_funcionarios["CÉDULA"].astype(str) == seleccionado_g]
                nombre_activo = fila_activa.iloc[0]["GRADO Y NOMBRE"] if not fila_activa.empty else seleccionado_g
                st.info(f"Filtro activo · {nombre_activo} · C.C. {seleccionado_g}")
            else:
                st.caption(
                    "Haz clic en cualquier fila de la tabla para seleccionar un funcionario y filtrar los gráficos de abajo.")

        vista_funcionarios = tabla_funcionarios[
            ["GRADO Y NOMBRE", "CÉDULA", "ESTACIÓN", "CANTIDAD DELITOS"]].copy().reset_index(drop=True)
        vista_funcionarios = vista_funcionarios.rename(
            columns={"GRADO Y NOMBRE": "Grado, nombres y apellidos", "CÉDULA": "Cédula", "ESTACIÓN": "Estación",
                     "CANTIDAD DELITOS": "Cantidad de delitos"})

        vista_funcionarios = vista_funcionarios.head(2000)
        evento_tabla_g = st.dataframe(vista_funcionarios, width="stretch", hide_index=True,
                                      height=min(440, 46 + 35 * min(len(vista_funcionarios), 11)), on_select="rerun",
                                      selection_mode="single-row", key="tabla_funcionarios_gestion_delictiva",
                                      column_config={"Grado, nombres y apellidos": st.column_config.TextColumn(
                                          "Grado, nombres y apellidos", width="large"),
                                          "Cédula": st.column_config.TextColumn("Cédula", width="medium"),
                                          "Estación": st.column_config.TextColumn("Estación", width="medium"),
                                          "Cantidad de delitos": st.column_config.NumberColumn(
                                              "Cantidad de delitos", format="%d", width="small")})

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

            fila_sel = tabla_funcionarios[tabla_funcionarios["CÉDULA"].astype(str) == seleccionado_g]
            if not fila_sel.empty:
                nombre_completo_g = str(fila_sel.iloc[0]["GRADO Y NOMBRE"]).strip() or seleccionado_g
            else:
                nombre_completo_g = seleccionado_g

            st.markdown(
                f'''
                <div style="background: linear-gradient(135deg, #FDF2F4 0%, #F8E4E8 100%); border-left: 4px solid {ROJO_CARMESI}; padding: 14px 18px; border-radius: 10px; margin: 8px 0 18px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="color: #701A35; font-weight: 600; font-size: 14px;">👮 Vista filtrada · {html.escape(nombre_completo_g)} · Cédula {html.escape(seleccionado_g)}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

            b_ant_g, b_rnmc_g = st.columns(2)
            with b_ant_g:
                if st.button("🔍 Ver Detalle de Antecedentes", key=f"btn_antecedentes_del_{seleccionado_g}",
                             width="stretch"):
                    mostrar_dialogo_antecedentes(seleccionado_g, nombre_completo_g)
            with b_rnmc_g:
                if st.button("📄 Ver Comparendos RNMC", key=f"btn_rnmc_del_{seleccionado_g}",
                             width="stretch"):
                    mostrar_dialogo_rnmc(seleccionado_g, nombre_completo_g)
        else:
            delitos_g = base_gestion.copy()
    else:
        delitos_g = base_gestion.copy()
        st.info("No hay registros de funcionarios para los filtros actuales.")

    total_casos_g = float(
        pd.to_numeric(delitos_g.get("CANTIDAD CASOS", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    total_victimas_g = float(
        pd.to_numeric(delitos_g.get("CANTIDAD VICTIMA", pd.Series(dtype=float)), errors="coerce").fillna(
            0).sum()) if "CANTIDAD VICTIMA" in delitos_g.columns else 0
    tipos_g = int(delitos_g["DELITO"].nunique()) if "DELITO" in delitos_g.columns else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta("Casos registrados", formatear_entero(total_casos_g))
    with c2:
        tarjeta("Víctimas registradas", formatear_entero(total_victimas_g))
    with c3:
        tarjeta("Tipos de delito", formatear_entero(tipos_g))

    titulo_seccion("02 · Evolución mensual de delitos")
    con_fecha_g = delitos_g.dropna(
        subset=["FECHA_HECHO"]).copy() if "FECHA_HECHO" in delitos_g.columns else pd.DataFrame()
    if not con_fecha_g.empty:
        con_fecha_g["MES_ANIO"] = con_fecha_g["FECHA_HECHO"].dt.to_period("M").astype(str)
        if "CANTIDAD CASOS" in con_fecha_g.columns:
            tendencia_g = con_fecha_g.groupby("MES_ANIO")["CANTIDAD CASOS"].sum().reset_index(name="CASOS")
        else:
            tendencia_g = con_fecha_g.groupby("MES_ANIO").size().reset_index(name="CASOS")
        fig = px.line(tendencia_g, x="MES_ANIO", y="CASOS", markers=True, text="CASOS",
                      color_discrete_sequence=[ROJO_CARMESI],
                      labels={"MES_ANIO": "Mes", "CASOS": "Cantidad de delitos"})
        fig.update_traces(line=dict(width=4, color=ROJO_CARMESI), marker=dict(size=10, color=ROJO_CARMESI),
                          textposition="top center", textfont=dict(size=13, color=ROJO_CARMESI))
        fig.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de delitos")
        mostrar_grafico(estilizar_grafico(fig))
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
            estacion_g["ESTACION"] = estacion_g["ESTACION"].astype("string").fillna("No especificada")
            estacion_g = estacion_g.sort_values("CASOS", ascending=False).head(12).sort_values("CASOS")
            fig = px.bar(estacion_g, x="CASOS", y="ESTACION", orientation="h", text="CASOS",
                         color_discrete_sequence=[ROJO_CARMESI],
                         labels={"CASOS": "Cantidad de delitos", "ESTACION": "Estación"})
            fig.update_traces(textposition="outside", marker_color=ROJO_CARMESI)
            fig.update_layout(xaxis_title="Cantidad de delitos", yaxis_title="")
            mostrar_grafico(estilizar_grafico(fig))
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
            tipos_delito_g["DELITO"] = tipos_delito_g["DELITO"].astype("string").fillna("No especificado")
            tipos_delito_g = tipos_delito_g.sort_values("CASOS", ascending=False).head(12).sort_values("CASOS")
            fig = px.bar(tipos_delito_g, x="CASOS", y="DELITO", orientation="h", text="CASOS",
                         color_discrete_sequence=[ROJO_CARMESI_CLARO],
                         labels={"CASOS": "Cantidad de delitos", "DELITO": "Tipo de delito"})
            fig.update_traces(textposition="outside", marker_color=ROJO_CARMESI_CLARO)
            fig.update_layout(xaxis_title="Cantidad de delitos", yaxis_title="")
            mostrar_grafico(estilizar_grafico(fig))
        else:
            st.info("No hay tipos de delitos para la selección actual.")

    titulo_seccion("05 · Funcionarios con más delitos de homicidio")
    if not delitos_g.empty and "DELITO" in delitos_g.columns:
        homicidios_g = delitos_g[
            delitos_g["DELITO"].astype(str).str.contains(r"\bhomicidio\b", case=False, regex=True, na=False)].copy()
        if not homicidios_g.empty:
            if "CANTIDAD CASOS" in homicidios_g.columns:
                homicidios_g["CANTIDAD CASOS"] = pd.to_numeric(homicidios_g["CANTIDAD CASOS"], errors="coerce").fillna(
                    0)
                ranking_hom_g = homicidios_g.groupby("_ID_CLAVE")["CANTIDAD CASOS"].sum().reset_index(name="HOMICIDIOS")
            else:
                ranking_hom_g = homicidios_g.groupby("_ID_CLAVE").size().reset_index(name="HOMICIDIOS")
            ranking_hom_g = ranking_hom_g.merge(maestros[["_ID_CLAVE", "GRADO", "NOMBRE"]], on="_ID_CLAVE", how="left")
            ranking_hom_g["FUNCIONARIO"] = (
                    ranking_hom_g["GRADO"].fillna("").astype(str) + " " + ranking_hom_g["NOMBRE"].fillna("").astype(
                str)).str.strip()
            ranking_hom_g = ranking_hom_g.sort_values("HOMICIDIOS", ascending=False).head(10).sort_values("HOMICIDIOS")
            fig = px.bar(ranking_hom_g, x="HOMICIDIOS", y="FUNCIONARIO", orientation="h", text="HOMICIDIOS",
                         color_discrete_sequence=[ROJO_CARMESI],
                         labels={"HOMICIDIOS": "Casos de homicidio", "FUNCIONARIO": "Funcionario"})
            fig.update_traces(textposition="outside", marker_color=ROJO_CARMESI)
            fig.update_layout(xaxis_title="Casos de homicidio", yaxis_title="")
            mostrar_grafico(estilizar_grafico(fig))
        else:
            st.info("No se encontraron delitos cuyo nombre contenga 'homicidio' para la selección actual.")

    titulo_seccion("06 · Registros delictivos")
    columnas_tabla_g = ["FECHA_HECHO", "BOLETIN", "MUNICIPIO", "DISTRITO", "ESTACION", "CAI", "CUADRANTE",
                        "GR APELLIDOS Y NOMBRES POLICIA_1", "IDENTIFICACION", "DELITO", "CANTIDAD CASOS",
                        "CANTIDAD VICTIMA"]
    mostrar_tabla(delitos_g.sort_values("FECHA_HECHO", ascending=False,
                                        na_position="last") if "FECHA_HECHO" in delitos_g.columns else delitos_g,
                  columnas_tabla_g,
                  {"FECHA_HECHO": "Fecha", "BOLETIN": "Boletín", "MUNICIPIO": "Municipio", "DISTRITO": "Distrito",
                   "ESTACION": "Estación", "CAI": "CAI", "CUADRANTE": "Cuadrante",
                   "GR APELLIDOS Y NOMBRES POLICIA_1": "Funcionario", "IDENTIFICACION": "Identificación",
                   "DELITO": "Delito", "CANTIDAD CASOS": "Casos", "CANTIDAD VICTIMA": "Víctimas"})


# ============================================================
# PANTALLA 4: SEGUIMIENTO ACTIVACIÓN AL SERVICIO
# ============================================================

elif pantalla == "Seguimiento activación al servicio":
    encabezado("SEGUIMIENTO ACTIVACIÓN AL SERVICIO",
               "Turnos cumplidos y permisos otorgados por funcionario")

    if turnos.empty or "_ID_CLAVE" not in turnos.columns:
        st.info("No se encontró el archivo REPORTE_TURNOS en la carpeta data.")
    else:
        fechas_t = turnos["FECHA_DIA"].dropna()
        unidades_t = sorted(x for x in turnos["UNIDAD"].unique() if x)
        cargos_t = sorted(x for x in turnos["CARGO_SIATH"].unique() if x)

        f1, f2, f3 = st.columns([1.2, 1.4, 1.4], gap="medium")
        with f1:
            if not fechas_t.empty:
                rango_t = st.date_input("Periodo de turnos",
                                        value=(fechas_t.min().date(), fechas_t.max().date()),
                                        min_value=fechas_t.min().date(), max_value=fechas_t.max().date(),
                                        format="DD/MM/YYYY", key="seg_periodo")
                if isinstance(rango_t, (tuple, list)):
                    if len(rango_t) == 2:
                        inicio_t, fin_t = rango_t
                    elif len(rango_t) == 1:
                        inicio_t = fin_t = rango_t[0]
                    else:
                        inicio_t = fin_t = None
                else:
                    inicio_t = fin_t = rango_t
            else:
                inicio_t = fin_t = None
                st.warning("No se encontraron fechas válidas en REPORTE_TURNOS.")
        with f2:
            unidades_sel_t = st.multiselect("Unidad", options=unidades_t, default=[],
                                            placeholder="Todas las unidades", key="seg_unidades")
        with f3:
            cargos_sel_t = st.multiselect("Cargo", options=cargos_t, default=[],
                                          placeholder="Todos los cargos", key="seg_cargos")

        st.caption("Aquí también se aplican las búsquedas por cédula y por grado/nombre del panel lateral. "
                   "El periodo y la estación del panel lateral no aplican, porque este reporte usa sus propias "
                   "unidades y fechas.")

        turnos_f, resumen_t = calcular_turnos(inicio_t, fin_t, tuple(unidades_sel_t), tuple(cargos_sel_t),
                                              cedula_busqueda, nombre_busqueda)

        if turnos_f.empty:
            st.info("No hay turnos para los filtros seleccionados.")
        else:
            zona_kpi = st.container()  # se llena más abajo, cuando ya se conoce el funcionario seleccionado

            # ---------- 01 · Tabla de funcionarios ----------
            titulo_seccion("01 · Funcionarios y turnos realizados")

            clave_estado_s = "seguimiento_funcionario_cedula"
            seleccionado_s = str(st.session_state.get(clave_estado_s, "") or "").strip()
            if seleccionado_s and seleccionado_s not in set(resumen_t["Cédula"].astype(str)):
                st.session_state.pop(clave_estado_s, None)
                seleccionado_s = ""

            ctrl_s, estado_s = st.columns([1, 4])
            with ctrl_s:
                if st.button("Mostrar todos", key="seguimiento_mostrar_todos", width="stretch"):
                    st.session_state.pop(clave_estado_s, None)
                    st.session_state.pop("tabla_funcionarios_seguimiento", None)
                    st.rerun()
            with estado_s:
                if seleccionado_s:
                    fila_act = resumen_t[resumen_t["Cédula"].astype(str) == seleccionado_s]
                    nombre_act = fila_act.iloc[0][
                        "Grado, nombres y apellidos"] if not fila_act.empty else seleccionado_s
                    st.info(f"Filtro activo · {nombre_act} · C.C. {seleccionado_s}")
                else:
                    st.caption("Haz clic en una fila para ver el detalle de turnos de ese funcionario.")

            resumen_t_mostrar = resumen_t.head(2000)
            evento_s = st.dataframe(
                resumen_t_mostrar, width="stretch", hide_index=True,
                height=min(440, 46 + 35 * min(len(resumen_t_mostrar), 11)),
                on_select="rerun", selection_mode="single-row", key="tabla_funcionarios_seguimiento",
                column_config={
                    "Grado, nombres y apellidos": st.column_config.TextColumn("Grado, nombres y apellidos",
                                                                              width="large"),
                    "Cédula": st.column_config.TextColumn("Cédula", width="medium"),
                    "Unidad": st.column_config.TextColumn("Unidad", width="medium"),
                    "Turnos": st.column_config.NumberColumn("Turnos", format="%d", width="small"),
                    "Días con servicio": st.column_config.NumberColumn("Días con servicio", format="%d", width="small"),
                    "Primer turno": st.column_config.TextColumn("Primer turno", width="small"),
                    "Último turno": st.column_config.TextColumn("Último turno", width="small"),
                },
            )
            filas_s = evento_s.selection.rows if hasattr(evento_s, "selection") else []
            if filas_s:
                idx_s = filas_s[0]
                if 0 <= idx_s < len(resumen_t):
                    cedula_elegida_s = str(resumen_t.iloc[idx_s]["Cédula"]).strip()
                    if cedula_elegida_s:
                        st.session_state[clave_estado_s] = cedula_elegida_s
                        seleccionado_s = cedula_elegida_s

            if seleccionado_s:
                turnos_sel = turnos_f[turnos_f["_ID_CLAVE"] == seleccionado_s]
                fila_sel = resumen_t[resumen_t["Cédula"].astype(str) == seleccionado_s].iloc[0]
                st.markdown(
                    f'''
                    <div style="background: linear-gradient(135deg, #F3F7FC 0%, #E8F0F8 100%); border-left: 4px solid {AZUL}; padding: 14px 18px; border-radius: 10px; margin: 8px 0 18px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <div style="color: #12345A; font-weight: 600; font-size: 14px;">👮 Vista filtrada · {html.escape(str(fila_sel["Grado, nombres y apellidos"]))} · Cédula {html.escape(seleccionado_s)} · {formatear_entero(fila_sel["Turnos"])} turnos</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
            else:
                turnos_sel = turnos_f

            # ---------- Tarjetas e indicador (siempre se ejecutan, con o sin selección) ----------
            hoy = pd.Timestamp.today().normalize()
            dias_ideal = int((hoy - pd.Timestamp(year=hoy.year, month=1, day=1)).days) + 1

            registros_sel = len(turnos_sel)
            fechas_sel = turnos_sel["FECHA_DIA"].dropna()
            if not fechas_sel.empty:
                primer_dia = fechas_sel.min()
                ultimo_dia = fechas_sel.max()
                dias_transcurridos = int((ultimo_dia - primer_dia).days) + 1
            else:
                primer_dia = ultimo_dia = None
                dias_transcurridos = 0

            if seleccionado_s:
                valor_medidor = registros_sel
                titulo_medidor = "Veces registrado / días transcurridos"
                decimales_medidor = 0
            else:
                valor_medidor = registros_sel / len(resumen_t) if len(resumen_t) else 0
                titulo_medidor = "Promedio por funcionario / días transcurridos"
                decimales_medidor = 1

            with zona_kpi:
                k1, k2, k3 = st.columns([1, 1, 1.6], gap="medium")
                with k1:
                    tarjeta("Ideal de turnos", formatear_entero(dias_ideal),
                            f"Días del año: 01/01/{hoy.year} al {hoy.strftime('%d/%m/%Y')}", alto=200)
                with k2:
                    tarjeta("Días con servicio", formatear_entero(registros_sel),
                            "Veces registrado en el archivo" if seleccionado_s
                            else "Registros de todos los funcionarios", alto=200)
                with k3:
                    mostrar_grafico(
                        grafico_medidor(valor_medidor, dias_transcurridos, titulo_medidor, decimales_medidor))

                if primer_dia is not None:
                    cobertura = (valor_medidor / dias_transcurridos * 100) if dias_transcurridos else 0
                    cobertura_txt = f"{cobertura:.1f}".replace(".", ",")
                    st.caption(
                        f"Primer registro: {primer_dia.strftime('%d/%m/%Y')} · "
                        f"Último registro: {ultimo_dia.strftime('%d/%m/%Y')} · "
                        f"Días transcurridos: {formatear_entero(dias_transcurridos)} · "
                        f"Cobertura: {cobertura_txt}%"
                    )

            # ---------- 02 · Turnos en el tiempo ----------
            titulo_seccion("02 · Turnos en el tiempo")
            con_fecha_t = turnos_sel.dropna(subset=["FECHA_DIA"])
            if not con_fecha_t.empty:
                if con_fecha_t["FECHA_DIA"].nunique() > 62:
                    clave_t = con_fecha_t["FECHA_DIA"].dt.to_period("M").astype(str)
                    etiqueta_t = "Mes"
                else:
                    clave_t = con_fecha_t["FECHA_DIA"].dt.strftime("%Y-%m-%d")
                    etiqueta_t = "Día"
                serie_t = con_fecha_t.groupby(clave_t).size().reset_index()
                serie_t.columns = ["PERIODO", "TURNOS"]
                fig = px.line(serie_t, x="PERIODO", y="TURNOS", markers=True,
                              labels={"PERIODO": etiqueta_t, "TURNOS": "Turnos"})
                fig.update_traces(line=dict(color=AZUL, width=3), marker=dict(size=8, color=DORADO))
                mostrar_grafico(estilizar_grafico(fig))
            else:
                st.info("No hay fechas válidas para construir la gráfica.")

            # ---------- 03 · Por unidad y por cargo ----------
            col_u, col_c = st.columns(2, gap="large")
            with col_u:
                titulo_seccion("03 · Turnos por unidad")
                por_unidad = (turnos_sel["UNIDAD"].replace("", "No especificada").value_counts()
                              .head(15).sort_values().reset_index())
                por_unidad.columns = ["UNIDAD", "TURNOS"]
                fig = px.bar(por_unidad, x="TURNOS", y="UNIDAD", orientation="h", text="TURNOS",
                             color_discrete_sequence=[AZUL], labels={"TURNOS": "Turnos", "UNIDAD": "Unidad"})
                fig.update_layout(yaxis_title="")
                mostrar_grafico(estilizar_grafico(fig))
            with col_c:
                titulo_seccion("04 · Turnos por cargo")
                por_cargo = (turnos_sel["CARGO_SIATH"].replace("", "No especificado").value_counts()
                             .head(12).sort_values().reset_index())
                por_cargo.columns = ["CARGO", "TURNOS"]
                fig = px.bar(por_cargo, x="TURNOS", y="CARGO", orientation="h", text="TURNOS",
                             color_discrete_sequence=[DORADO], labels={"TURNOS": "Turnos", "CARGO": "Cargo"})
                fig.update_layout(yaxis_title="")
                mostrar_grafico(estilizar_grafico(fig))

            # ---------- 05 · Permisos otorgados ----------
            titulo_seccion("05 · Permisos otorgados")
            if permisos.empty or "_ID_CLAVE" not in permisos.columns:
                st.info("No se encontró el archivo REPORTE_PERMISOS en la carpeta data.")
            elif not seleccionado_s:
                st.info("Selecciona un funcionario en la tabla para ver los permisos que le fueron otorgados.")
            else:
                permisos_sel = permisos[permisos["_ID_CLAVE"] == seleccionado_s]
                if inicio_t is not None and fin_t is not None:
                    f_p = permisos_sel["FECHA_DIA"]
                    permisos_sel = permisos_sel[
                        f_p.isna() | ((f_p >= pd.Timestamp(inicio_t)) & (f_p <= pd.Timestamp(fin_t)))]

                if permisos_sel.empty:
                    st.info("Este funcionario no tiene permisos registrados en el periodo seleccionado.")
                else:
                    permisos_sel = permisos_sel.sort_values("FECHA_DIA", ascending=False, na_position="last")
                    p1, p2, p3 = st.columns(3, gap="medium")
                    with p1:
                        tarjeta("Permisos otorgados", formatear_entero(len(permisos_sel)),
                                "Registros sin servicio en el periodo")
                    with p2:
                        tarjeta("Tipos de novedad",
                                formatear_entero(permisos_sel["DESCRIPCION_NOVEDAD"].replace("", pd.NA).nunique()),
                                "Descripciones distintas")
                    with p3:
                        tarjeta("Último permiso", fecha_legible(permisos_sel["FECHA_DIA"].max()),
                                "Fecha más reciente")

                    st.markdown("##### Permisos por tipo de novedad")
                    por_tipo = (permisos_sel["DESCRIPCION_NOVEDAD"].replace("", "Sin descripción")
                                .value_counts().reset_index())
                    por_tipo.columns = ["Novedad / permiso", "Cantidad"]
                    st.dataframe(por_tipo, width="stretch", hide_index=True)

                    st.markdown("##### Detalle de permisos")
                    detalle_p = permisos_sel.copy()
                    detalle_p["FECHA"] = detalle_p["FECHA_DIA"].dt.strftime("%d/%m/%Y").fillna("")
                    mostrar_tabla(
                        detalle_p,
                        ["FECHA", "TURNO", "TIPO_MINUTA", "UNIDAD", "DESCRIPCION_NOVEDAD",
                         "CODIGO_CUADRANTE", "CARGO_SIATH", "ROL_SIATH"],
                        {"TIPO_MINUTA": "Tipo de minuta", "UNIDAD": "Unidad",
                         "DESCRIPCION_NOVEDAD": "Descripción de la novedad",
                         "CODIGO_CUADRANTE": "Código de cuadrante", "CARGO_SIATH": "Cargo", "ROL_SIATH": "Rol"},
                    )
                    st.caption("Se aplica el periodo seleccionado arriba. Un permiso corresponde a los registros "
                               "de REPORTE_PERMISOS donde el funcionario no estuvo en servicio.")

            # ---------- 06 · Registros ----------
            titulo_seccion("06 · Registros de turnos")
            registros_t = turnos_sel.sort_values("FECHA_DIA", ascending=False, na_position="last").copy()
            registros_t["FECHA"] = registros_t["FECHA_DIA"].dt.strftime("%d/%m/%Y").fillna("")
            limite_filas = 2000
            truncado = len(registros_t) > limite_filas
            mostrar_tabla(
                registros_t.head(limite_filas),
                ["FECHA", "UNIDAD", "IDENTIFICACION_TURNO", "NOMBRE_COMPLETO", "CODIGO_CUADRANTE", "CARGO_SIATH"],
                {"UNIDAD": "Unidad", "IDENTIFICACION_TURNO": "Cédula", "NOMBRE_COMPLETO": "Grado, nombres y apellidos",
                 "CODIGO_CUADRANTE": "Código de cuadrante", "CARGO_SIATH": "Cargo"},
            )
            if truncado:
                st.caption(f"Se muestran los {limite_filas:,} turnos más recientes de {len(registros_t):,}. "
                           "Selecciona un funcionario para ver todos los suyos.")

# ============================================================
# PIE
# ============================================================

st.markdown(
    '<div class="pie">DASHBOARD MEBAR · Panel de análisis institucional · La información depende de los reportes Excel cargados.</div>',
    unsafe_allow_html=True)
