import os
import sys
import uuid
# Añadir el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))
from config.supabase_client import supabase

def add_image(image_path, slot):
    try:
        bucket = 'becas-public'
        ext = image_path.split('.')[-1]
        filename = f"gallery/{slot}_{uuid.uuid4().hex[:8]}.{ext}"
        
        with open(image_path, 'rb') as f:
            file_bytes = f.read()
            
        print(f"Subiendo {image_path} a {bucket}/{filename}...")
        supabase.storage.from_(bucket).upload(path=filename, file=file_bytes, file_options={"content-type": f"image/{ext}"})
        
        public_url = supabase.storage.from_(bucket).get_public_url(filename)
        print(f"URL pública: {public_url}")
        
        data = {
            'slot': slot,
            'image_data': public_url
        }
        
        supabase.table('gallery_images').upsert(data, on_conflict='slot').execute()
        print(f"✅ Slot {slot} actualizado en la DB.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: py scripts/add_home_image.py <image_path> <slot>")
    else:
        add_image(sys.argv[1], sys.argv[2])
