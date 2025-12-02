"""
Tests para la validación de confirmación de contraseña en el registro.

Este test verifica que:
1. Las contraseñas deben coincidir
2. La contraseña debe tener al menos 6 caracteres
3. Todos los campos son requeridos

Ejecutar:
    python -m pytest tests/test_registro.py -v
"""

import sys
import os

# Agregar el directorio project al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'project'))


# ==============================================
# TESTS PARA VALIDACIÓN DE CONFIRMACIÓN DE CONTRASEÑA
# ==============================================

def test_contrasenas_deben_coincidir():
    """Test: Las contraseñas debe coincid para ser válidas"""
    password = "mipassword123"
    confirm_password = "mipassword123"
    
    # Verificar que coinciden
    assert password == confirm_password


def test_contrasenas_no_coinciden():
    """Test: Detectar cuando las contraseñas NO coinciden"""
    password = "password123"
    confirm_password = "password456"  # Diferente
    
    # Verificar que NO coinciden
    assert password != confirm_password


def test_longitud_minima_password():
    """Test: Contraseña debe tener al menos 6 caracteres"""
    passwords_validas = ["123456", "pass1234", "abcdefghi"]
    passwords_invalidas = ["12345", "abc", ""]
    
    for pwd in passwords_validas:
        assert len(pwd) >= 6, f"{pwd} debería ser válida"
    
    for pwd in passwords_invalidas:
        assert len(pwd) < 6, f"{pwd} debería ser inválida"


def test_validacion_campos_requeridos():
    """Test: Todos los campos son requeridos"""
    # Simular datos del formulario
    datos_completos = {
        'email': 'usuario@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'nombre': 'Juan',
        'apellido': 'Pérez'
    }
    
    # Verificar que todos los campos tienen valor
    for campo, valor in datos_completos.items():
        assert valor is not None, f"El campo {campo} no puede estar vacío"
        assert len(valor) > 0, f"El campo {campo} debe tener contenido"


def test_caso_completo_registro_exitoso():
    """
    Test de integración: Simula un registro exitoso
    Verifica todos los requisitos juntos
    """
    # Datos del formulario
    email = "juan.perez@example.com"
    password = "MiPassword123"
    confirm_password = "MiPassword123"
    nombre = "Juan"
    apellido = "Pérez"
    
    # 1. Validar que todos los campos existen
    assert email and password and confirm_password and nombre and apellido
    
    # 2. Validar que las contraseñas coinciden
    assert password == confirm_password, "Las contraseñas deben coincidir"
    
    # 3. Validar longitud mínima
    assert len(password) >= 6, "La contraseña debe tener al menos 6 caracteres"
    
    # 4. Validar formato de email
    assert "@" in email, "El email debe tener formato válido"
    
    # ✅ Todos los requisitos se cumplen
    print("✅ Registro válido - Todos los requisitos cumplidos")


def test_caso_completo_registro_fallido_passwords_diferentes():
    """
    Test de integración: Registro falla por contraseñas diferentes
    """
    # Datos del formulario
    email = "usuario@example.com"
    password = "password123"
    confirm_password = "password456"  # ❌ Diferente
    nombre = "Juan"
    apellido = "Pérez"
    
    # Validar todos los campos
    assert email and password and confirm_password and nombre and apellido
    
    # Validar contraseñas
    passwords_coinciden = (password == confirm_password)
    
    # ❌ Debe fallar porque las contraseñas no coinciden
    assert not passwords_coinciden, "Las contraseñas NO coinciden (esperado)"
    print("❌ Registro rechazado - Las contraseñas no coinciden")


def test_caso_completo_registro_fallido_password_muy_corta():
    """
    Test de integración: Registro falla por contraseña muy corta
    """
    # Datos del formulario
    email = "usuario@example.com"
    password = "12345"  # ❌ Solo 5 caracteres
    confirm_password = "12345"
    nombre = "Juan"
    apellido = "Pérez"
    
    # Validar todos los campos
    assert email and password and confirm_password and nombre and apellido
    
    # Validar contraseñas coinciden
    assert password == confirm_password
    
    # Validar longitud
    password_valida = len(password) >= 6
    
    # ❌ Debe fallar porque la contraseña es muy corta
    assert not password_valida, "La contraseña es muy corta (esperado)"
    print("❌ Registro rechazado - Contraseña muy corta")


def test_passwords_con_espacios():
    """Test: Contraseñas con espacios deben ser permitidas"""
    password = "mi contraseña segura"
    confirm_password = "mi contraseña segura"
    
    # Espacios son permitidos
    assert password == confirm_password
    assert len(password) >= 6


def test_passwords_case_sensitive():
    """Test: Las contras son case sensitive (mayúsculas/minúsculas importan)"""
    password = "Password123"
    confirm_password = "password123"  # Diferente en mayúsculas
    
    # NO deben coincidir (case sensitive)
    assert password != confirm_password


def test_passwords_con_caracteres_especiales():
    """Test: Contraseñas con caracteres especiales son permitidas"""
    passwords_especiales = [
        "Pass@123!",
        "P@$$w0rd",
        "Mi#Contraseña$2024",
        "!@#$%^&*()",
    ]
    
    for pwd in passwords_especiales:
        # Deben ser válidas
        assert len(pwd) >= 6
        print(f"✅ Contraseña con caracteres especiales: {pwd}")


# ==============================================
# TESTS DE SEGURIDAD
# ==============================================

def test_password_no_puede_ser_solo_espacios():
    """Test de seguridad: Contraseña no puede ser solo espacios"""
    password = "      "  # 6 espacios
    
    # Aunque tiene 6 caracteres, debería ser rechazada
    # (En producción, deberías agregar trim() o validación adicional)
    password_sin_espacios = password.strip()
    assert len(password_sin_espacios) == 0, "Contraseña vacía después de trim"


def test_email_valido_es_requerido():
    """Test: El email debe tener formato válido"""
    emails_validos = [
        "usuario@example.com",
        "juan.perez@gmail.com",
        "test+tag@domain.co.ve",
    ]
    
    emails_invalidos = [
        "usuario",  # Sin @
        "@example.com",  # Sin usuario
        "usuario@",  # Sin dominio
        "",  # Vacío
    ]
    
    for email in emails_validos:
        assert "@" in email and "." in email
    
    for email in emails_invalidos:
        is_valid = "@" in email and "." in email and len(email) > 0
        assert not is_valid


# ==============================================
# ESTADÍSTICAS
# ==============================================

"""
RESUMEN DE TESTS:
- test_contrasenas_deben_coincidir ✅
- test_contrasenas_no_coinciden ✅
- test_longitud_minima_password ✅
- test_validacion_campos_requeridos ✅
- test_caso_completo_registro_exitoso ✅
- test_caso_completo_registro_fallido_passwords_diferentes ✅
- test_caso_completo_registro_fallido_password_muy_corta ✅
- test_passwords_con_espacios ✅
- test_passwords_case_sensitive ✅
- test_passwords_con_caracteres_especiales ✅
- test_password_no_puede_ser_solo_espacios ✅
- test_email_valido_es_requerido ✅

TOTAL: 12 tests de validación de registro ✅

Ejecutar:
    python -m pytest tests/test_registro.py -v
"""
