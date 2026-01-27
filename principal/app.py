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
    sys.exit(1)

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

@app.route("/api/upload", methods=["POST"])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No se recibio archivo"}), 400
    
    file = request.files['file']
    datos = data_loader.cargar_csv(file)
    
    if datos is None or len(datos) == 0:
        return jsonify({"error": "Datos no validos"}), 400

    session_id, stats = session_manager.create_session(datos, fuente=file.filename)
    return jsonify({"session_id": session_id, "datos": {"filas_validas": len(datos)}, "estadisticas": stats})

@app.route("/api/generar_ejemplo", methods=["POST"])
def generar_ejemplo():
    try:
        params = request.get_json()
        n, media, std = int(params.get('n', 100)), float(params.get('media', 5.5)), float(params.get('desviacion', 1.5))
        shape, scale = (media / std)**2, (std**2) / media
        datos = np.random.gamma(shape, scale, n)
        datos = np.clip(datos, 0.5, 24) 

        session_id, stats = session_manager.create_session(datos, fuente="Simulado")
        return jsonify({"success": True, "session_id": session_id, "estadisticas": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/analisis_completo", methods=["POST"])
def analisis_completo():
    try:
        payload = request.get_json()
        session_id = payload.get("session_id")
        umbral = float(payload.get("umbral", 5.0))
        confianza = float(payload.get("nivel_confianza", 0.95))
        
        # 1. Intentar recuperar del cache
        cache = session_manager.obtener_cache(session_id, umbral, confianza)
        if cache:
            return jsonify(cache)

        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Sesion no encontrada"}), 404

        datos = session["datos"]

        # 2. Ejecutar calculos 
        resultado = serializar_numpy({
            "capitulo1_descriptiva": capitulo_1_descriptiva(datos),
            "capitulo2_estimacion": capitulo_2_estimacion(datos),
            "capitulo3_intervalos": capitulo_3_intervalos(datos, nivel_confianza=confianza),
            "capitulo4_hipotesis": capitulo_4_hipotesis(datos, umbral=umbral, alpha=(1-confianza)),
            "capitulo5_comparacion": capitulo_5_comparacion(datos, datos * 0.9),
            "metadata": {"session_id": session_id, "n": len(datos), "timestamp": datetime.now().isoformat()}
        })

        # 3. Guardar en cache 
        session_manager.guardar_cache(session_id, umbral, confianza, resultado)
        
        return jsonify(resultado)

    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/api/analisis_rapido", methods=["POST"])
def health_check():
    return jsonify({"status": "ready"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)