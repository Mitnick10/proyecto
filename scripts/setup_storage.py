import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: Faltan credenciales (URL o SERVICE_KEY).")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

buckets = ['avatars', 'documentos']

for bucket in buckets:
    try:
        print(f"Intentando crear bucket: {bucket}...")
        # Intentar crear el bucket como público
        supabase.storage.create_bucket(bucket, options={'public': True})
        print(f"✅ Bucket '{bucket}' creado exitosamente.")
    except Exception as e:
        # Si falla, puede ser que ya exista o que haya otro error
        if "already exists" in str(e) or "Duplicate" in str(e):
            print(f"ℹ️ El bucket '{bucket}' ya existe.")
        else:
            print(f"❌ Error creando bucket '{bucket}': {e}")

print("Configuración de almacenamiento finalizada.")
