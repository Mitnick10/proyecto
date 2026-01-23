"""
Utilidades para procesamiento de formularios.
Centraliza la extracción y validación de datos de formularios.
"""

from typing import Any, Dict, Optional
from flask import Request
import logging

logger = logging.getLogger(__name__)


def safe_form_get(
    request: Request, 
    field: str, 
    default: Any = None, 
    convert_type: Optional[type] = None
) -> Any:
    """
    Obtiene un campo del formulario con conversión de tipo segura.
    
    Args:
        request: Objeto Request de Flask
        field: Nombre del campo a obtener
        default: Valor por defecto si el campo está vacío o no existe
        convert_type: Tipo al que convertir (int, float, bool, etc.)
        
    Returns:
        El valor del campo convertido o el default
    """
    value = request.form.get(field, '').strip()
    
    # Si está vacío, retornar default
    if not value:
        return default
    
    # Si no hay conversión, retornar como string
    if convert_type is None:
        return value
    
    # Intentar conversión
    try:
        if convert_type == bool:
            # Para checkboxes, Flask usa 'on' cuando está marcado
            return value.lower() in ('on', 'true', '1', 'yes')
        elif convert_type == int:
            return int(value)
        elif convert_type == float:
            return float(value)
        else:
            return convert_type(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Error convirtiendo campo '{field}' a {convert_type.__name__}: {e}")
        return default


def extract_athlete_data(request: Request) -> Dict[str, Any]:
    """
    Extrae y valida datos de atleta del formulario.
    Reemplaza la función obtener_datos_formulario con mejor validación.
    
    Args:
        request: Objeto Request de Flask con los datos del formulario
        
    Returns:
        Diccionario con todos los datos del atleta procesados
    """
    # Helper para campos de texto
    def get_text(field: str, default: Optional[str] = None) -> Optional[str]:
        return safe_form_get(request, field, default)
    
    # Helper para enteros
    def get_int(field: str) -> Optional[int]:
        return safe_form_get(request, field, None, int)
    
    # Helper para booleanos (checkboxes)
    def get_bool(field: str) -> bool:
        return request.form.get(field) == 'on'
    
    datos = {
        # Datos Básicos
        'nombre': get_text('nombre'),
        'apellido': get_text('apellido'),
        'cedula': get_text('cedula'),
        'edad': get_int('edad'),
        'sexo': get_text('sexo'),
        'email': get_text('email'),
        'telefono': get_text('telefono'),
        'estatus': get_text('estatus'),
        'cuenta_bancaria': get_text('cuenta_bancaria'),
        
        # Datos del Representante
        'es_menor': get_bool('es_menor'),
        'representante_nombre': get_text('representante_nombre'),
        'representante_cedula': get_text('representante_cedula'),
        'representante_telefono': get_text('representante_telefono'),
        'representante_parentesco': get_text('representante_parentesco'),
        
        # Ubicación
        'municipio': get_text('municipio'),
        'lugar_nacimiento': get_text('lugar_nacimiento'),
        'direccion': get_text('direccion'),
        'fecha_nacimiento': get_text('fecha_nacimiento'),

        # Datos Deportivos
        'disciplina': get_text('disciplina'),
        'especialidad': get_text('especialidad'),
        'categoria': get_text('categoria'),
        'tipo_beca': get_text('tipo_beca'),

        # Antropometría
        'sangre': get_text('sangre'),
        'peso': get_text('peso'),
        'estatura': get_text('estatura'),

        # Tallas
        'talla_zapato': get_text('talla_zapato'),
        'talla_franela': get_text('talla_franela'),
        'talla_short': get_text('talla_short'),
        'talla_chemise': get_text('talla_chemise'),
        'talla_mono': get_text('talla_mono'),
        'talla_competencia': get_text('talla_competencia'),

        # Información Médica y Otros (Selects Si/No)
        'usa_lentes': get_text('usa_lentes'),
        'usa_bucal': get_text('usa_bucal'),
        'usa_munequera': get_text('usa_munequera'),
        'usa_rodilleras': get_text('usa_rodilleras'),
        'dieta_deportiva': get_text('dieta_deportiva'),
        'control_medico': get_text('control_medico'),
        'estudio_social': get_text('estudio_social'),
    }
    
    return datos


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> tuple[bool, list]:
    """
    Valida que los campos requeridos estén presentes y no vacíos.
    
    Args:
        data: Diccionario con los datos a validar
        required_fields: Lista de nombres de campos requeridos
        
    Returns:
        Tupla (es_valido: bool, campos_faltantes: list)
    """
    missing = []
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    
    return len(missing) == 0, missing
