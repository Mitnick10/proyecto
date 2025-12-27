import os
import sys
import logging

# Añadir el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

from config.supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_gallery():
    logger.info("Listando todos los registros de gallery_images...")
    try:
        res = supabase.table('gallery_images').select('id', 'slot', 'image_data').execute()
        for item in res.data:
            logger.info(f"ID: {item['id']} | Slot: {item['slot']} | Data (prefix): {item['image_data'][:100]}...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    list_gallery()
