"""
Configuración de Rate Limiter para toda la aplicación.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Crear el limiter que será importado por app.py y blueprints
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
