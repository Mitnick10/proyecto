import os
import sys
import requests
import logging

# Añadir el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

from config.supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_data():
    logger.info("Verificando integridad de datos y accesibilidad...")
    
    # 1. Atletas
    logger.info("\n--- BECAS (ATLETAS) ---")
    res_becas = supabase.table('becas').select('id', 'nombre', 'foto').not_.is_('foto', 'null').limit(3).execute()
    for b in res_becas.data:
        url = b['foto']
        logger.info(f"ID {b['id']} ({b['nombre']}): Foto URL = {url}")
        if url.startswith('http'):
            try:
                head = requests.head(url)
                logger.info(f"   Status: {head.status_code}")
            except Exception as e:
                logger.error(f"   Error al acceder: {e}")
        else:
            logger.warning("   ⚠️ Aún es Base64 o no es URL!")

    # 2. Galería
    logger.info("\n--- GALLERY_IMAGES ---")
    res_gallery = supabase.table('gallery_images').select('slot', 'image_data').limit(3).execute()
    for g in res_gallery.data:
        url = g['image_data']
        logger.info(f"Slot {g['slot']}: Image Data = {url[:50]}...")
        if url.startswith('http'):
            try:
                head = requests.head(url)
                logger.info(f"   Status: {head.status_code}")
            except Exception as e:
                logger.error(f"   Error al acceder: {e}")
        else:
            logger.warning("   ⚠️ Aún es Base64 o no es URL!")

if __name__ == "__main__":
    verify_data()
