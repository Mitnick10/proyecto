import os
import sys
import logging

# Añadir el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

from config.supabase_client import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_schema():
    logger.info("Inspeccionando esquema de gallery_images...")
    
    try:
        # No podemos consultar information_schema directamente vía RPC fácilmente sin funciones definidas,
        # pero podemos intentar un select y ver qué columnas y tipos nos da la metadata si el cliente lo soporta,
        # o simplemente intentar un upsert de prueba y ver el error.
        
        test_slot = 'test_debug_slot'
        data = {'slot': test_slot, 'image_data': 'test_data'}
        
        logger.info(f"Intentando upsert de prueba en slot: {test_slot}")
        try:
            res = supabase.table('gallery_images').upsert(data, on_conflict='slot').execute()
            logger.info(f"✅ Upsert exitoso: {res.data}")
            
            # Limpiar
            supabase.table('gallery_images').delete().eq('slot', test_slot).execute()
            logger.info("✅ Registro de prueba eliminado.")
            
        except Exception as e:
            logger.error(f"❌ Error en upsert por 'slot': {e}")
            
            # Intentar ver si existe el slot sin on_conflict
            logger.info("Intentando insert simple...")
            try:
                res2 = supabase.table('gallery_images').insert(data).execute()
                logger.info(f"✅ Insert exitoso: {res2.data}")
            except Exception as e2:
                logger.error(f"❌ Error en insert simple: {e2}")

    except Exception as e:
        logger.error(f"Error general: {e}")

if __name__ == "__main__":
    inspect_schema()
