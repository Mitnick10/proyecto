import os

def read_env():
    env_path = os.path.join('c:\\Users\\UUARIO\\Desktop\\proyecto - copia\\proyecto', '.env')
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if 'SUPABASE_URL' in line or 'SUPABASE_KEY' in line:
                    # Ocultar la mayoría de la key pero mostrar el final para identificar
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        val = parts[1]
                        hidden_val = val[:10] + "..." + val[-5:] if len(val) > 15 else "***"
                        print(f"{parts[0]} = {hidden_val}")
    except Exception as e:
        print(f"Error reading .env: {e}")

if __name__ == "__main__":
    read_env()
