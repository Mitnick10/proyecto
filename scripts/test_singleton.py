
import os
import sys
import traceback

# Add project root to path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

try:
    print("Intentando importar SupabaseManager...")
    from config.supabase_client import supabase, supabase_admin, SupabaseManager
    from supabase import Client
    print("✅ Importación exitosa.")

    if isinstance(supabase, Client):
        print("✅ Cliente Standard 'supabase' es válido.")
    else:
        print(f"❌ Cliente Standard 'supabase' NO es válido. Es {type(supabase)}")

    if supabase_admin is None:
        print("ℹ️ Cliente Admin es None.")
    elif isinstance(supabase_admin, Client):
        print("✅ Cliente Admin 'supabase_admin' es válido.")
    else:
        print("❌ Cliente Admin tiene un tipo inesperado.")

    manager1 = SupabaseManager()
    manager2 = SupabaseManager()
    
    if manager1 is manager2:
        print("✅ Singleton funciona.")
    else:
        print("❌ Singleton FALLÓ.")

except Exception:
    traceback.print_exc()
