import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from gotrue.errors import AuthApiError
from dotenv import load_dotenv

# Importaciones de nuestros módulos
from config.supabase_client import supabase
from blueprints.dashboard import dashboard_blueprint
from blueprints.auth import auth_blueprint

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
logger.info("Aplicación Flask inicializada correctamente")

# --- Registrar el Blueprint del Dashboard ---
app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')

# --- Registrar el Blueprint de Autenticación ---
app.register_blueprint(auth_blueprint, url_prefix='/')


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