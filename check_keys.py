
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
service_key = os.environ.get("SUPABASE_SERVICE_KEY")

print(f"URL: {url}")
print(f"Anon Key (first 10 chars): {key[:10] if key else 'None'}")
print(f"Service Key (first 10 chars): {service_key[:10] if service_key else 'None'}")

if not url or not key:
    print("MISSING SUPABASE_URL or SUPABASE_KEY locally")
    exit(1)

try:
    print("\n--- Testing ANON KEY ---")
    client = create_client(url, key)
    # Just checking if client object is created, real test needs network request
    # But often creating client validates format of URL/Key immediately
    print("Client created successfully.")
except Exception as e:
    print(f"Error creating ANON client: {e}")

if service_key:
    try:
        print("\n--- Testing SERVICE KEY ---")
        admin = create_client(url, service_key)
        print("Admin client created successfully.")
    except Exception as e:
        print(f"Error creating ADMIN client: {e}")
else:
    print("\nNo SUPABASE_SERVICE_KEY found.")
