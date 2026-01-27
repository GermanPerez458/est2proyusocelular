import os
import io
import numpy as np
import pandas as pd

def procesar_csv_flexible(file_source):
    
    try:
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                return None
            df = pd.read_csv(file_source, sep=None, engine='python')
        else:
            content = file_source.read().decode("utf-8-sig") 
            file_source.seek(0) 
            df = pd.read_csv(io.StringIO(content), sep=None, engine='python')

        columna_objetivo = None
        for col in df.columns:
            normalized = col.lower().strip()
            if any(p in normalized for p in ['horas_uso', 'uso', 'tiempo', 'horas', 'time']):
                columna_objetivo = col
                break
        
        if not columna_objetivo:
            cols_num = df.select_dtypes(include=[np.number]).columns
            if len(cols_num) > 0:
                columna_objetivo = cols_num[0]

        if columna_objetivo:
            datos = pd.to_numeric(df[columna_objetivo], errors='coerce').dropna()
            datos = datos[(datos > 0) & (datos <= 24)]
            return datos.values.astype(float)
        
        return None
    except Exception as e:
        print(f"Error crítico en Data Loader: {e}")
        return None

def generar_horas_aleatorias(n=100, media=5.8, desviacion=1.2, seed=None):
    """
    Genera datos simulados. Nota: Se usa Normal para simular horas 
    pero se limita al rango 1-24.
    """
    rng = np.random.default_rng(seed)
    datos = rng.normal(loc=media, scale=desviacion, size=n)
    return np.clip(datos, 1, 24).astype(float)

def validar_datos(datos):
    """
    Retorna un diccionario con el estado de salud de los datos.
    """
    if datos is None or len(datos) == 0:
        return {"valido": False, "errores": ["No se encontraron datos numéricos válidos"]}
    
    arr = np.array(datos)
    errores = []
    advertencias = []

    if len(arr) < 3:
        errores.append("Muestra insuficiente (mínimo 3)")
    if np.all(arr == arr[0]):
        errores.append("Varianza cero: todos los datos son iguales")
    if len(arr) < 30:
        advertencias.append("Muestra pequeña para inferencia robusta (n < 30)")

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "advertencias": advertencias,
        "n": int(len(arr)),
        "estadisticas": {
            "media": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr))
        }
    }

cargar_csv = procesar_csv_flexible
generar_datos_ejemplo = generar_horas_aleatorias