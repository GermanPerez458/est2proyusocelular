import numpy as np
from scipy import stats
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# UTILIDADES
def _preparar_datos(datos) -> np.ndarray:
    """Valida y limpia datos para análisis estadístico."""
    datos = np.asarray(datos, dtype=np.float64)
    datos = datos[~np.isnan(datos) & ~np.isinf(datos)]
    if datos.size < 2:
        raise ValueError("Se requieren al menos 2 observaciones válidas")
    return datos

def _formatear_numero(valor: float, decimales: int = 4) -> float:
    """Formatea número para visualización limpia."""
    if np.isnan(valor) or np.isinf(valor):
        return 0.0
    return round(float(valor), decimales)

def envolver_capitulo(
    *,
    titulo: str,
    descripcion: str,
    resultados: Dict[str, Any],
    desarrollo_latex: str,
    grafico_datos: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Estructura estándar de respuesta para frontend de Requiem Engine."""
    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "resultados": resultados,
        "formulas": {
            "latex": desarrollo_latex,
            "pasos": ""  # Los pasos se integran en el HTML del desarrollo_latex
        },
        "grafico_datos": grafico_datos
    }


# CAPÍTULOS

def capitulo_1_descriptiva(datos: np.ndarray) -> Dict[str, Any]:
    try:
        datos = _preparar_datos(datos)
        n = datos.size
        suma_xi = np.sum(datos)
        media = np.mean(datos)
        suma_desv_cuadrado = np.sum((datos - media)**2)
        varianza = suma_desv_cuadrado / (n-1)
        desviacion = np.sqrt(varianza)

        resultados = {
            "Tamaño (n)": int(n),
            "Media (X̄)": _formatear_numero(media),
            "Varianza (s²)": _formatear_numero(varianza),
            "Desviación (s)": _formatear_numero(desviacion)
        }

        desarrollo = f"""
        <div class="space-y-4">
            <div class="bg-blue-500/10 p-4 rounded-lg border border-blue-500/30">
                <p class="text-[11px] text-blue-400 font-bold uppercase mb-2">1. Medida de Tendencia Central</p>
                $$\\bar{{X}} = \\frac{{\\sum X_i}}{{n}} = \\frac{{{suma_xi:.4f}}}{{{n}}} = {media:.4f}$$
            </div>
            <div class="bg-green-500/10 p-4 rounded-lg border border-green-500/30">
                <p class="text-[11px] text-green-400 font-bold uppercase mb-2">2. Medida de Dispersión</p>
                $$s = \\sqrt{{\\frac{{\\sum(X_i-\\bar{{X}})^2}}{{n-1}}}} = \\sqrt{{{varianza:.4f}}} = {desviacion:.4f}$$
            </div>
        </div>
        """

        return envolver_capitulo(
            titulo="Capítulo 1: Análisis Descriptivo",
            descripcion="Exploración de las propiedades fundamentales de la muestra.",
            resultados=resultados,
            desarrollo_latex=desarrollo,
            grafico_datos={"tipo": "histograma", "data": datos.tolist()}
        )
    except Exception as e:
        logger.error(f"Error Cap 1: {e}")
        raise

def capitulo_2_estimacion(datos: np.ndarray) -> Dict[str, Any]:
    try:
        datos = _preparar_datos(datos)
        n = datos.size
        media = np.mean(datos)
        s = np.std(datos, ddof=1)
        se = s / np.sqrt(n)

        resultados = {
            "Media Muestral": _formatear_numero(media),
            "Error Estándar": _formatear_numero(se),
            "Precisión Estimada": _formatear_numero(1/se if se > 0 else 0)
        }

        desarrollo = f"""
        <div class="bg-purple-500/10 p-4 rounded-lg border border-purple-500/30">
            <p class="text-[11px] text-purple-400 font-bold uppercase mb-2">Error Estándar de la Media</p>
            $$SE(\\bar{{X}}) = \\frac{{s}}{{\\sqrt{{n}}}} = \\frac{{{s:.4f}}}{{\\sqrt{{{n}}}}} = {se:.4f}$$
        </div>
        """

        return envolver_capitulo(
            titulo="Capítulo 2: Estimación Puntual",
            descripcion="Inferencia del parámetro poblacional a partir de estadísticos.",
            resultados=resultados,
            desarrollo_latex=desarrollo,
            grafico_datos={"tipo": "boxplot", "data": datos.tolist()}
        )
    except Exception as e:
        logger.error(f"Error Cap 2: {e}")
        raise

def capitulo_3_intervalos(datos: np.ndarray, nivel_confianza: float = 0.95) -> Dict[str, Any]:
    try:
        datos = _preparar_datos(datos)
        n = datos.size
        media = np.mean(datos)
        se = np.std(datos, ddof=1)/np.sqrt(n)
        t_critico = stats.t.ppf((1+nivel_confianza)/2, df=n-1)
        margen = t_critico * se
        li, ls = media - margen, media + margen

        resultados = {
            "Confianza": f"{int(nivel_confianza*100)}%",
            "Límite Inferior": _formatear_numero(li),
            "Límite Superior": _formatear_numero(ls),
            "Margen": _formatear_numero(margen)
        }

        desarrollo = f"""
        <div class="space-y-4">
            <div class="bg-orange-500/10 p-4 rounded-lg border border-orange-500/30">
                <p class="text-[11px] text-orange-400 font-bold uppercase mb-2">Cálculo del Intervalo</p>
                $$IC = \\bar{{X}} \\pm t_{{(\\alpha/2, n-1)}} \\cdot SE$$
                $$IC = {media:.4f} \\pm ({t_critico:.4f} \\cdot {se:.4f})$$
            </div>
            <div class="bg-gray-800 p-3 rounded text-center border border-white/10">
                $$IC_{{{int(nivel_confianza*100)}\\%}} = [{li:.4f}, {ls:.4f}]$$
            </div>
        </div>
        """

        return envolver_capitulo(
            titulo="Capítulo 3: Intervalos de Confianza",
            descripcion="Rango de valores probables para la media poblacional.",
            resultados=resultados,
            desarrollo_latex=desarrollo,
            grafico_datos={"tipo": "boxplot", "data": datos.tolist()}
        )
    except Exception as e:
        logger.error(f"Error Cap 3: {e}")
        raise

def capitulo_4_hipotesis(datos: np.ndarray, umbral: float = 5.0, alpha: float = 0.05) -> Dict[str, Any]:
    try:
        datos = _preparar_datos(datos)
        n = datos.size
        media = np.mean(datos)
        se = np.std(datos, ddof=1)/np.sqrt(n)
        t_stat = (media - umbral)/se
        p_valor = 2*(1-stats.t.cdf(abs(t_stat), df=n-1))
        rechazar = p_valor < alpha
        decision = "RECHAZAR H₀" if rechazar else "NO RECHAZAR H₀"

        resultados = {
            "T-Calculado": _formatear_numero(t_stat),
            "P-Valor": _formatear_numero(p_valor, 6),
            "Resultado": decision
        }

        desarrollo = f"""
        <div class="space-y-4">
            <div class="bg-red-500/10 p-4 rounded-lg border border-red-500/30">
                <p class="text-[11px] text-red-400 font-bold uppercase mb-2">Estadístico de Prueba</p>
                $$t = \\frac{{\\bar{{X}} - \\mu_0}}{{SE}} = \\frac{{{media:.4f} - {umbral}}}{{{se:.4f}}} = {t_stat:.4f}$$
            </div>
            <div class="p-3 rounded border {'border-red-500/50 bg-red-500/20' if rechazar else 'border-green-500/50 bg-green-500/20'}">
                <p class="text-xs text-center font-bold">{decision} (p={p_valor:.6f})</p>
            </div>
        </div>
        """

        return envolver_capitulo(
            titulo="Capítulo 4: Prueba de Hipótesis",
            descripcion=f"Prueba de significancia para un valor hipotético μ = {umbral}.",
            resultados=resultados,
            desarrollo_latex=desarrollo,
            grafico_datos={"tipo":"hipotesis","x":np.linspace(-4,4,100).tolist(),"y":stats.norm.pdf(np.linspace(-4,4,100)).tolist(),"t_stat":float(t_stat)}
        )
    except Exception as e:
        logger.error(f"Error Cap 4: {e}")
        raise

def capitulo_5_comparacion(datos: np.ndarray, umbral: float = 5.0, nivel_confianza: float = 0.95) -> Dict[str, Any]:
    """
    Capítulo 5: Comparación de Métodos Estadísticos
    Compara los datos observados vs un grupo de control generado bajo H0
    """
    try:
        datos_obs = _preparar_datos(datos)
        n = datos_obs.size
        
        # Generar grupo de control bajo H0 (μ = umbral)
        # Usamos la desviación observada para mantener realismo
        s_obs = np.std(datos_obs, ddof=1)
        np.random.seed(42)  # Para reproducibilidad
        datos_h0 = np.random.normal(loc=umbral, scale=s_obs, size=n)
        
        # Estadísticas de ambos grupos
        media_obs = np.mean(datos_obs)
        media_h0 = np.mean(datos_h0)
        
        # Prueba t de Welch para muestras independientes
        t_stat, p_valor = stats.ttest_ind(datos_obs, datos_h0, equal_var=False)
        
        # Prueba t clásica (una muestra)
        t_clasico = (media_obs - umbral) / (s_obs / np.sqrt(n))
        p_clasico = 2 * (1 - stats.t.cdf(abs(t_clasico), df=n-1))
        
        # Intervalo de confianza
        alpha = 1 - nivel_confianza
        t_crit = stats.t.ppf(1 - alpha/2, df=n-1)
        margen = t_crit * (s_obs / np.sqrt(n))
        ic_lower = media_obs - margen
        ic_upper = media_obs + margen
        contiene_h0 = ic_lower <= umbral <= ic_upper
        
        resultados = {
            "Media Observada": _formatear_numero(media_obs),
            "Media H₀": _formatear_numero(umbral),
            "Diferencia": _formatear_numero(media_obs - umbral),
            "T-Welch": _formatear_numero(t_stat),
            "P-Welch": _formatear_numero(p_valor, 6),
            "T-Clásico": _formatear_numero(t_clasico),
            "P-Clásico": _formatear_numero(p_clasico, 6),
            "IC Contiene H₀": "SÍ" if contiene_h0 else "NO"
        }
        
        # Determinar concordancia de métodos
        rechazar_welch = p_valor < alpha
        rechazar_clasico = p_clasico < alpha
        concordancia = "✓ Ambos métodos CONCUERDAN" if rechazar_welch == rechazar_clasico else "⚠ Métodos DISCREPAN"
        decision = "RECHAZAR H₀" if rechazar_clasico else "NO RECHAZAR H₀"
        
        desarrollo = f"""
        <div class="space-y-4">
            <div class="bg-cyan-500/10 p-4 rounded-lg border border-cyan-500/30">
                <p class="text-[11px] text-cyan-400 font-bold uppercase mb-2">Método 1: Prueba T Clásica (Una Muestra)</p>
                $$t_{{clásico}} = \\frac{{\\bar{{X}} - \\mu_0}}{{s/\\sqrt{{n}}}} = \\frac{{{media_obs:.4f} - {umbral}}}{{{s_obs:.4f}/\\sqrt{{{n}}}}} = {t_clasico:.4f}$$
                <p class="text-xs mt-2 text-elephant-300">P-valor: {p_clasico:.6f}</p>
            </div>
            
            <div class="bg-yellow-500/10 p-4 rounded-lg border border-yellow-500/30">
                <p class="text-[11px] text-yellow-400 font-bold uppercase mb-2">Método 2: Prueba Welch (Dos Muestras)</p>
                <p class="text-xs text-elephant-300 mb-2">Comparación: Datos Observados vs Datos Simulados bajo H₀</p>
                $$t_{{Welch}} = {t_stat:.4f}$$
                <p class="text-xs mt-2 text-elephant-300">P-valor: {p_valor:.6f}</p>
            </div>
            
            <div class="bg-purple-500/10 p-4 rounded-lg border border-purple-500/30">
                <p class="text-[11px] text-purple-400 font-bold uppercase mb-2">Método 3: Intervalo de Confianza ({int(nivel_confianza*100)}%)</p>
                $$IC = [{ic_lower:.4f}, {ic_upper:.4f}]$$
                <p class="text-xs mt-2 text-elephant-300">¿Contiene μ₀ = {umbral}? <strong class="text-{'green' if contiene_h0 else 'red'}-400">{resultados['IC Contiene H₀']}</strong></p>
            </div>
            
            <div class="p-4 rounded border {'border-green-500/50 bg-green-500/20' if rechazar_clasico == (not contiene_h0) else 'border-orange-500/50 bg-orange-500/20'}">
                <p class="text-sm text-center font-bold text-white">{concordancia}</p>
                <p class="text-xs text-center mt-1 text-elephant-300">Decisión Final: <strong>{decision}</strong></p>
            </div>
        </div>
        """

        # Preparar datos para gráfico de comparación
        grafico_datos = {
            "tipo": "comparacion",
            "data_obs": datos_obs.tolist()[:100],  # Limitar para performance
            "data_h0": datos_h0.tolist()[:100],
            "umbral": float(umbral),
            "media_obs": float(media_obs),
            "media_h0": float(media_h0)
        }

        return envolver_capitulo(
            titulo="Capítulo 5: Comparación de Métodos Estadísticos",
            descripcion="Validación cruzada entre prueba T clásica, Welch y intervalos de confianza.",
            resultados=resultados,
            desarrollo_latex=desarrollo,
            grafico_datos=grafico_datos
        )
    except Exception as e:
        logger.error(f"Error Cap 5: {e}")
        import traceback
        traceback.print_exc()
        raise

