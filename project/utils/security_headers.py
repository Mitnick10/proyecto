"""
Headers de seguridad HTTP para proteger la aplicación.
"""

def add_security_headers(response):
    """
    Agrega headers de seguridad HTTP estándar a todas las respuestas.
    
    Headers implementados:
    - X-Content-Type-Options: Previene MIME type sniffing
    - X-Frame-Options: Previene clickjacking
    - X-XSS-Protection: Habilita filtro XSS del navegador
    - Strict-Transport-Security: Fuerza HTTPS (producción)
    - Content-Security-Policy: Previene XSS y injection
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # HSTS - Solo en producción con HTTPS
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # CSP básico - ajustar según necesidades
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: https://noticias.com.ve; "
    )
    
    return response
