import os
import io
import numpy as np
import pandas as pd

def procesar_csv_flexible(file_source):
    """
    Procesa un archivo CSV de manera flexible, detectando automáticamente
    la columna de horas de uso del celular.
    
    Args:
        file_source: Puede ser un path (str) o un objeto FileStorage de Flask
    
    Returns:
        dict con 'array' (np.array) y 'preview' (list de dicts) o None si falla
    """
    try:
        # Determinar si es path o archivo en memoria
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                return None
            df = pd.read_csv(file_source, sep=None, engine='python')
        else:
            # Leer archivo en memoria (Flask FileStorage)
            content = file_source.read().decode("utf-8-sig") 
            file_source.seek(0) 
            df = pd.read_csv(io.StringIO(content), sep=None, engine='python')

        # Buscar columna objetivo (horas de uso)
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
            # Limpiar datos
            df_limpio = df[[columna_objetivo]].copy()
            df_limpio[columna_objetivo] = pd.to_numeric(df_limpio[columna_objetivo], errors='coerce')
            df_limpio = df_limpio.dropna()
            df_limpio = df_limpio[(df_limpio[columna_objetivo] > 0) & (df_limpio[columna_objetivo] <= 24)]
            
            # Retornar array para cálculos y preview para UI
            return {
                "array": df_limpio[columna_objetivo].values.astype(float),
                "preview": df_limpio.to_dict(orient='records')  # [{col: val}, ...]
            }
        return None
    
    except Exception as e:
        print(f"Error crítico en Data Loader: {e}")
        return None

def generar_horas_aleatorias(n=100, media=5.8, desviacion=1.2, seed=None):
    """
    Genera datos simulados usando distribución Gamma (más realista para horas de uso).
    
    Args:
        n: Tamaño de muestra
        media: Media deseada
        desviacion: Desviación estándar deseada
        seed: Semilla para reproducibilidad
    
    Returns:
        np.array de valores simulados
    """
    rng = np.random.default_rng(seed)
    
    # Parametrización de distribución Gamma
    if desviacion <= 0:
        desviacion = 0.1
    
    shape = (media / desviacion)**2
    scale = (desviacion**2) / media
    
    datos = rng.gamma(shape, scale, size=n)
    
    # Limitar a rango realista de horas (0.5 - 24)
    return np.clip(datos, 0.5, 24).astype(float)

def validar_datos(datos):
    """
    Valida que los datos sean adecuados para análisis estadístico.
    
    Args:
        datos: np.array o list de valores numéricos
    
    Returns:
        dict con estado de validación, errores, advertencias y estadísticas básicas
    """
    if datos is None or len(datos) == 0:
        return {"valido": False, "errores": ["No se encontraron datos numéricos válidos"]}
    
    arr = np.array(datos)
    errores = []
    advertencias = []

    # Validaciones críticas
    if len(arr) < 3:
        errores.append("Muestra insuficiente (mínimo 3)")
    if np.all(arr == arr[0]):
        errores.append("Varianza cero: todos los datos son iguales")
    
    # Advertencias
    if len(arr) < 30:
        advertencias.append("Muestra pequeña para inferencia robusta (n < 30)")

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "advertencias": advertencias,
        "n": int(len(arr)),
        "estadisticas": {
            "media": float(np.mean(arr)),
            "std": float(np.std(arr, ddof=1)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr))
        }
    }

# Alias para compatibilidad
cargar_csv = procesar_csv_flexible
generar_datos_ejemplo = generar_horas_aleatorias
