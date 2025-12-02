"""
Módulo de validación de datos para el sistema IRDEBG.
Contiene funciones para validar emails, cédulas, rangos numéricos, etc.
"""

import re
from typing import Optional, Tuple

def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el formato de un email.
    
    Args:
        email: String con el email a validar
        
    Returns:
        Tuple (es_valido, mensaje_error)
    """
    if not email:
        return False, "El email es requerido"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, None


def validar_cedula(cedula: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el formato de una cédula venezolana (V-12345678 o E-12345678).
    
    Args:
        cedula: String con la cédula a validar
        
    Returns:
        Tuple (es_valido, mensaje_error)
    """
    if not cedula:
        return False, "La cédula es requerida"
    
    # Formato venezolano: V-12345678 o E-12345678
    pattern = r'^[VEve]-?\d{7,8}$'
    if not re.match(pattern, cedula.upper()):
        return False, "Formato de cédula inválido. Use V-12345678 o E-12345678"
    
    return True, None


def validar_edad(edad: str) -> Tuple[bool, Optional[str]]:
    """
    Valida que la edad sea un número entre 5 y 100.
    
    Args:
        edad: String con la edad a validar
        
    Returns:
        Tuple (es_valido, mensaje_error)
    """
    if not edad:
        return True, None  # La edad puede ser opcional
    
    try:
        edad_int = int(edad)
        if edad_int < 5 or edad_int > 100:
            return False, "La edad debe estar entre 5 y 100 años"
        return True, None
    except ValueError:
        return False, "La edad debe ser un número válido"


def validar_peso(peso: str) -> Tuple[bool, Optional[str]]:
    """
    Valida que el peso sea un número entre 20 y 200 kg.
    
    Args:
        peso: String con el peso a validar
        
    Returns:
        Tuple (es_valido, mensaje_error)
    """
    if not peso:
        return True, None  # El peso puede ser opcional
    
    try:
        peso_float = float(peso)
        if peso_float < 20 or peso_float > 200:
            return False, "El peso debe estar entre 20 y 200 kg"
        return True, None
    except ValueError:
        return False, "El peso debe ser un número válido"


def validar_estatura(estatura: str) -> Tuple[bool, Optional[str]]:
    """
    Valida la estatura y la normaliza a centímetros.
    Acepta tanto metros (ej: 1.75) como centímetros (ej: 175).
    
    Args:
        estatura: String con la estatura a validar (metros o centímetros)
        
    Returns:
        Tuple (es_valido, mensaje_error)
        
    Ejemplos:
        validar_estatura("1.75") -> Detecta metros, convierte a 175 cm
        validar_estatura("175") -> Ya está en centímetros
        validar_estatura("2.10") -> Detecta metros, convierte a 210 cm
    """
    if not estatura:
        return True, None  # La estatura puede ser opcional
    
    try:
        estatura_float = float(estatura)
        
        # Determinar si está en metros o centímetros
        # Si el valor es <= 3, asumimos que está en metros
        if estatura_float <= 3:
            # Convertir metros a centímetros
            estatura_cm = estatura_float * 100
        else:
            # Ya está en centímetros
            estatura_cm = estatura_float
        
        # Validar rango razonable (50 cm a 250 cm)
        if estatura_cm < 50 or estatura_cm > 250:
            return False, "La estatura debe estar entre 50 cm (0.5 m) y 250 cm (2.5 m)"
        
        return True, None
    except ValueError:
        return False, "La estatura debe ser un número válido"


def normalizar_estatura(estatura: str) -> int:
    """
    Normaliza la estatura a centímetros.
    Si está en metros (<=3), convierte a centímetros.
    
    Args:
        estatura: String con la estatura
        
    Returns:
        Entero con la estatura en centímetros
    """
    if not estatura:
        return None
    
    try:
        estatura_float = float(estatura)
        
        # Si el valor es <= 3, asumimos que está en metros
        if estatura_float <= 3:
            return int(estatura_float * 100)
        else:
            return int(estatura_float)
    except:
        return None


def validar_telefono(telefono: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el formato de un teléfono venezolano.
    
    Args:
        telefono: String con el teléfono a validar
        
    Returns:
        Tuple (es_valido, mensaje_error)
    """
    if not telefono:
        return True, None  # El teléfono puede ser opcional
    
    # Formato: 0414-1234567 o 04141234567
    pattern = r'^0(412|414|424|416|426)\d{7}$'
    telefono_limpio = telefono.replace('-', '').replace(' ', '')
    
    if not re.match(pattern, telefono_limpio):
        return False, "Formato de teléfono inválido. Use 0414-1234567"
    
    return True, None


def validar_datos_atleta(datos: dict) -> Tuple[bool, list]:
    """
    Valida todos los datos de un atleta.
    
    Args:
        datos: Diccionario con los datos del atleta
        
    Returns:
        Tuple (es_valido, lista_de_errores)
    """
    errores = []
    
    # Validaciones obligatorias
    if not datos.get('nombre'):
        errores.append("El nombre es requerido")
    
    if not datos.get('apellido'):
        errores.append("El apellido es requerido")
    
    # Validar cédula
    if datos.get('cedula'):
        es_valido, mensaje = validar_cedula(datos['cedula'])
        if not es_valido:
            errores.append(mensaje)
    else:
        errores.append("La cédula es requerida")
    
    # Validar email
    if datos.get('email'):
        es_valido, mensaje = validar_email(datos['email'])
        if not es_valido:
            errores.append(mensaje)
    
    # Validar edad
    if datos.get('edad'):
        es_valido, mensaje = validar_edad(datos['edad'])
        if not es_valido:
            errores.append(mensaje)
    
    # Validar peso
    if datos.get('peso'):
        es_valido, mensaje = validar_peso(datos['peso'])
        if not es_valido:
            errores.append(mensaje)
    
    # Validar estatura
    if datos.get('estatura'):
        es_valido, mensaje = validar_estatura(datos['estatura'])
        if not es_valido:
            errores.append(mensaje)
    
    # Validar teléfono
    if datos.get('telefono'):
        es_valido, mensaje = validar_telefono(datos['telefono'])
        if not es_valido:
            errores.append(mensaje)
    
    return len(errores) == 0, errores


def sanitizar_input(texto: str) -> str:
    """
    Sanitiza un input de texto eliminando caracteres peligrosos.
    
    Args:
        texto: String a sanitizar
        
    Returns:
        String sanitizado
    """
    if not texto:
        return texto
    
    # Eliminar scripts y tags HTML
    texto = re.sub(r'<script[^>]*>.*?</script>', '', texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r'<[^>]+>', '', texto)
    
    return texto.strip()
