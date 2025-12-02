import traceback
try:
    import gotrue
    print("Success")
except Exception:
    traceback.print_exc()
