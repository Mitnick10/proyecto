import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase: Client = None

try:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configuradas.")
    
    # Intentar usar la Service Key primero para evitar problemas de RLS en el backend
    service_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    key_to_use = service_key if service_key else SUPABASE_KEY
    
    supabase = create_client(SUPABASE_URL, key_to_use)
    print("Conexión (compartida) con Supabase inicializada.")
except Exception as e:
    print(f"Error fatal al inicializar Supabase (compartido): {e}")