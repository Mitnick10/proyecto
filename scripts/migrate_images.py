import os
import sys
import base64
import logging
import uuid
from datetime import datetime

# Añadir el directorio del proyecto al path para poder importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

from config.supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_images():
    logger.info("Iniciando migración de imágenes de Base64 a Supabase Storage...")
    bucket = 'becas-public'
    
    # --- 1. MIGRAR BECAS (FOTOS ATLETAS) ---
    try:
        result = supabase.table('becas').select('id', 'nombre', 'apellido', 'foto').not_.is_('foto', 'null').execute()
        atletas = result.data
        logger.info(f"--- Becas (Atletas): Found {len(atletas)} items ---")
        
        for atleta in atletas:
            foto_data = atleta.get('foto')
            atleta_id = atleta.get('id')
            nombre = f"{atleta.get('nombre')} {atleta.get('apellido')}"
            
            if foto_data.startswith('http'):
                continue
                
            if foto_data.startswith('data:image'):
                try:
                    header, encoded = foto_data.split(",", 1)
                    image_bytes = base64.b64decode(encoded)
                    ext = header.split('/')[1].split(';')[0]
                    if ext == 'jpeg': ext = 'jpg'
                    
                    filename = f"imagenes/{atleta_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                    content_type = header.split(':')[1].split(';')[0]
                    
                    logger.info(f"Migrating photo for {nombre}...")
                    supabase.storage.from_(bucket).upload(path=filename, file=image_bytes, file_options={"content-type": content_type})
                    public_url = supabase.storage.from_(bucket).get_public_url(filename)
                    supabase.table('becas').update({'foto': public_url}).eq('id', atleta_id).execute()
                    logger.info(f"✅ Migrated Atleta {atleta_id}")
                except Exception as e:
                    logger.error(f"❌ Error migrando atleta {atleta_id}: {e}")
    except Exception as e:
        logger.error(f"Error querying becas: {e}")

    # --- 2. MIGRAR GALLERY_IMAGES ---
    try:
        res_gallery = supabase.table('gallery_images').select('id', 'slot', 'image_data').execute()
        gallery = res_gallery.data
        logger.info(f"--- Gallery Images: Found {len(gallery)} items ---")
        
        for item in gallery:
            image_data = item.get('image_data')
            slot = item.get('slot')
            item_id = item.get('id')
            
            if not image_data or image_data.startswith('http'):
                continue
                
            if image_data.startswith('data:image'):
                try:
                    header, encoded = image_data.split(",", 1)
                    image_bytes = base64.b64decode(encoded)
                    ext = header.split('/')[1].split(';')[0]
                    if ext == 'jpeg': ext = 'jpg'
                    
                    filename = f"gallery/{slot}_{uuid.uuid4().hex[:8]}.{ext}"
                    content_type = header.split(':')[1].split(';')[0]
                    
                    logger.info(f"Migrating gallery image for slot {slot}...")
                    supabase.storage.from_(bucket).upload(path=filename, file=image_bytes, file_options={"content-type": content_type})
                    public_url = supabase.storage.from_(bucket).get_public_url(filename)
                    
                    # Actualizar image_data con la URL de Storage
                    supabase.table('gallery_images').update({'image_data': public_url}).eq('id', item_id).execute()
                    logger.info(f"✅ Migrated Gallery Slot {slot}")
                except Exception as e:
                    logger.error(f"❌ Error migrando slot {slot}: {e}")
    except Exception as e:
        logger.error(f"Error querying gallery_images: {e}")

    logger.info("Migración finalizada.")

if __name__ == "__main__":
    migrate_images()
