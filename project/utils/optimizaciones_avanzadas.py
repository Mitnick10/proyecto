"""
Optimizaciones avanzadas de rendimiento para IRDEBG.
Incluye compresión de respuestas, lazy loading y consultas más eficientes.
"""

from flask import Flask
from flask_compress import Compress
import logging

logger = logging.getLogger(__name__)

def configurar_optimizaciones(app: Flask):
    """
    Configura optimizaciones de rendimiento para la aplicación Flask.
    
    Args:
        app: Instancia de Flask
    """
    
    # 1. Comprimir respuestas HTTP (reduce tamaño en 70-80%)
    compress = Compress()
    compress.init_app(app)
    logger.info("Compresión HTTP activada")
    
    # 2. Configurar caché de respuestas estáticas
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 año para archivos estáticos
    
    # 3. Optimizar configuración de Flask
    app.config['JSON_SORT_KEYS'] = False  # No ordenar JSON (más rápido)
    app.config['TEMPLATES_AUTO_RELOAD'] = False  # No recargar templates en producción
    
    logger.info("Optimizaciones de Flask configuradas")


def optimizar_consulta_becas(supabase, page=1, per_page=20, filtro=None):
    """
    Consulta optimizada que solo trae los campos necesarios para el listado.
    
    Args:
        supabase: Cliente Supabase
        page: Número de página
        per_page: Registros por página
        filtro: Filtro de disciplina
        
    Returns:
        dict con becas, total, total_pages
    """
    try:
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        # Solo seleccionar campos necesarios para el listado (más rápido)
        campos = 'id,nombre,apellido,cedula,disciplina,estatus,foto'
        
        query = supabase.table('becas').select(campos, count='exact')
        
        if filtro and filtro != 'Todas':
            query = query.eq('disciplina', filtro)
        
        result = query.order('id', desc=True).range(start, end).execute()
        
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return {
            'becas': result.data,
            'total': total,
            'total_pages': total_pages,
            'page': page
        }
    except Exception as e:
        logger.error(f"Error en consulta optimizada: {e}")
        return {'becas': [], 'total': 0, 'total_pages': 1, 'page': 1}


# Caché en memoria para disciplinas (se actualiza cada 5 minutos)
_cache_disciplinas = {
    'data': None,
    'timestamp': None
}

def obtener_disciplinas_cached(supabase):
    """
    Obtiene lista de disciplinas con caché de 5 minutos.
    """
    from datetime import datetime
    
    now = datetime.now()
    
    # Verificar caché
    if _cache_disciplinas['data'] and _cache_disciplinas['timestamp']:
        elapsed = (now - _cache_disciplinas['timestamp']).total_seconds()
        if elapsed < 300:  # 5 minutos
            return _cache_disciplinas['data']
    
    # Consultar y cachear
    try:
        result = supabase.table('becas').select('disciplina').limit(500).execute()
        disciplinas = sorted(list(set(i['disciplina'] for i in result.data if i.get('disciplina'))))
        
        _cache_disciplinas['data'] = disciplinas
        _cache_disciplinas['timestamp'] = now
        
        return disciplinas
    except Exception as e:
        logger.error(f"Error obteniendo disciplinas: {e}")
        return []


def invalidar_cache_disciplinas():
    """Invalida el caché de disciplinas."""
    _cache_disciplinas['data'] = None
    _cache_disciplinas['timestamp'] = None
