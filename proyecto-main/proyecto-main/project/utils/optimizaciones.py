"""
Módulo de optimización de rendimiento para el dashboard.
Incluye caché simple y funciones optimizadas.
"""

from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Caché simple en memoria
_cache = {}

def cache_with_ttl(ttl_seconds=60):
    """
    Decorador para cachear resultados de funciones con TTL (Time To Live).
    
    Args:
        ttl_seconds: Tiempo de vida del caché en segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crear clave única basada en función y argumentos
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            now = datetime.now()
            
            # Verificar si existe en caché y no ha expirado
            if cache_key in _cache:
                cached_data, timestamp = _cache[cache_key]
                if (now - timestamp).total_seconds() < ttl_seconds:
                    logger.debug(f"Cache HIT para {func.__name__}")
                    return cached_data
            
            # Ejecutar función y guardar en caché
            logger.debug(f"Cache MISS para {func.__name__}")
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, now)
            
            return result
        return wrapper
    return decorator


def limpiar_cache():
    """Limpia todo el caché."""
    global _cache
    _cache = {}
    logger.info("Caché limpiado")


def invalidar_cache_patron(patron):
    """
    Invalida entradas de caché que coincidan con un patrón.
    
    Args:
        patron: String que debe estar contenido en la clave
    """
    global _cache
    keys_to_delete = [k for k in _cache.keys() if patron in k]
    for key in keys_to_delete:
        del _cache[key]
    logger.info(f"Invalidadas {len(keys_to_delete)} entradas de caché con patrón '{patron}'")


# Funciones optimizadas para consultas frecuentes

@cache_with_ttl(ttl_seconds=60)
def obtener_contadores_dashboard(supabase):
    """
    Obtiene los contadores del dashboard con caché de 60 segundos.
    
    Returns:
        dict con atletas, revision, medallas
    """
    try:
        atletas = supabase.table('becas').select('id', count='exact').eq('estatus', 'Activo').execute().count or 0
        revision = supabase.table('becas').select('id', count='exact').eq('estatus', 'En Revisión').execute().count or 0
        
        try:
            medallas = supabase.table('medallas').select('id', count='exact').execute().count or 0
        except:
            medallas = 0
        
        return {
            'atletas': atletas,
            'revision': revision,
            'medallas': medallas
        }
    except Exception as e:
        logger.error(f"Error obteniendo contadores: {e}")
        return {'atletas': 0, 'revision': 0, 'medallas': 0}


@cache_with_ttl(ttl_seconds=300)  # 5 minutos
def obtener_lista_disciplinas(supabase):
    """
    Obtiene la lista única de disciplinas con caché de 5 minutos.
    
    Returns:
        list de disciplinas ordenadas
    """
    try:
        # Limitar a 1000 registros para evitar consultas muy grandes
        all_d = supabase.table('becas').select('disciplina').limit(1000).execute()
        return sorted(list(set(i['disciplina'] for i in all_d.data if i.get('disciplina'))))
    except Exception as e:
        logger.error(f"Error obteniendo disciplinas: {e}")
        return []


def obtener_becas_paginadas(supabase, page=1, per_page=20, filtro_disciplina=None):
    """
    Obtiene becas con paginación optimizada.
    
    Args:
        supabase: Cliente de Supabase
        page: Número de página (1-indexed)
        per_page: Registros por página
        filtro_disciplina: Filtro opcional por disciplina
        
    Returns:
        dict con becas, total, total_pages
    """
    try:
        # Calcular rango
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        # Construir consulta
        query = supabase.table('becas').select('*', count='exact')
        
        if filtro_disciplina and filtro_disciplina != 'Todas':
            query = query.eq('disciplina', filtro_disciplina)
        
        # Ordenar por ID descendente (más recientes primero) y aplicar límite
        result = query.order('id', desc=True).range(start, end).execute()
        
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return {
            'becas': result.data,
            'total': total,
            'total_pages': total_pages,
            'page': page,
            'per_page': per_page
        }
    except Exception as e:
        logger.error(f"Error obteniendo becas paginadas: {e}")
        return {
            'becas': [],
            'total': 0,
            'total_pages': 1,
            'page': 1,
            'per_page': per_page
        }
