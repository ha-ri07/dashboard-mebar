from pathlib import Path
from time import perf_counter
import gc

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
    return _optimizar_dtypes(_leer_archivo(nombre_base))


def _leer_archivo(nombre_base: str) -> pd.DataFrame:
    """Lee un archivo sin caché individual, conservando Excel -> Parquet."""
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


def _firma_archivos(nombres: tuple[str, ...]) -> tuple[tuple, ...]:
    """Devuelve la firma de todos los archivos existentes de un grupo."""
    firma = []
    for nombre in nombres:
        for ext in (".parquet", *EXTENSIONES_EXCEL):
            ruta = DATA_DIR / f"{nombre}{ext}"
            if ruta.is_file():
                stat = ruta.stat()
                firma.append((nombre, ext, stat.st_mtime_ns, stat.st_size))
    return tuple(firma)


def _firma_archivo(nombre_base: str) -> tuple[tuple, ...]:
    """Devuelve la firma de un reporte, incluyendo sus formatos disponibles."""
    return _firma_archivos((nombre_base,))


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


def _optimizar_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce memoria en textos de baja cardinalidad y columnas numéricas."""
    total_filas = len(df)
    if total_filas == 0:
        return df

    for columna in df.select_dtypes(include=["object", "string"]).columns:
        serie = df[columna]
        numerica = pd.to_numeric(serie, errors="coerce")
        valores_no_nulos = serie.notna().sum()
        if valores_no_nulos and numerica.notna().sum() >= valores_no_nulos * 0.8:
            df[columna] = pd.to_numeric(
                numerica,
                downcast="integer" if pd.api.types.is_integer_dtype(numerica) else "float",
            )
            continue
        valores_unicos = df[columna].nunique(dropna=False)
        if valores_unicos < total_filas * 0.5:
            df[columna] = serie.astype("category")

    for columna in df.columns:
        serie = df[columna]
        if pd.api.types.is_integer_dtype(serie):
            df[columna] = pd.to_numeric(serie, downcast="integer")
        elif pd.api.types.is_float_dtype(serie):
            df[columna] = pd.to_numeric(serie, downcast="float")

    return df


@st.cache_resource(show_spinner=False, max_entries=8)
def _cargar_reporte_optimizado(nombre_base: str, firma: tuple[tuple, ...]) -> pd.DataFrame:
    """Carga y optimiza un reporte aislado sin retener copias intermedias."""
    df = _leer_archivo(nombre_base)
    if df.empty:
        return df
    optimizado = _optimizar_dtypes(df)
    del df
    gc.collect()
    return optimizado


@st.cache_resource(show_spinner=False, max_entries=4)
def _cargar_delitos_operatividad_cache(
    firma_delitos: tuple[tuple, ...], firma_operatividad: tuple[tuple, ...]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga solo los dos reportes base usados por los paneles analíticos."""
    delitos = _optimizar_dtypes(_leer_archivo("REPORTE_DELITOS"))
    operatividad = _optimizar_dtypes(_leer_archivo("REPORTE_OPERATIVIDAD"))
    gc.collect()
    return delitos, operatividad


@st.cache_resource(show_spinner=False, max_entries=4)
def _cargar_antecedentes_combinados(
    nombres: tuple[str, ...], tipo: str, firma: tuple[tuple, ...]
) -> pd.DataFrame:
    """Lee, combina y cachea un grupo mensual completo."""
    partes = []
    for mes, nombre in zip(MESES, nombres):
        df_mes = _leer_archivo(nombre)
        if not df_mes.empty:
            df_mes["MES_CONSULTA"] = mes
            df_mes["TIPO_CONSULTA"] = tipo
            partes.append(df_mes)

    if not partes:
        return pd.DataFrame()

    combinado = pd.concat(partes, ignore_index=True, sort=False)
    del partes, df_mes
    gc.collect()
    return _optimizar_dtypes(combinado)


def cargar_delitos_operatividad() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga únicamente delitos y operatividad para los paneles principales."""
    return _cargar_delitos_operatividad_cache(
        _firma_archivo("REPORTE_DELITOS"),
        _firma_archivo("REPORTE_OPERATIVIDAD"),
    )


def cargar_antecedentes_persona() -> pd.DataFrame:
    """Carga antecedentes de persona solo cuando la sección los solicita."""
    nombres = tuple(f"REPORTE_ANTECEDENTES_PERSONA_{mes}" for mes in MESES)
    return _cargar_antecedentes_combinados(nombres, "PERSONA", _firma_archivos(nombres))


def cargar_antecedentes_vehiculo() -> pd.DataFrame:
    """Carga antecedentes de vehículo solo cuando la sección los solicita."""
    nombres = tuple(f"REPORTE_ANTECEDENTES_VEHICULO_{mes}" for mes in MESES)
    return _cargar_antecedentes_combinados(nombres, "VEHICULO", _firma_archivos(nombres))


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
    delitos = _leer(nombres_principales[0])
    operatividad = _leer(nombres_principales[1])
    tahum = _cargar_antecedentes_combinados(
        tuple(nombres_persona), "PERSONA", _firma_archivos(tuple(nombres_persona))
    )
    vehiculos = _cargar_antecedentes_combinados(
        tuple(nombres_vehiculo), "VEHICULO", _firma_archivos(tuple(nombres_vehiculo))
    )

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
    return _cargar_reporte_optimizado("REPORTE_RNMC", _firma_archivo("REPORTE_RNMC"))


def cargar_turnos() -> pd.DataFrame:
    """Carga REPORTE_TURNOS: cada registro es un turno cumplido por un funcionario."""
    return _cargar_reporte_optimizado("REPORTE_TURNOS", _firma_archivo("REPORTE_TURNOS"))


def cargar_permisos() -> pd.DataFrame:
    """Carga REPORTE_PERMISOS: registros de minuta con novedades/permisos por funcionario."""
    return _cargar_reporte_optimizado("REPORTE_PERMISOS", _firma_archivo("REPORTE_PERMISOS"))


def cargar_tahum() -> pd.DataFrame:
    """Carga el padrón pequeño de funcionarios usado para construir maestros."""
    return _cargar_reporte_optimizado("REPORTE_TAHUM", _firma_archivo("REPORTE_TAHUM"))
