import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from gotrue.errors import AuthApiError
from config.supabase_client import supabase
from utils.decorators import login_required
from utils.password_strength import validar_fortaleza_password, generar_sugerencias_password
from utils.auth_helpers import get_user_role, create_user_session
from utils.login_attempts import record_failed_login, is_account_locked, reset_login_attempts, get_lockout_time_remaining
from utils.rate_limiter import limiter

# --- Configuración de Logging ---
logger = logging.getLogger(__name__)

# --- Definición del Blueprint ---
auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión con auto-login después de confirmación de email."""
    
    # Si ya hay sesión de Flask activa, redirigir al dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    # Detectar si hay sesión activa de Supabase (ej: desde confirmación de email)
    try:
        user = supabase.auth.get_user()
        if user and user.user:
            user_id = user.user.id
            email = user.user.email
            user_role = get_user_role(user_id)
            
            # Crear sesión de Flask
            session.permanent = True
            session['user_id'] = user_id
            session['email'] = email
            session['role'] = user_role
            
            flash(f'¡Bienvenido/a {email}! Tu correo ha sido confirmado.', 'success')
            logger.info(f"✅ Auto-login exitoso después de confirmación: {email}")
            return redirect(url_for('dashboard.index'))
    except Exception as e:
        # Si falla la detección de sesión, continuar con login normal
        logger.debug(f"No hay sesión activa de Supabase: {e}")

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
            
            # 2. Obtener rol del usuario
            user_role = get_user_role(user_id)

            # 3. Crear sesión de Flask
            create_user_session(auth_response, user_role, email)
            
            logger.info(f"✅ Login exitoso: {email}")
            return redirect(url_for('dashboard.index'))

        except AuthApiError as e:
            logger.warning(f"Intento de login fallido para email {email}: {e.message}")
            
            if "Email not confirmed" in e.message:
                flash('Tu correo electrónico no ha sido confirmado. Por favor revisa tu bandeja de entrada.', 'warning')
            elif "Invalid login credentials" in e.message:
                flash(f'❌ Email o contraseña incorrectos.', 'error')
            else:
                flash(f'Error de autenticación: {e.message}', 'error')
        except Exception as e:
            logger.error(f"Error inesperado durante el inicio de sesión: {e}", exc_info=True)
            flash(f'Error inesperado durante el inicio de sesión.', 'error')
    
    return render_template('login.html')

@auth_blueprint.route('/login/phone', methods=['POST'])
def login_phone():
    """Maneja el inicio de sesión con teléfono (envío de OTP)."""
    if not supabase:
        abort(503)

    phone = request.form.get('phone')
    if not phone:
        flash('Por favor ingresa tu número de teléfono.', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Enviar OTP por SMS
        supabase.auth.sign_in_with_otp({"phone": phone})
        flash(f'Código enviado a {phone}.', 'success')
        return render_template('verify_otp.html', phone=phone)

    except AuthApiError as e:
        logger.warning(f"Error al enviar OTP a {phone}: {e.message}")
        flash(f'Error al enviar código: {e.message}', 'error')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error inesperado en login_phone: {e}", exc_info=True)
        flash('Error inesperado al intentar enviar el código.', 'error')
        return redirect(url_for('auth.login'))

@auth_blueprint.route('/login/verify', methods=['POST'])
def verify_otp():
    """Verifica el OTP enviado al teléfono."""
    if not supabase:
        abort(503)

    phone = request.form.get('phone')
    token = request.form.get('token')

    if not phone or not token:
        flash('Teléfono y código son requeridos.', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Verificar OTP
        auth_response = supabase.auth.verify_otp({
            "phone": phone,
            "token": token,
            "type": "sms"
        })

        user_id = auth_response.session.user.id

        # Obtener rol y crear sesión
        user_role = get_user_role(user_id)
        create_user_session(auth_response, user_role)

        flash(f'Bienvenido/a. Rol: {user_role.upper()}', 'success')
        return redirect(url_for('dashboard.index'))

    except AuthApiError as e:
        logger.warning(f"Error al verificar OTP para {phone}: {e.message}")
        flash(f'Código inválido o expirado: {e.message}', 'error')
        return render_template('verify_otp.html', phone=phone)
    except Exception as e:
        logger.error(f"Error inesperado en verify_otp: {e}", exc_info=True)
        flash('Error inesperado al verificar el código.', 'error')
        return redirect(url_for('auth.login'))

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
        cedula = request.form.get('cedula')

        # Validación de campos requeridos
        if not email or not password or not confirm_password or not nombre or not apellido or not cedula:
            flash('Todos los campos son requeridos.', 'error')
            return render_template('register.html')
        
        # Validar que las contraseñas coincidan (fail fast)
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
            # Construir URL de redirect para confirmación de email
            app_url = os.environ.get('APP_URL', request.url_root.rstrip('/'))
            redirect_url = f"{app_url}/login"
            
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "email_redirect_to": redirect_url,  # Redirige a /login después de confirmar email
                    "data": {
                        "first_name": nombre,
                        "last_name": apellido,
                        "full_name": f"{nombre} {apellido}",
                        "cedula": cedula
                    }
                }
            })
            
            if auth_response.user:
                # Actualizar perfil con cédula
                try:
                    supabase.table('profiles').update({
                        'cedula': cedula
                    }).eq('id', auth_response.user.id).execute()
                except Exception as profile_error:
                    logger.warning(f"No se pudo actualizar perfil con cedula: {profile_error}")
                
                flash('✅ ¡Registro exitoso! Por favor verifica tu correo electrónico.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Registro procesado. Por favor verifica tu correo.', 'warning')
                return redirect(url_for('auth.login'))
            
        except AuthApiError as e:
            error_msg = e.message if hasattr(e, 'message') else str(e)
            logger.warning(f"Error en registro para email {email}: {error_msg}")
            
            # Mensajes más específicos según el error
            if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                flash('Este correo electrónico ya está registrado. Por favor inicia sesión.', 'error')
            elif "invalid" in error_msg.lower() and "email" in error_msg.lower():
                flash('El correo electrónico no es válido. Por favor verifica el formato.', 'error')
            else:
                flash(f'Error durante el registro: {error_msg}', 'error')
        except Exception as e:
            logger.error(f"Error inesperado durante el registro: {e}", exc_info=True)
            flash('Error inesperado durante el registro. Por favor intenta nuevamente.', 'error')

    return render_template('register.html')

@auth_blueprint.route('/verify/phone-change', methods=['POST'])
def verify_phone_change():
    """Verifica el cambio de teléfono (usado en registro)."""
    if not supabase:
        abort(503)

    phone = request.form.get('phone')
    token = request.form.get('token')

    if not phone or not token:
        flash('Teléfono y código son requeridos.', 'error')
        return render_template('verify_otp.html', phone=phone, type='phone_change')

    try:
        # Verificar OTP de cambio de teléfono
        response = supabase.auth.verify_otp({
            "phone": phone,
            "token": token,
            "type": "phone_change"
        })
        
        flash('✅ Teléfono verificado exitosamente. ¡Bienvenido!', 'success')
        return redirect(url_for('dashboard.index'))

    except AuthApiError as e:
        logger.warning(f"Error al verificar teléfono {phone}: {e.message}")
        flash(f'Código inválido o expirado: {e.message}', 'error')
        return render_template('verify_otp.html', phone=phone, type='phone_change')
    except Exception as e:
        logger.error(f"Error inesperado en verify_phone_change: {e}", exc_info=True)
        flash('Error inesperado al verificar el código.', 'error')
        return redirect(url_for('auth.login'))

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
            logger.info(f"🔗 Generando URL de recuperación: {redirect_url}")
            
            supabase.auth.reset_password_email(email, options={'redirect_to': redirect_url})
            
            flash('Si el correo existe, recibirás un enlace para restablecer tu contraseña.', 'success')
            return redirect(url_for('auth.login'))
            
        except AuthApiError as e:
            logger.warning(f"Error al solicitar recuperación para {email}: {e}")
            # Por seguridad, mostramos el mismo mensaje
            flash('Si el correo existe, recibirás un enlace para restablecer tu contraseña.', 'success')
        except Exception as e:
            logger.error(f"Error inesperado en forgot_password: {e}", exc_info=True)
            flash('Error al procesar la solicitud.', 'error')
            
    return render_template('forgot_password.html')

@auth_blueprint.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Maneja el restablecimiento de la contraseña (Soporta PKCE e Implicit Flow)."""
    access_token = None
    refresh_token = None
    
    # Manejar el flujo PKCE (cuando viene ?code=...) en GET
    if request.method == 'GET':
        code = request.args.get('code')
        if code:
            try:
                # Intercambiar código por sesión
                res = supabase.auth.exchange_code_for_session({"auth_code": code})
                if res.session:
                    access_token = res.session.access_token
                    refresh_token = res.session.refresh_token
                    logger.info(f"✅ Code intercambiado exitosamente por tokens para {res.user.email}")
            except AuthApiError as e:
                logger.error(f"Error al intercambiar code por sesión: {e.message}")
                flash(f'El enlace de recuperación es inválido o ha expirado: {e.message}', 'error')
                return redirect(url_for('auth.forgot_password'))
            except Exception as e:
                logger.error(f"Error inesperado al intercambiar code: {e}")
                flash('Error al procesar el enlace de recuperación.', 'error')
                return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        if not supabase: 
            abort(503)
        
        access_token = request.form.get('access_token')
        refresh_token = request.form.get('refresh_token')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Por favor ingresa y confirma tu nueva contraseña.', 'error')
            return render_template('reset_password.html', access_token=access_token, refresh_token=refresh_token)
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('reset_password.html', access_token=access_token, refresh_token=refresh_token)
            
        if not access_token:
            flash('Token de recuperación inválido o expirado. Por favor solicita uno nuevo.', 'error')
            return redirect(url_for('auth.forgot_password'))

        try:
            # Opción 1: Si tenemos refresh token, usar set_session
            if refresh_token:
                supabase.auth.set_session(access_token, refresh_token)
            
            # Actualizar usuario
            supabase.auth.update_user({"password": password})
            
            # Cerrar sesión por seguridad y limpiar flask session
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

    return render_template('reset_password.html', access_token=access_token, refresh_token=refresh_token)


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
