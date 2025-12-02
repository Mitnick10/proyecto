import traceback
try:
    from supabase import AuthApiError
    print("Found in supabase")
except ImportError:
    print("Not found in supabase")
except Exception:
    traceback.print_exc()
