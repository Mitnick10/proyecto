import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from gotrue.errors import AuthApiError
from config.supabase_client import supabase
from utils.decorators import login_required
from utils.password_strength import validar_fortaleza_password, generar_sugerencias_password

# --- Configuración de Logging ---
logger = logging.getLogger(__name__)

# --- Definición del Blueprint ---
auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión con depuración de roles."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        if not supabase: 
            abort(503)

        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email y contraseña son requeridos.', 'error')
            return render_template('login.html')

        try:
            # 1. Autenticación con Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user_id = auth_response.session.user.id
            
            # 2. BUSCAR ROL EN LA TABLA PROFILES
            logger.info(f"🔍 Buscando rol para user_id: {user_id}")
            profile_response = supabase.table('profiles').select('role').eq('id', user_id).execute()
            
            # Log detallado de la respuesta
            logger.info(f"📋 Respuesta de profiles: {profile_response.data}")
            
            # Verificamos si encontró datos
            if profile_response.data and len(profile_response.data) > 0:
                user_role = profile_response.data[0]['role']
                logger.info(f"✅ Rol encontrado en BD: {user_role} para {email}")
            else:
                user_role = 'usuario'
                logger.warning(f"⚠️ No se encontró rol para {email}, asignando 'usuario' por defecto")

            # 3. Guardar todo en la sesión de Flask
            session['user_id'] = user_id
            session['access_token'] = auth_response.session.access_token
            session['refresh_token'] = auth_response.session.refresh_token
            session['role'] = user_role
            
            logger.info(f"💾 Sesión guardada - user_id: {user_id}, role: {user_role}")
            flash(f'Bienvenido/a {email}. Rol: {user_role.upper()}', 'success')
            return redirect(url_for('dashboard.index'))

        except AuthApiError as e:
            logger.warning(f"Intento de login fallido para email: {email}")
            flash('Email o contraseña incorrectos.', 'error')
        except Exception as e:
            logger.error(f"Error inesperado durante el inicio de sesión: {e}", exc_info=True)
            flash(f'Error inesperado durante el inicio de sesión.', 'error')
    
    return render_template('login.html')

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de un nuevo usuario con validación avanzada de contraseña."""
    if request.method == 'POST':
        if not supabase: 
            abort(503)
            
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')

        # Validación de campos requeridos
        if not email or not password or not confirm_password or not nombre or not apellido:
            flash('Todos los campos son requeridos.', 'error')
            return render_template('register.html')
        
        # Validar que las contraseñas coincidan
        if password != confirm_password:
            flash('❌ Las contraseñas no coinciden. Por favor verifícalas.', 'error')
            return render_template('register.html')
        
        # Validar fortaleza de la contraseña
        es_valida, errores, nivel = validar_fortaleza_password(password)
        
        if not es_valida:
            # Mostrar todos los errores de validación
            flash('Tu contraseña no cumple con los requisitos de seguridad:', 'error')
            for error in errores:
                flash(f'  • {error}', 'error')
            
            # Mostrar sugerencias útiles
            sugerencias = generar_sugerencias_password(password)
            if sugerencias:
                flash('Sugerencias para mejorar tu contraseña:', 'warning')
                for sugerencia in sugerencias[:2]:  # Máximo 2 sugerencias
                    flash(f'  {sugerencia}', 'warning')
            
            return render_template('register.html')
        
        # Si llegamos aquí, la contraseña es válida
        logger.info(f"Contraseña válida con nivel de fortaleza: {nivel}/100")

        try:
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "first_name": nombre,
                        "last_name": apellido,
                        "full_name": f"{nombre} {apellido}"
                    }
                }
            })
            
            if auth_response.user:
                flash('✅ ¡Registro exitoso! Tu contraseña es segura. Por favor inicia sesión.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Registro procesado. Por favor verifica tu correo.', 'warning')
                return redirect(url_for('auth.login'))
            
        except AuthApiError as e:
            logger.warning(f"Error en registro para email {email}: {e.message}")
            flash(f'Error durante el registro: {e.message}', 'error')
        except Exception as e:
            logger.error(f"Error inesperado durante el registro: {e}", exc_info=True)
            flash(f'Error inesperado durante el registro.', 'error')

    return render_template('register.html')

@auth_blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Maneja la solicitud de recuperación de contraseña."""
    if request.method == 'POST':
        if not supabase: 
            abort(503)
        
        email = request.form.get('email')
        if not email:
            flash('Por favor ingresa tu correo electrónico.', 'error')
            return render_template('forgot_password.html')
            
        try:
            # Enviar correo de recuperación
            redirect_url = request.url_root.rstrip('/') + url_for('auth.reset_password')
            supabase.auth.reset_password_email(email, options={'redirect_to': redirect_url})
            
            flash('Si el correo existe, recibirás un enlace para restablecer tu contraseña.', 'success')
            return redirect(url_for('auth.login'))
            
        except AuthApiError as e:
            logger.warning(f"Error al solicitar recuperación para {email}: {e}")
            flash('Si el correo existe, recibirás un enlace para restablecer tu contraseña.', 'success')
        except Exception as e:
            logger.error(f"Error inesperado en forgot_password: {e}", exc_info=True)
            flash('Error al procesar la solicitud.', 'error')
            
    return render_template('forgot_password.html')

@auth_blueprint.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Maneja el restablecimiento de la contraseña."""
    if request.method == 'POST':
        if not supabase: 
            abort(503)
        
        access_token = request.form.get('access_token')
        refresh_token = request.form.get('refresh_token')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Por favor ingresa y confirma tu nueva contraseña.', 'error')
            return render_template('reset_password.html')
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('reset_password.html')
            
        if not access_token:
            flash('Token de recuperación inválido o expirado. Por favor solicita uno nuevo.', 'error')
            return redirect(url_for('auth.forgot_password'))

        try:
            supabase.auth.set_session(access_token, refresh_token)
            supabase.auth.update_user({"password": password})
            supabase.auth.sign_out()
            session.clear()
            
            flash('Contraseña actualizada exitosamente. Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except AuthApiError as e:
            logger.warning(f"Error al restablecer contraseña: {e}")
            flash(f'Error al restablecer contraseña: {e.message}', 'error')
        except Exception as e:
            logger.error(f"Error inesperado en reset_password: {e}", exc_info=True)
            flash('Error inesperado al restablecer la contraseña.', 'error')

    return render_template('reset_password.html')

@auth_blueprint.route('/logout')
@login_required 
def logout():
    """Cierra la sesión del usuario."""
    if supabase and 'access_token' in session:
        try:
            supabase.auth.sign_out()
        except Exception as e:
            logger.warning(f"Error al cerrar sesión en Supabase: {e}")

    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))
