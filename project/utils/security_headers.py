"""
Headers de seguridad HTTP para proteger la aplicación.
"""

def add_security_headers(response):
    """
<<<<<<< HEAD
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
=======
    Aplica headers de seguridad HTTP a una respuesta Flask.
    
    Args:
        response: Objeto Response de Flask
        
    Returns:
        Response con headers de seguridad agregados
    """
    # Previene ataques MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Previene clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Habilita protección XSS en navegadores antiguos
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # HSTS - Force HTTPS (comentado para desarrollo local)
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy - ACTUALIZADO para permitir blob:, cdnjs y PDFs de Supabase
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://kit.fontawesome.com https://ka-f.fontawesome.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://ka-f.fontawesome.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob: https: https://noticias.com.ve; "
        "connect-src 'self' https://ka-f.fontawesome.com; "
        "frame-src 'self' blob: https://*.supabase.co; "  # Permite iframes para PDFs de Supabase
        "object-src 'self' blob: https://*.supabase.co; "  # Permite <object> y <embed> para PDFs de Supabase
        "frame-ancestors 'none';"
    )
    response.headers['Content-Security-Policy'] = csp
>>>>>>> 19bc0b42141dc9139c457364af8c7d05a8913cbc
    
    return response
