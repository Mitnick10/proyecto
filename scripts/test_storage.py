import os
import sys
import logging

# Añadir el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

from config.supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_storage():
    logger.info("Testeando Supabase Storage...")
    bucket_name = 'becas-public'
    test_filename = f"test_{int(datetime.now().timestamp())}.txt"
    file_content = b"Prueba de conexion a Supabase Storage"
    
    try:
        # 1. Intentar listar buckets para ver si tenemos acceso y si existe el bucket
        logger.info("Listando buckets...")
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        logger.info(f"Buckets encontrados: {bucket_names}")
        
        if bucket_name not in bucket_names:
            logger.error(f"❌ El bucket '{bucket_name}' NO EXISTE.")
            return

        # 2. Intentar subir algo
        logger.info(f"Subiendo archivo de prueba: {test_filename}")
        res = supabase.storage.from_(bucket_name).upload(
            path=test_filename,
            file=file_content,
            file_options={"content-type": "text/plain"}
        )
        logger.info(f"Resultado upload: {res}")
        
        # 3. Obtener URL pública
        url = supabase.storage.from_(bucket_name).get_public_url(test_filename)
        logger.info(f"URL pública generada: {url}")
        
        # En algunas versiones de supabase-py, get_public_url devuelve un objeto con un atributo 'public_url'
        # o retorna un string directamente. Vamos a ver que imprime.
        
    except Exception as e:
        logger.error(f"❌ Error durante el test: {e}")

if __name__ == "__main__":
    from datetime import datetime
    test_storage()
