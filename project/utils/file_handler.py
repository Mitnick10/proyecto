import logging
import uuid
from datetime import datetime
from config.supabase_client import supabase

logger = logging.getLogger(__name__)

def upload_file_to_supabase(file, bucket, folder):
    """
    Sube un archivo a Supabase Storage y retorna la URL pública.
    """
    if not file or not file.filename:
        return None
        
    try:
        # Generar nombre único: timestamp_uuid_filename
        ext = file.filename.split('.')[-1]
        filename = f"{folder}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        
        # Leer archivo
        file.seek(0)
        file_bytes = file.read()
        
        # Subir a Supabase
        # file_options = {"content-type": file.content_type} # Opcional
        res = supabase.storage.from_(bucket).upload(path=filename, file=file_bytes, file_options={"content-type": file.content_type})
        
        # Obtener URL pública
        public_url = supabase.storage.from_(bucket).get_public_url(filename)
        
        return public_url
    except Exception as e:
        logger.error(f"Error subiendo archivo a {bucket}/{folder}: {e}")
        print(f"Error subiendo archivo: {e}")
        return None

def procesar_imagen(file):
    """
    Sube la imagen a Supabase Storage (bucket 'becas-public', folder 'imagenes').
    Retorna la URL pública.
    """
    return upload_file_to_supabase(file, 'becas-public', 'imagenes')

def procesar_pdf(file):
    """
    Sube el PDF a Supabase Storage (bucket 'becas-public', folder 'documentos').
    Retorna la URL pública.
    """
    return upload_file_to_supabase(file, 'becas-public', 'documentos')
