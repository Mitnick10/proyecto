
import os
import sys
import re
from urllib.parse import urlparse, unquote
import requests

# Add project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'project'))

try:
    from config.supabase_client import supabase_admin
    
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        def log(msg):
            print(msg)
            f.write(msg + '\n')
            
        log("--- DIAGNÓSTICO DE ACCESO A PDF (V4) ---")

        # 2. Analizar documento específico
        log("\n2. Analizando documento de BD:")
        try:
            doc = supabase_admin.table('documentos').select('*').limit(1).single().execute()
            if doc.data:
                real_url = str(doc.data.get('archivo'))
                log(f"   URL: {real_url}")
                
                # Parsear
                decoded = unquote(real_url.split('?')[0])
                parts = decoded.split('/object/public/')
                
                if len(parts) > 1:
                    suffix = parts[1] 
                    log(f"   Suffix: {suffix}")
                    
                    # Split bucket/path
                    if '/' in suffix:
                        bucket_candidate = suffix.split('/')[0]
                        path_candidate = '/'.join(suffix.split('/')[1:])
                        
                        log(f"   Hipótesis -> Bucket: '{bucket_candidate}', Path: '{path_candidate}'")
                        
                        # Probar firma
                        try:
                            res = supabase_admin.storage.from_(bucket_candidate).create_signed_url(path_candidate, 60)
                            
                            # Handle weird return types safely
                            s_url = None
                            if isinstance(res, dict): s_url = res.get('signedURL')
                            elif hasattr(res, 'signedURL'): s_url = res.signedURL
                            elif isinstance(res, str): s_url = res
                            else: log(f"   Tipo de respuesta desconocido: {type(res)}")
                            
                            if s_url:
                                s_url = str(s_url) # Force string
                                log(f"   Firmado: {s_url}")
                                
                                resp = requests.get(s_url)
                                log(f"   Status HTTP: {resp.status_code}")
                            else:
                                log(f"   ❌ No devolvió URL. Respuesta: {res}")

                        except Exception as e:
                            log(f"   Error firmando: {e}")
                    else:
                        log("   Suffix no tiene '/' para separar bucket/path")
                else:
                    log("   No se encontró '/object/public/' en la URL")
            else:
                log("   Tabla vacia.")
        except Exception as e:
            log(f"❌ Error BD: {e}")

except Exception as e:
    print(f"❌ Error general en script: {e}")
    import traceback
    traceback.print_exc()
