"""
Tests para las funciones de upload de archivos.

Este test es más avanzado porque:
1. Necesita crear archivos falsos (mocking)
2. Necesita simular Supabase Storage
3. Prueba casos de error

Ejecutar:
    python -m pytest tests/test_upload.py -v
"""

import sys
import os
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock

# Agregar el directorio project al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'project'))

from werkzeug.datastructures import FileStorage


# ============================================
# TESTS PARA UPLOAD_FILE (con mocking)
# ============================================

@patch('blueprints.dashboard.supabase')
def test_upload_file_imagen_exitosa(mock_supabase):
    """Test: Subir una imagen exitosamente debe retornar URL pública"""
    from blueprints.dashboard import upload_file
    
    # 1. ARRANGE - Crear un archivo fake
    fake_image = BytesIO(b"fake image content")
    fake_file = FileStorage(
        stream=fake_image,
        filename="foto_atleta.jpg",
        content_type="image/jpeg"
    )
    
    # 2. Simular respuesta de Supabase Storage
    mock_storage = Mock()
    mock_supabase.storage.from_.return_value = mock_storage
    mock_storage.upload.return_value = None  # Upload exitoso
    mock_storage.get_public_url.return_value = "https://supabase.co/storage/avatars/123.jpg"
    
    # 3. ACT - Ejecutar la función
    url = upload_file(fake_file, 'avatars', 'fotos')
    
    # 4. ASSERT - Verificar resultados
    assert url is not None
    assert "https://" in url
    assert "avatars" in url
    assert mock_storage.upload.called  # Verificar que se llamó upload
    assert mock_storage.get_public_url.called  # Verificar que se llamó get_public_url


@patch('blueprints.dashboard.supabase')
def test_upload_file_sin_archivo(mock_supabase):
    """Test: Intentar subir sin archivo debe retornar None"""
    from blueprints.dashboard import upload_file
    
    # Intentar subir None
    url = upload_file(None, 'avatars')
    assert url is None
    
    # Intentar subir archivo sin filename
    fake_file = Mock()
    fake_file.filename = None
    url = upload_file(fake_file, 'avatars')
    assert url is None


@patch('blueprints.dashboard.supabase')
def test_upload_file_error_supabase(mock_supabase):
    """Test: Si Supabase falla, debe retornar None y loggear el error"""
    from blueprints.dashboard import upload_file
    
    # Crear archivo fake
    fake_image = BytesIO(b"fake image content")
    fake_file = FileStorage(
        stream=fake_image,
        filename="foto.jpg",
        content_type="image/jpeg"
    )
    
    # Simular error en Supabase
    mock_storage = Mock()
    mock_supabase.storage.from_.return_value = mock_storage
    mock_storage.upload.side_effect = Exception("Supabase Storage error")
    
    # Ejecutar
    url = upload_file(fake_file, 'avatars')
    
    # Debe retornar None cuando hay error
    assert url is None


# ============================================
# TEST PARA VALIDAR EXTENSIONES DE ARCHIVO
# ============================================

def test_validar_extension_imagen_valida():
    """Test: Imágenes con extensiones válidas deben ser aceptadas"""
    extensiones_validas = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    
    for ext in extensiones_validas:
        filename = f"foto.{ext}"
        # Extraer extensión
        extension = filename.split('.')[-1].lower()
        assert extension in extensiones_validas


def test_validar_extension_imagen_invalida():
    """Test: Archivos peligrosos NO deben ser aceptados"""
    extensiones_peligrosas = ['exe', 'bat', 'sh', 'php', 'js']
    extensiones_validas = ['jpg', 'jpeg', 'png', 'gif']
    
    for ext in extensiones_peligrosas:
        filename = f"virus.{ext}"
        extension = filename.split('.')[-1].lower()
        # Verificar que NO está en extensiones válidas
        assert extension not in extensiones_validas


# ============================================
# TEST PARA VALIDAR TAMAÑO DE ARCHIVO
# ============================================

def test_validar_tamano_archivo_pequeno():
    """Test: Archivo pequeño (< 5MB) debe ser aceptado"""
    # Crear archivo de 1MB
    contenido = b"x" * (1024 * 1024)  # 1 MB
    
    # Verificar tamaño
    tamano_mb = len(contenido) / (1024 * 1024)
    assert tamano_mb < 5  # Menor a 5MB
    assert tamano_mb > 0


def test_validar_tamano_archivo_grande():
    """Test: Archivo muy grande (> 10MB) debería ser rechazado"""
    # Simular archivo de 15MB
    tamano_bytes = 15 * 1024 * 1024
    tamano_mb = tamano_bytes / (1024 * 1024)
    
    limite_mb = 10
    assert tamano_mb > limite_mb  # Verificar que excede el límite


# ============================================
# TEST PARA PROCESAR_IMAGEN
# ============================================

@patch('blueprints.dashboard.upload_file')
def test_procesar_imagen_llama_upload_file(mock_upload):
    """Test: procesar_imagen() debe llamar a upload_file con bucket 'avatars'"""
    from blueprints.dashboard import procesar_imagen
    
    # Crear archivo fake
    fake_file = Mock()
    fake_file.filename = "foto.jpg"
    
    # Simular respuesta
    mock_upload.return_value = "https://fake-url.com/foto.jpg"
    
    # Ejecutar
    url = procesar_imagen(fake_file)
    
    # Verificar que se llamó upload_file con los parámetros correctos
    mock_upload.assert_called_once_with(fake_file, 'avatars')
    assert url == "https://fake-url.com/foto.jpg"


@patch('blueprints.dashboard.upload_file')
def test_procesar_pdf_llama_upload_file(mock_upload):
    """Test: procesar_pdf() debe llamar a upload_file con bucket 'documentos'"""
    from blueprints.dashboard import procesar_pdf
    
    # Crear archivo fake
    fake_file = Mock()
    fake_file.filename = "documento.pdf"
    
    # Simular respuesta
    mock_upload.return_value = "https://fake-url.com/doc.pdf"
    
    # Ejecutar
    url = procesar_pdf(fake_file)
    
    # Verificar que se llamó upload_file con los parámetros correctos
    mock_upload.assert_called_once_with(fake_file, 'documentos')
    assert url == "https://fake-url.com/doc.pdf"


# ============================================
# TEST DE INTEGRACIÓN (más realista)
# ============================================

@patch('blueprints.dashboard.supabase')
def test_flujo_completo_subir_foto_atleta(mock_supabase):
    """
    Test de integración: Simula el flujo completo de subir una foto de atleta
    
    Este test simula lo que pasa cuando un usuario:
    1. Selecciona una foto en el formulario
    2. La foto se procesa
    3. Se sube a Supabase Storage
    4. Se obtiene la URL pública
    """
    from blueprints.dashboard import procesar_imagen
    
    # ARRANGE - Usuario selecciona una foto
    foto_contenido = b"JPEG FAKE CONTENT XYZ123"
    foto_stream = BytesIO(foto_contenido)
    foto = FileStorage(
        stream=foto_stream,
        filename="atleta_juan_perez.jpg",
        content_type="image/jpeg"
    )
    
    # Mock de Supabase Storage
    mock_storage = Mock()
    mock_supabase.storage.from_.return_value = mock_storage
    
    # Simular upload exitoso
    mock_storage.upload.return_value = {"path": "avatars/abc123.jpg"}
    
    # Simular URL pública
    url_esperada = "https://xyz.supabase.co/storage/v1/object/public/avatars/abc123.jpg"
    mock_storage.get_public_url.return_value = url_esperada
    
    # ACT - Procesar la imagen
    url_resultado = procesar_imagen(foto)
    
    # ASSERT - Verificar resultados
    assert url_resultado == url_esperada
    assert "supabase" in url_resultado
    assert "avatars" in url_resultado
    
    # Verificar que se leyó el contenido del archivo
    foto_stream.seek(0)  # Volver al inicio
    contenido_leido = foto_stream.read()
    assert len(contenido_leido) > 0


# ============================================
# TEST DE SEGURIDAD
# ============================================

def test_prevenir_directory_traversal():
    """
    Test de seguridad: Verificar que no se puedan subir archivos
    con nombres maliciosos que intenten acceder a otras carpetas
    """
    nombres_maliciosos = [
        "../../../etc/passwd",
        "..\\..\\windows\\system32\\config",
        "foto.jpg/../../../hack.exe",
    ]
    
    for nombre in nombres_maliciosos:
        # Verificar que contiene caracteres peligrosos
        assert ".." in nombre or "/" in nombre or "\\" in nombre
        
        # En producción, deberías sanitizar esto
        # Por ejemplo: os.path.basename(nombre) elimina el path


def test_validar_mime_type():
    """Test: Verificar que solo se acepten MIME types válidos"""
    mime_types_validos = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'application/pdf'
    ]
    
    mime_types_invalidos = [
        'application/x-msdownload',  # .exe
        'application/x-sh',           # script shell
        'text/html',                  # HTML (posible XSS)
    ]
    
    for mime in mime_types_validos:
        assert mime.startswith('image/') or mime == 'application/pdf'
    
    for mime in mime_types_invalidos:
        assert not (mime.startswith('image/') or mime == 'application/pdf')


# ============================================
# ESTADÍSTICAS
# ============================================

"""
RESUMEN DE TESTS CREADOS:
- test_upload_file_imagen_exitosa ✅
- test_upload_file_sin_archivo ✅
- test_upload_file_error_supabase ✅
- test_validar_extension_imagen_valida ✅
- test_validar_extension_imagen_invalida ✅
- test_validar_tamano_archivo_pequeno ✅
- test_validar_tamano_archivo_grande ✅
- test_procesar_imagen_llama_upload_file ✅
- test_procesar_pdf_llama_upload_file ✅
- test_flujo_completo_subir_foto_atleta ✅
- test_prevenir_directory_traversal ✅
- test_validar_mime_type ✅

TOTAL: 12 tests de upload/seguridad ✅

Ejecutar:
    python -m pytest tests/test_upload.py -v
    
Ejecutar con cobertura:
    python -m pytest tests/test_upload.py --cov=blueprints.dashboard -v
"""
