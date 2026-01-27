from functools import wraps
from flask import session, flash, redirect, url_for
from config.supabase_client import supabase
from gotrue.errors import AuthApiError
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    """
    Verifica sesión, restaura conexión Supabase y asegura que el ROL exista.
    Previene mezcla de roles validando que el usuario de Supabase coincida con la sesión.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificar si hay sesión básica en Flask
        if 'user_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('auth.login'))
        
        # 2. Restaurar la sesión en Supabase (Token)
        try:
            access_token = session.get('access_token')
            refresh_token = session.get('refresh_token')
            user_id_session = session.get('user_id')
            
            if access_token and refresh_token:
                supabase.auth.set_session(access_token, refresh_token)
                
                # SEGURIDAD: Verificar que el usuario autenticado coincide con la sesión
                current_user = supabase.auth.get_user()
                if current_user and current_user.user:
                    if current_user.user.id != user_id_session:
                        # El usuario de Supabase no coincide con la sesión de Flask
                        logger.warning(f"⚠️ SECURITY: User mismatch! Supabase: {current_user.user.id} != Session: {user_id_session}")
                        session.clear()
                        flash('Sesión inválida. Por favor inicia sesión nuevamente.', 'error')
                        return redirect(url_for('auth.login'))
            else:
                raise ValueError("Tokens no encontrados")

            # 3. RECUPERACIÓN DE ROL CON VALIDACIÓN DE SEGURIDAD
            if 'role' not in session or not session['role']:
                logger.debug(f"Rol perdido para {user_id_session}. Recuperando de forma segura...")
                try:
                    profile = supabase.table('profiles').select('role').eq('id', user_id_session).single().execute()
                    if profile.data and profile.data.get('role'):
                        new_role = profile.data['role']
                        session['role'] = new_role
                        logger.debug(f"Rol recuperado correctamente para {user_id_session} -> {new_role}")
                    else:
                        logger.warning(f"No se encontró rol para {user_id_session}, asignando 'usuario' por defecto")
                        session['role'] = 'usuario'
                except Exception as e:
                    logger.error(f"Error recuperando rol: {e}")
                    # Por seguridad, cerrar sesión si hay error
                    session.clear()
                    flash('Error de autenticación. Por favor inicia sesión nuevamente.', 'error')
                    return redirect(url_for('auth.login'))
                
        except (AuthApiError, ValueError) as e:
            logger.info(f"Sesión expirada: {e}")
            session.clear()
            flash('Tu sesión ha expirado.', 'warning')
            return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"Error inesperado en login_required: {e}", exc_info=True)
            session.clear()
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Permite acceso a Admin y Superadmin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', 'usuario')
        if role not in ['admin', 'superadmin']:
            flash('⚠️ Acceso denegado: Se requieren permisos de Administrador.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    """Permite acceso SOLO a Superadmin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', 'usuario')
        if role != 'superadmin':
            flash('⛔ Acceso denegado: Solo el Superadministrador puede hacer esto.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function