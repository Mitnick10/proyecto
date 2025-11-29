from functools import wraps
from flask import session, flash, redirect, url_for
from config.supabase_client import supabase
from gotrue.errors import AuthApiError

def login_required(f):
    """
    Verifica sesión, restaura conexión Supabase y asegura que el ROL exista.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificar si hay sesión básica en Flask
        if 'user_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('login'))
        
        # 2. Restaurar la sesión en Supabase (Token)
        try:
            access_token = session.get('access_token')
            refresh_token = session.get('refresh_token')
            
            if access_token and refresh_token:
                supabase.auth.set_session(access_token, refresh_token)
            else:
                raise ValueError("Tokens no encontrados")

            # 3. --- RECUPERACIÓN DE ROL DE EMERGENCIA ---
            # Si por alguna razón se borró el rol de la sesión, lo buscamos de nuevo.
            if 'role' not in session or not session['role']:
                print(f"DEBUG: Rol perdido para {session['user_id']}. Recuperando...")
                try:
                    profile = supabase.table('profiles').select('role').eq('id', session['user_id']).single().execute()
                    if profile.data:
                        session['role'] = profile.data['role']
                        print(f"DEBUG: Rol recuperado -> {session['role']}")
                    else:
                        session['role'] = 'usuario'
                except Exception as e:
                    print(f"Error recuperando rol: {e}")
                    session['role'] = 'usuario' # Fallback seguro
            # ---------------------------------------------
                
        except (AuthApiError, ValueError) as e:
            print(f"Sesión expirada: {e}")
            session.clear()
            flash('Tu sesión ha expirado.', 'warning')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error inesperado: {e}")
            session.clear()
            return redirect(url_for('login'))

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