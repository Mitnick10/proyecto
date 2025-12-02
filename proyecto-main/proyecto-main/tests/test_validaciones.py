"""
Tests unitarios para el módulo de validaciones.

Cómo ejecutar estos tests:
    pytest tests/test_validaciones.py
    pytest tests/test_validaciones.py -v  (modo verbose, más detallado)
    pytest tests/test_validaciones.py::test_validar_cedula_valida  (solo un test)
"""

import sys
import os

# Agregar el directorio project al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'project'))

from utils.validaciones import (
    validar_email, 
    validar_cedula, 
    validar_edad,
    validar_peso,
    validar_estatura,
    validar_telefono,
    sanitizar_input
)


# ============================================
# TESTS PARA VALIDAR_EMAIL
# ============================================

def test_validar_email_valido():
    """Test: Email válido debe pasar la validación"""
    es_valido, error = validar_email("juan@gmail.com")
    assert es_valido == True
    assert error == None


def test_validar_email_invalido_sin_arroba():
    """Test: Email sin @ debe fallar"""
    es_valido, error = validar_email("juangmail.com")
    assert es_valido == False
    assert "inválido" in error.lower()


def test_validar_email_invalido_sin_dominio():
    """Test: Email sin dominio debe fallar"""
    es_valido, error = validar_email("juan@")
    assert es_valido == False
    assert "inválido" in error.lower()


def test_validar_email_vacio():
    """Test: Email vacío debe fallar"""
    es_valido, error = validar_email("")
    assert es_valido == False
    assert "requerido" in error.lower()


# ============================================
# TESTS PARA VALIDAR_CEDULA
# ============================================

def test_validar_cedula_valida_v():
    """Test: Cédula venezolana con V debe pasar"""
    es_valido, error = validar_cedula("V-12345678")
    assert es_valido == True
    assert error == None


def test_validar_cedula_valida_e():
    """Test: Cédula extranjera con E debe pasar"""
    es_valido, error = validar_cedula("E-12345678")
    assert es_valido == True
    assert error == None


def test_validar_cedula_sin_guion():
    """Test: Cédula sin guion también debe pasar"""
    es_valido, error = validar_cedula("V12345678")
    assert es_valido == True
    assert error == None


def test_validar_cedula_minuscula():
    """Test: Cédula en minúscula debe pasar (se convierte a mayúscula)"""
    es_valido, error = validar_cedula("v-12345678")
    assert es_valido == True
    assert error == None


def test_validar_cedula_invalida_letra_incorrecta():
    """Test: Cédula con letra diferente a V o E debe fallar"""
    es_valido, error = validar_cedula("X-12345678")
    assert es_valido == False
    assert "inválido" in error.lower()


def test_validar_cedula_invalida_muy_corta():
    """Test: Cédula muy corta debe fallar"""
    es_valido, error = validar_cedula("V-123")
    assert es_valido == False
    assert "inválido" in error.lower()


def test_validar_cedula_vacia():
    """Test: Cédula vacía debe fallar"""
    es_valido, error = validar_cedula("")
    assert es_valido == False
    assert "requerida" in error.lower()


# ============================================
# TESTS PARA VALIDAR_EDAD
# ============================================

def test_validar_edad_valida():
    """Test: Edad válida (entre 5 y 100) debe pasar"""
    es_valido, error = validar_edad("25")
    assert es_valido == True
    assert error == None


def test_validar_edad_minima():
    """Test: Edad mínima (5) debe pasar"""
    es_valido, error = validar_edad("5")
    assert es_valido == True
    assert error == None


def test_validar_edad_maxima():
    """Test: Edad máxima (100) debe pasar"""
    es_valido, error = validar_edad("100")
    assert es_valido == True
    assert error == None


def test_validar_edad_muy_baja():
    """Test: Edad menor a 5 debe fallar"""
    es_valido, error = validar_edad("4")
    assert es_valido == False
    assert "entre 5 y 100" in error.lower()


def test_validar_edad_muy_alta():
    """Test: Edad mayor a 100 debe fallar"""
    es_valido, error = validar_edad("101")
    assert es_valido == False
    assert "entre 5 y 100" in error.lower()


def test_validar_edad_no_numerica():
    """Test: Edad no numérica debe fallar"""
    es_valido, error = validar_edad("abc")
    assert es_valido == False
    assert "número válido" in error.lower()


def test_validar_edad_vacia():
    """Test: Edad vacía debe pasar (es opcional)"""
    es_valido, error = validar_edad("")
    assert es_valido == True
    assert error == None


# ============================================
# TESTS PARA VALIDAR_TELEFONO
# ============================================

def test_validar_telefono_valido_con_guion():
    """Test: Teléfono válido con guión debe pasar"""
    es_valido, error = validar_telefono("0414-1234567")
    assert es_valido == True
    assert error == None


def test_validar_telefono_valido_sin_guion():
    """Test: Teléfono válido sin guión debe pasar"""
    es_valido, error = validar_telefono("04141234567")
    assert es_valido == True
    assert error == None


def test_validar_telefono_valido_0412():
    """Test: Teléfono con código 0412 debe pasar"""
    es_valido, error = validar_telefono("0412-7654321")
    assert es_valido == True
    assert error == None


def test_validar_telefono_invalido_codigo():
    """Test: Teléfono con código inválido debe fallar"""
    es_valido, error = validar_telefono("0411-1234567")
    assert es_valido == False
    assert "inválido" in error.lower()


def test_validar_telefono_muy_corto():
    """Test: Teléfono muy corto debe fallar"""
    es_valido, error = validar_telefono("0414-123")
    assert es_valido == False
    assert "inválido" in error.lower()


def test_validar_telefono_vacio():
    """Test: Teléfono vacío debe pasar (es opcional)"""
    es_valido, error = validar_telefono("")
    assert es_valido == True
    assert error == None


# ============================================
# TESTS PARA SANITIZAR_INPUT
# ============================================

def test_sanitizar_input_script_tag():
    """Test: Script tags deben ser eliminados"""
    texto = "Hola <script>alert('hack')</script> mundo"
    resultado = sanitizar_input(texto)
    assert "<script>" not in resultado
    assert "alert" not in resultado
    assert "Hola" in resultado and "mundo" in resultado


def test_sanitizar_input_html_tags():
    """Test: Tags HTML deben ser eliminados"""
    texto = "Texto <b>con</b> <i>tags</i>"
    resultado = sanitizar_input(texto)
    assert "<b>" not in resultado
    assert "<i>" not in resultado
    assert "Texto con tags" == resultado


def test_sanitizar_input_texto_limpio():
    """Test: Texto sin tags debe permanecer igual"""
    texto = "Texto normal sin problemas"
    resultado = sanitizar_input(texto)
    assert resultado == texto


def test_sanitizar_input_espacios():
    """Test: Espacios al inicio y final deben eliminarse"""
    texto = "   Texto con espacios   "
    resultado = sanitizar_input(texto)
    assert resultado == "Texto con espacios"


def test_sanitizar_input_vacio():
    """Test: Input vacío o None debe retornar vacío/None"""
    assert sanitizar_input("") == ""
    assert sanitizar_input(None) == None


# ============================================
# RESUMEN DE COBERTURA
# ============================================

"""
RESUMEN DE TESTS:
- validar_email: 4 tests
- validar_cedula: 7 tests
- validar_edad: 7 tests
- validar_telefono: 6 tests
- sanitizar_input: 5 tests

TOTAL: 29 tests unitarios ✅

Para ejecutar:
    pytest tests/test_validaciones.py -v

Para ver cobertura:
    pytest --cov=project.utils tests/test_validaciones.py
"""
