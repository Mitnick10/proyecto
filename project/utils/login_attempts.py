"""
Sistema de seguimiento de intentos de login fallidos.
Implementa bloqueo temporal de cuentas después de intentos fallidos.
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Almacenar en memoria (en producción usar Redis)
login_attempts = {}
lockout_duration = timedelta(minutes=15)
max_attempts = 5


def record_failed_login(email: str):
    """
    Registra un intento de login fallido para un email.
    
    Args:
        email: Email del usuario que falló el login
    """
    if email not in login_attempts:
        login_attempts[email] = []
    
    login_attempts[email].append(datetime.utcnow())
    
    # Limpiar intentos antiguos (más de 15 minutos)
    cutoff = datetime.utcnow() - lockout_duration
    login_attempts[email] = [t for t in login_attempts[email] if t > cutoff]
    
    logger.warning(f"Intento fallido registrado para {email}. Total en ventana: {len(login_attempts[email])}")


def is_account_locked(email: str) -> tuple[bool, int]:
    """
    Verifica si una cuenta está bloqueada por intentos fallidos.
    
    Args:
        email: Email del usuario a verificar
        
    Returns:
        tuple: (está_bloqueada, intentos_restantes)
    """
    if email not in login_attempts:
        return False, max_attempts
    
    # Limpiar intentos antiguos
    cutoff = datetime.utcnow() - lockout_duration
    login_attempts[email] = [t for t in login_attempts[email] if t > cutoff]
    
    current_attempts = len(login_attempts[email])
    is_locked = current_attempts >= max_attempts
    attempts_remaining = max(0, max_attempts - current_attempts)
    
    if is_locked:
        logger.warning(f"Cuenta bloqueada: {email} ({current_attempts} intentos)")
    
    return is_locked, attempts_remaining


def reset_login_attempts(email: str):
    """
    Limpia los intentos fallidos de un email (después de login exitoso).
    
    Args:
        email: Email del usuario
    """
    if email in login_attempts:
        del login_attempts[email]
        logger.info(f"Intentos de login reseteados para {email}")


def get_lockout_time_remaining(email: str) -> int:
    """
    Obtiene los minutos restantes de bloqueo para una cuenta.
    
    Args:
        email: Email del usuario
        
    Returns:
        int: Minutos restantes de bloqueo (0 si no está bloqueado)
    """
    if email not in login_attempts or len(login_attempts[email]) < max_attempts:
        return 0
    
    # Tiempo del primer intento que aún cuenta
    oldest_attempt = min(login_attempts[email])
    unlock_time = oldest_attempt + lockout_duration
    remaining = unlock_time - datetime.utcnow()
    
    return max(0, int(remaining.total_seconds() / 60))
