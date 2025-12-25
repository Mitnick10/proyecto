import os
import logging
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from gotrue.errors import AuthApiError
from dotenv import load_dotenv

# Importaciones de nuestros módulos
from config.supabase_client import supabase
from utils.rate_limiter import limiter
from blueprints.dashboard import dashboard_blueprint
from blueprints.auth import auth_blueprint
from utils.security_headers import add_security_headers


# --- Cargar variables de entorno ---
load_dotenv()

# --- Configuración de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuración de la App ---
app = Flask(__name__)

# Validación obligatoria de SECRET_KEY
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
if not SECRET_KEY:
    logger.error("FLASK_SECRET_KEY no está configurada en el archivo .env")
    raise ValueError("FLASK_SECRET_KEY debe estar configurada en el archivo .env")
app.config['SECRET_KEY'] = SECRET_KEY

# --- Configuración de Seguridad ---
# Session security
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Previene acceso desde JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protección CSRF
app.config['SESSION_COOKIE_SECURE'] = False  # Cambiar a True en producción (HTTPS)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Timeout de sesión

# Desactivar caché de templates para desarrollo
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# --- Rate Limiting ---
# Inicializar limiter con la app
limiter.init_app(app)

logger.info("Aplicación Flask inicializada correctamente")

# --- Registrar el Blueprint del Dashboard ---
app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')

# --- Registrar el Blueprint de Autenticación ---
app.register_blueprint(auth_blueprint, url_prefix='/')

# --- Security Headers ---
@app.after_request
def apply_security_headers(response):
    """Aplica headers de seguridad HTTP a todas las respuestas."""
    return add_security_headers(response)


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
    """Ruta Raíz. Redirige al dashboard si hay sesión, o al login si no."""
    # Detectar confirmación de correo (Supabase envía type=signup o recovery)
    if request.args.get('type') == 'signup' or request.args.get('code'):
        flash('¡Correo confirmado exitosamente! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

# --- Ejecución de la App ---
if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    app.run(debug=True, port=port, host=host)