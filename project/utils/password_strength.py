"""
Validaciones de contraseñas con requisitos de fortaleza.
"""
import re
from typing import Tuple, List


def validar_fortaleza_password(password: str) -> Tuple[bool, List[str], int]:
    """
    Valida la fortaleza de una contraseña según múltiples criterios.
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Tuple (es_valida, lista_errores, nivel_fortaleza)
        - es_valida: True si cumple todos los requisitos
        - lista_errores: Lista de mensajes de error
        - nivel_fortaleza: 0-100 indicando qué tan fuerte es
    """
    errores = []
    puntos = 0
    
    if not password:
        return False, ["La contraseña es requerida"], 0
    
    # 1. Longitud mínima (REQUERIDO)
    if len(password) < 6:
        errores.append("Debe tener al menos 6 caracteres")
    else:
        puntos += 20
        if len(password) >= 8:
            puntos += 10
        if len(password) >= 12:
            puntos += 10
    
    # 2. Debe contener al menos una minúscula (REQUERIDO)
    if not re.search(r'[a-z]', password):
        errores.append("Debe contener al menos una letra minúscula")
    else:
        puntos += 15
    
    # 3. Debe contener al menos una mayúscula (REQUERIDO)
    if not re.search(r'[A-Z]', password):
        errores.append("Debe contener al menos una letra MAYÚSCULA")
    else:
        puntos += 15
    
    # 4. Debe contener al menos un número (REQUERIDO)
    if not re.search(r'\d', password):
        errores.append("Debe contener al menos un número")
    else:
        puntos += 15
    
    # 5. Caracteres especiales (OPCIONAL pero suma puntos)
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        puntos += 15
    
    # 6. Sin espacios (REQUERIDO)
    if ' ' in password:
        errores.append("No debe contener espacios")
    else:
        puntos += 10
    
    # Es válida si no hay errores
    es_valida = len(errores) == 0
    
    # Nivel de fortaleza (0-100)
    nivel_fortaleza = min(puntos, 100)
    
    return es_valida, errores, nivel_fortaleza


def obtener_nivel_texto(nivel: int) -> str:
    """
    Convierte el nivel numérico en texto descriptivo.
    
    Args:
        nivel: Nivel de fortaleza (0-100)
        
    Returns:
        Texto descriptivo ("Muy débil", "Débil", "Media", "Fuerte", "Muy fuerte")
    """
    if nivel < 30:
        return "Muy débil"
    elif nivel < 50:
        return "Débil"
    elif nivel < 70:
        return "Media"
    elif nivel < 90:
        return "Fuerte"
    else:
        return "Muy fuerte"


def obtener_color_fortaleza(nivel: int) -> str:
    """
    Retorna el color CSS apropiado según el nivel de fortaleza.
    
    Args:
        nivel: Nivel de fortaleza (0-100)
        
    Returns:
        Color en formato CSS (red, orange, yellow, lightgreen, green)
    """
    if nivel < 30:
        return "red"
    elif nivel < 50:
        return "orange"
    elif nivel < 70:
        return "yellow"
    elif nivel < 90:
        return "lightgreen"
    else:
        return "green"


def generar_sugerencias_password(password: str) -> List[str]:
    """
    Genera sugerencias para mejorar la contraseña.
    
    Args:
        password: Contraseña actual
        
    Returns:
        Lista de sugerencias
    """
    sugerencias = []
    
    if len(password) < 8:
        sugerencias.append("💡 Usa al menos 8 caracteres para mayor seguridad")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        sugerencias.append("💡 Agrega caracteres especiales (!@#$%^&*) para hacerla más fuerte")
    
    if len(password) < 12:
        sugerencias.append("💡 Contraseñas de 12+ caracteres son mucho más seguras")
    
    # Verificar patrones comunes débiles
    patrones_debiles = ['123', 'abc', 'password', 'qwerty', '000', '111']
    for patron in patrones_debiles:
        if patron.lower() in password.lower():
            sugerencias.append(f"⚠️ Evita patrones comunes como '{patron}'")
            break
    
    return sugerencias


# Ejemplo de uso en comentarios para documentación
"""
Ejemplos de uso:

# Contraseña débil
>>> validar_fortaleza_password("abc123")
(False, ['Debe contener al menos una letra MAYÚSCULA'], 60)

# Contraseña fuerte
>>> validar_fortaleza_password("MiPassword123!")
(True, [], 100)

# Obtener descripción
>>> obtener_nivel_texto(85)
'Fuerte'

# Generar sugerencias
>>> generar_sugerencias_password("password")
['💡 Agrega caracteres especiales (!@#$%^&*) para hacerla más fuerte', 
 '💡 Contraseñas de 12+ caracteres son mucho más seguras',
 '⚠️ Evita patrones comunes como 'password'']
"""
