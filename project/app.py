import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from gotrue.errors import AuthApiError
from dotenv import load_dotenv

# Importaciones de nuestros módulos
from supabase_client import supabase
from dashboard import dashboard_blueprint
from decorators import login_required

# --- Cargar variables de entorno ---
load_dotenv()

# --- Configuración de la App ---
app = Flask(__name__)
# Asegúrate de tener esta variable en tu archivo .env o usa una cadena segura aquí
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'una-clave-secreta-muy-dificil-de-adivinar-cambia-esto')

# --- Registrar el Blueprint del Dashboard ---
# Todas las rutas en dashboard.py comenzarán con /dashboard
app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )
# --- Manejador de Errores ---
@app.errorhandler(503)
def service_unavailable(e):
    """Maneja el error 503 si Supabase no está disponible."""
    return render_template('503.html'), 503

@app.errorhandler(404)
def page_not_found(e):
    """Maneja el error 404 (Página no encontrada)."""
    return render_template('404.html'), 404

# --- RUTAS PRINCIPALES ---

@app.route('/')
def index():
    """
    Ruta Raíz.
    Redirige al dashboard si hay sesión, o al login si no.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión con depuración de roles."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        if not supabase: abort(503)

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
            # Esto es crucial para saber si es admin o superadmin
            print(f"--- DEBUG LOGIN ---")
            print(f"Buscando rol para usuario ID: {user_id}")
            
            profile_response = supabase.table('profiles').select('role').eq('id', user_id).execute()
            
            # Verificamos si encontró datos
            if profile_response.data and len(profile_response.data) > 0:
                user_role = profile_response.data[0]['role']
                print(f"Rol encontrado en base de datos: {user_role}")
            else:
                user_role = 'usuario'
                print("AVISO: No se encontró perfil. Se asigna 'usuario' por defecto.")

            # 3. Guardar todo en la sesión de Flask
            # Estos tokens son los que usa decorators.py para mantener la sesión viva
            session['user_id'] = user_id
            session['access_token'] = auth_response.session.access_token
            session['refresh_token'] = auth_response.session.refresh_token
            session['role'] = user_role
            
            flash(f'Bienvenido/a. Rol: {user_role.upper()}', 'success')
            return redirect(url_for('dashboard.index'))

        except AuthApiError as e:
            flash('Email o contraseña incorrectos.', 'error')
        except Exception as e:
            flash(f'Error inesperado durante el inicio de sesión.', 'error')
            print(f"Error en login: {e}")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de un nuevo usuario."""
    if request.method == 'POST':
        if not supabase: abort(503)
            
        email = request.form.get('email')
        password = request.form.get('password')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')

        if not email or not password or not nombre or not apellido:
            flash('Todos los campos son requeridos.', 'error')
            return render_template('register.html')

        try:
            # El trigger de base de datos (si lo configuraste) creará el perfil automáticamente
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
            flash('¡Registro exitoso! Por favor inicia sesión.', 'success')
            return redirect(url_for('login'))
            
        except AuthApiError as e:
            flash(f'Error durante el registro: {e.message}', 'error')
        except Exception as e:
            flash(f'Error inesperado durante el registro.', 'error')
            print(f"Error en register: {e}")

    return render_template('register.html')

@app.route('/logout')
@login_required 
def logout():
    """Cierra la sesión del usuario."""
    if supabase and 'access_token' in session:
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print(f"Error silencioso al cerrar sesión en Supabase: {e}")

    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))

# --- Ejecución de la App ---
if __name__ == '__main__':
    # El modo debug es útil para desarrollo
    app.run(debug=True)