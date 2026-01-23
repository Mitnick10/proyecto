import os
import sys
# Añadir el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))
from config.supabase_client import supabase

def check_columns():
    try:
        res = supabase.table('becas').select('*').limit(1).execute()
        if res.data:
            print("Columnas en 'becas':", res.data[0].keys())
        else:
            print("La tabla 'becas' está vacía o no se puede acceder.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
