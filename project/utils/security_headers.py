"""
Headers de seguridad HTTP para proteger la aplicación.
"""

def add_security_headers(response):
    """
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
    
    return response
