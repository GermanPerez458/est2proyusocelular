import os
import sys
import uuid
import numpy as np
import logging
import traceback
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from utils import data_loader 

# Configuracion de rutas del sistema
BASE_DIR = os.path.abspath(os.path.dirname(__file__)) 
ROOT_DIR = os.path.dirname(BASE_DIR) 
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, ROOT_DIR)

# Importacion de modulos de calculo estadistico
try:
    from capitulos.capitulos_integrados import (
        capitulo_1_descriptiva,
        capitulo_2_estimacion,
        capitulo_3_intervalos,
        capitulo_4_hipotesis,
        capitulo_5_comparacion
    )
except ImportError as e:
    logging.error(f"Error al importar modulos: {e}")
    pass

app = Flask(__name__)
app.config.update({
    "SECRET_KEY": "requiem-stats-key",
    "MAX_CONTENT_LENGTH": 16 * 1024 * 1024
})
logger = logging.getLogger("RequiemApp")

# Gestion de datos y cache para optimizar velocidad
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.cache_resultados = {}

    def create_session(self, datos, fuente="Desconocida"):
        session_id = str(uuid.uuid4())[:12]
        stats = {
            "n": int(len(datos)),
            "media": float(np.mean(datos)),
            "std": float(np.std(datos, ddof=1))
        }
        self.sessions[session_id] = {
            "datos": datos,
            "stats": stats,
            "fuente": fuente,
            "timestamp": datetime.now()
        }
        return session_id, stats

    def get_session(self, session_id):
        return self.sessions.get(session_id)

    def obtener_cache(self, session_id, umbral, confianza):
        key = f"{session_id}_{umbral}_{confianza}"
        return self.cache_resultados.get(key)

    def guardar_cache(self, session_id, umbral, confianza, resultado):
        key = f"{session_id}_{umbral}_{confianza}"
        self.cache_resultados[key] = resultado

session_manager = SessionManager()

def serializar_numpy(obj):
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, (np.integer, np.int64)): return int(obj)
    if isinstance(obj, (np.floating, np.float64)): return float(obj)
    if isinstance(obj, dict): return {k: serializar_numpy(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [serializar_numpy(v) for v in obj]
    return obj

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No se recibió el archivo"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    # Procesamiento flexible del CSV
    resultado = data_loader.procesar_csv_flexible(file)
    
    if resultado is None:
        return jsonify({"error": "No se encontraron columnas numéricas (horas) válidas"}), 400

    datos_array = resultado["array"]
    datos_preview = resultado["preview"]

    validacion = data_loader.validar_datos(datos_array)
    
    if not validacion["valido"]:
        return jsonify({"error": " ".join(validacion["errores"])}), 400

    # Crear sesión con los datos procesados
    session_id, stats = session_manager.create_session(datos_array, fuente=file.filename)

    return jsonify({
        "session_id": session_id,
        "estadisticas": stats,
        "datos": datos_preview,
        "filas": datos_preview,
        "conteo": {
            "filas_validas": len(datos_array)
        }
    })

@app.route("/api/generar_ejemplo", methods=["POST"])
def generar_ejemplo():
    try:
        # 1. Obtener parámetros 
        params = request.get_json()
        n = int(params.get('n', 100))
        media = float(params.get('media', 5.5))
        std = float(params.get('desviacion', 1.5))
        
        # 2. Generar datos usando distribución Gamma 
        if std <= 0: 
            std = 0.1 
        
        shape = (media / std)**2
        scale = (std**2) / media
        
        datos = np.random.gamma(shape, scale, n)
        datos = np.clip(datos, 0.5, 24)  
        
        # 3. Formatear para la tabla del Frontend
        datos_preview = [{"Horas (Simulado)": round(float(x), 2)} for x in datos]

        # 4. Crear sesión y estadísticas
        session_id, stats = session_manager.create_session(datos, fuente="Muestra de Control")
        
        # 5. Retornar respuesta COMPLETA
        return jsonify({
            "success": True, 
            "session_id": session_id, 
            "estadisticas": stats,
            "datos": datos_preview, 
            "filas": datos_preview  
        })

    except Exception as e:
        print(f"Error en generar_ejemplo: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/analisis_completo", methods=["POST"])
def analisis_completo():
    try:
        params = request.get_json()
        session_id = params.get("session_id")
        umbral = float(params.get("umbral", 5.0))
        nivel_confianza = float(params.get("nivel_confianza", 0.95))
        
        # Verificar sesión
        sesion = session_manager.get_session(session_id)
        if not sesion:
            return jsonify({"error": "Sesión no válida o expirada"}), 400
        
        datos = sesion["datos"]
        
        # Verificar cache
        cached = session_manager.obtener_cache(session_id, umbral, nivel_confianza)
        if cached:
            return jsonify(cached)
        
        # Ejecutar análisis
        resultado = {}
        
        # Capítulo 1: Estadística Descriptiva
        try:
            cap1 = capitulo_1_descriptiva(datos)
            resultado["capitulo1_descriptiva"] = serializar_numpy(cap1)
        except Exception as e:
            logger.error(f"Error en capítulo 1: {e}")
            resultado["capitulo1_descriptiva"] = {"error": str(e)}
        
        # Capítulo 2: Estimación Puntual
        try:
            cap2 = capitulo_2_estimacion(datos)
            resultado["capitulo2_estimacion"] = serializar_numpy(cap2)
        except Exception as e:
            logger.error(f"Error en capítulo 2: {e}")
            resultado["capitulo2_estimacion"] = {"error": str(e)}
        
        # Capítulo 3: Intervalos de Confianza
        try:
            cap3 = capitulo_3_intervalos(datos, nivel_confianza)
            resultado["capitulo3_intervalos"] = serializar_numpy(cap3)
        except Exception as e:
            logger.error(f"Error en capítulo 3: {e}")
            resultado["capitulo3_intervalos"] = {"error": str(e)}
        
        # Capítulo 4: Prueba de Hipótesis
        try:
            cap4 = capitulo_4_hipotesis(datos, umbral, nivel_confianza)
            resultado["capitulo4_hipotesis"] = serializar_numpy(cap4)
        except Exception as e:
            logger.error(f"Error en capítulo 4: {e}")
            resultado["capitulo4_hipotesis"] = {"error": str(e)}
        
        # Capítulo 5: Comparación
        try:
            cap5 = capitulo_5_comparacion(datos, umbral, nivel_confianza)
            resultado["capitulo5_comparacion"] = serializar_numpy(cap5)
        except Exception as e:
            logger.error(f"Error en capítulo 5: {e}")
            resultado["capitulo5_comparacion"] = {"error": str(e)}
        
        # Guardar en cache
        session_manager.guardar_cache(session_id, umbral, nivel_confianza, resultado)
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Error crítico en analisis_completo: {traceback.format_exc()}")
        return jsonify({"error": f"Error en el análisis: {str(e)}"}), 500

@app.route("/api/analisis_rapido", methods=["POST"])
def health_check():
    return jsonify({"status": "ready"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
