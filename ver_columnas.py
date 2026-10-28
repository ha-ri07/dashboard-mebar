import pandas as pd

archivos = {
    "DELITOS": "data/REPORTE_DELITOS.xlsx",
    "OPERATIVIDAD": "data/REPORTE_OPERATIVIDAD.xlsx",
    "TAHUM": "data/REPORTE_TAHUM.xlsx"
}

for nombre, ruta in archivos.items():
    print("\n" + "=" * 50)
    print(nombre)
    print("=" * 50)

    df = pd.read_excel(ruta)

    for col in df.columns:
        print(col)