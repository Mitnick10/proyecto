"""
Utilidades para manejo de caché en la aplicación.
Consolida la lógica de validación de caché y proporciona decorators reutilizables.
"""

from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def is_cache_valid(cache: Dict[str, Any]) -> bool:
    """
    Verifica si un caché es válido según su TTL.
    
    Args:
        cache: Diccionario con keys 'data', 'timestamp', y 'ttl'
        
    Returns:
        bool: True si el caché es válido, False en caso contrario
    """
    if cache.get('data') is None or cache.get('timestamp') is None:
        return False
    
    now = datetime.now()
    ttl = cache.get('ttl', 60)
    elapsed = (now - cache['timestamp']).total_seconds()
    
    return elapsed < ttl


def get_cached_or_compute(
    cache: Dict[str, Any], 
    compute_func: Callable[[], Any]
) -> Any:
    """
    Obtiene datos del caché si son válidos, o los calcula y almacena.
    
    Args:
        cache: Diccionario de caché con 'data', 'timestamp', 'ttl'
        compute_func: Función que calcula los datos si el caché está inválido
        
    Returns:
        Los datos del caché o recién calculados
    """
    if is_cache_valid(cache):
        logger.debug(f"Cache hit - usando datos cacheados")
        return cache['data']
    
    logger.debug(f"Cache miss - recalculando datos")
    data = compute_func()
    
    # Actualizar caché
    cache['data'] = data
    cache['timestamp'] = datetime.now()
    
    return data


def invalidate_cache(cache: Dict[str, Any]) -> None:
    """
    Invalida un caché estableciendo data y timestamp a None.
    
    Args:
        cache: Diccionario de caché a invalidar
    """
    cache['data'] = None
    cache['timestamp'] = None
    logger.debug("Cache invalidado")


def create_cache(ttl: int = 60) -> Dict[str, Any]:
    """
    Crea un nuevo diccionario de caché con la estructura estándar.
    
    Args:
        ttl: Tiempo de vida del caché en segundos (default: 60)
        
    Returns:
        Diccionario de caché inicializado
    """
    return {
        'data': None,
        'timestamp': None,
        'ttl': ttl
    }
