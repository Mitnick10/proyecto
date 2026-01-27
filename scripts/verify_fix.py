
import os
import sys

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

try:
    print("Test: Importando config...")
    from config.supabase_client import supabase, supabase_admin, SupabaseManager
    print("✅ Importación exitosa.")

    print(f"Supabase Client Type: {type(supabase)}")
    if supabase_admin:
        print(f"Supabase Admin Client Type: {type(supabase_admin)}")
    else:
        print("Supabase Admin: None (OK if no key)")

    manager = SupabaseManager()
    print("✅ Manager instanciado.")

except Exception as e:
    print(f"❌ FALLÓ: {e}")
    import traceback
    traceback.print_exc()
