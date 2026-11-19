from pathlib import Path
from time import perf_counter

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MESES = (
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE"
)

EXTENSIONES_EXCEL = (".xlsx", ".xls")


# ============================================================
# CONVERSIÓN EXCEL -> PARQUET
#
# La primera vez que se lee un Excel se convierte a .parquet en la
# misma carpeta data/. En las siguientes ejecuciones se lee solo el
# Parquet, que es mucho más rápido. Si el Excel se modifica (es más
# nuevo que su Parquet), se reconvierte automáticamente.
#
# Requiere: pip install pyarrow python-calamine
# ============================================================
def _a_parquet_seguro(df: pd.DataFrame, destino: Path) -> None:
    """Guarda en Parquet; si hay columnas con tipos mezclados, las pasa a texto."""
    try:
        df.to_parquet(destino, index=False)
    except Exception:
        df = df.copy()
        for columna in df.select_dtypes(include="object").columns:
            df[columna] = df[columna].map(lambda x: None if pd.isna(x) else str(x))
        df.to_parquet(destino, index=False)


def _leer_excel(ruta: Path) -> pd.DataFrame:
    """Lee un Excel con calamine (rápido); si no está instalado, usa openpyxl/xlrd."""
    try:
        return pd.read_excel(ruta, engine="calamine")
    except ImportError:
        motor = "openpyxl" if ruta.suffix.lower() == ".xlsx" else "xlrd"
        return pd.read_excel(ruta, engine=motor)


# ============================================================
# LECTURA DE UN ARCHIVO CON CACHÉ DE RECURSOS
#
# Se usa @st.cache_resource (y no cache_data) porque devuelve el
# DataFrame sin serializarlo en cada rerun.
#
# Regla de oro: NO modificar in-place el DataFrame devuelto.
# Todo el código aguas abajo ya hace .copy() antes de escribir.
# ============================================================
@st.cache_resource(show_spinner=False, max_entries=40)
def _leer_archivo_cacheado(nombre_base: str, firma: tuple) -> pd.DataFrame:
    # `firma` (extensión, mtime y tamaño de cada archivo) solo sirve para
    # invalidar la caché cuando algún archivo cambia.
    parquet = DATA_DIR / f"{nombre_base}.parquet"
    excel = next(
        (
            DATA_DIR / f"{nombre_base}{ext}"
            for ext in EXTENSIONES_EXCEL
            if (DATA_DIR / f"{nombre_base}{ext}").is_file()
        ),
        None,
    )

    # Convertir si hay Excel y el Parquet no existe o está desactualizado.
    if excel is not None and (
        not parquet.is_file() or parquet.stat().st_mtime < excel.stat().st_mtime
    ):
        df = _leer_excel(excel)
        try:
            _a_parquet_seguro(df, parquet)
        except Exception:
            # Si no se puede escribir el Parquet (permisos, falta pyarrow),
            # se devuelve el DataFrame leído del Excel igualmente.
            return df

    if parquet.is_file():
        return pd.read_parquet(parquet)

    return pd.DataFrame()


def _leer(nombre_base: str) -> pd.DataFrame:
    """Lee un reporte usando caché; si no existe, devuelve un DataFrame vacío."""
    firma = []
    for ext in (".parquet", *EXTENSIONES_EXCEL):
        ruta = DATA_DIR / f"{nombre_base}{ext}"
        if ruta.is_file():
            stat = ruta.stat()
            firma.append((ext, stat.st_mtime_ns, stat.st_size))

    if not firma:
        return pd.DataFrame()

    return _leer_archivo_cacheado(nombre_base, tuple(firma))


def _leer_lote(nombres: list[str]) -> dict[str, pd.DataFrame]:
    """Lee los reportes de forma secuencial (predecible y sin overhead)."""
    return {nombre: _leer(nombre) for nombre in nombres}


# ============================================================
# CARGA DE TODOS LOS REPORTES
# ============================================================
def cargar_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carga delitos, operatividad y antecedentes mensuales de persona y vehículo.

    Devuelve, en este orden: delitos, operatividad, antecedentes_persona,
    antecedentes_vehiculo. Los datos originales se conservan y se añaden las
    columnas MES_CONSULTA y TIPO_CONSULTA a los reportes mensuales.
    """
    inicio = perf_counter()

    nombres_principales = ["REPORTE_DELITOS", "REPORTE_OPERATIVIDAD"]
    nombres_persona = [f"REPORTE_ANTECEDENTES_PERSONA_{mes}" for mes in MESES]
    nombres_vehiculo = [f"REPORTE_ANTECEDENTES_VEHICULO_{mes}" for mes in MESES]
    todos = nombres_principales + nombres_persona + nombres_vehiculo

    cargados = _leer_lote(todos)

    delitos = cargados["REPORTE_DELITOS"]
    operatividad = cargados["REPORTE_OPERATIVIDAD"]

    def combinar_mensuales(nombres: list[str], tipo: str) -> pd.DataFrame:
        partes = []
        for mes, nombre in zip(MESES, nombres):
            df_mes = cargados[nombre]
            if not df_mes.empty:
                # Copiar únicamente cuando se van a añadir columnas, para no
                # modificar el DataFrame almacenado en la caché individual.
                parte = df_mes.copy()
                parte["MES_CONSULTA"] = mes
                parte["TIPO_CONSULTA"] = tipo
                partes.append(parte)

        if not partes:
            return pd.DataFrame()
        return pd.concat(partes, ignore_index=True, sort=False)

    tahum = combinar_mensuales(nombres_persona, "PERSONA")
    vehiculos = combinar_mensuales(nombres_vehiculo, "VEHICULO")

    # Diagnóstico de bajo impacto: solo muestra cantidad de filas y tiempo total.
    duracion = perf_counter() - inicio
    st.session_state["_diagnostico_carga_excel"] = {
        "segundos": round(duracion, 2),
        "delitos_filas": len(delitos),
        "operatividad_filas": len(operatividad),
        "persona_filas": len(tahum),
        "vehiculo_filas": len(vehiculos),
    }

    return delitos, operatividad, tahum, vehiculos

def cargar_rnmc() -> pd.DataFrame:
    """Carga REPORTE_RNMC (comparendos del Registro Nacional de Medidas Correctivas)."""
    return _leer("REPORTE_RNMC")


def cargar_turnos() -> pd.DataFrame:
    """Carga REPORTE_TURNOS: cada registro es un turno cumplido por un funcionario."""
    return _leer("REPORTE_TURNOS")


def cargar_permisos() -> pd.DataFrame:
    """Carga REPORTE_PERMISOS: registros de minuta con novedades/permisos por funcionario."""
    return _leer("REPORTE_PERMISOS")