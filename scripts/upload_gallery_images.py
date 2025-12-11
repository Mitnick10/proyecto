"""
Script para subir las imágenes de atletas a Supabase Storage
"""
import os
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_images():
    """Sube las imágenes de atletas al bucket de galería en Supabase"""
    
    # Rutas de las imágenes
    images = [
        ("C:/Users/UUARIO/.gemini/antigravity/brain/cc1866da-c263-44da-ad27-84210d36ec57/uploaded_image_0_1765405000590.png", "home_1.png"),
        ("C:/Users/UUARIO/.gemini/antigravity/brain/cc1866da-c263-44da-ad27-84210d36ec57/uploaded_image_1_1765405000590.png", "home_2.png"),
        ("C:/Users/UUARIO/.gemini/antigravity/brain/cc1866da-c263-44da-ad27-84210d36ec57/uploaded_image_2_1765405000590.png", "home_3.png"),
        ("C:/Users/UUARIO/.gemini/antigravity/brain/cc1866da-c263-44da-ad27-84210d36ec57/uploaded_image_3_1765405000590.png", "home_4.png"),
    ]
    
    bucket_name = "gallery"
    
    for local_path, remote_name in images:
        try:
            # Leer el archivo
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            # Intentar eliminar si existe
            try:
                supabase.storage.from_(bucket_name).remove([remote_name])
                print(f"✓ Imagen existente eliminada: {remote_name}")
            except:
                pass
            
            # Subir nueva imagen
            supabase.storage.from_(bucket_name).upload(
                remote_name,
                file_data,
                {"content-type": "image/png"}
            )
            
            print(f"✓ Imagen subida exitosamente: {remote_name}")
            
        except Exception as e:
            print(f"✗ Error subiendo {remote_name}: {e}")
    
    print("\n✅ Proceso completado!")

if __name__ == "__main__":
    print("Subiendo imágenes de atletas a Supabase Storage...")
    print("-" * 50)
    upload_images()
