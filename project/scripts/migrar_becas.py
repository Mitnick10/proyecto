import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase_client import supabase

def migrar_becas():
    print("Iniciando migración de programas de becas...")
    
    # Mapping definition
    MAPPING = {
        "Alto Rendimiento": "Elite Nacional",
        "Talento Deportivo": "Talento Deportivo Guariqueño",
        "Apoyo Económico": "Esperanza Olímpica Guariqueña",
        "Otro": "Talento Deportivo Guariqueño"
    }
    
    # Default for unknown types
    DEFAULT_NEW = "Talento Deportivo Guariqueño"

    try:
        # 1. Fetch all athletes
        response = supabase.table('becas').select('id, nombre, apellido, tipo_beca').execute()
        atletas = response.data
        
        print(f"Total de atletas encontrados: {len(atletas)}")
        
        updated_count = 0
        
        for atleta in atletas:
            old_type = atleta.get('tipo_beca')
            
            # Determine new type
            new_type = MAPPING.get(old_type, DEFAULT_NEW)
            
            # Check if update is needed (if current type is not one of the new valid ones)
            valid_new_types = [
                "Esperanza Olímpica Guariqueña",
                "Elite Internacional",
                "Proyección a Selección Nacional",
                "Elite Nacional",
                "Talento Deportivo Guariqueño"
            ]
            
            if old_type not in valid_new_types:
                print(f"Migrando {atleta['nombre']} {atleta['apellido']}: '{old_type}' -> '{new_type}'")
                
                # Update record
                supabase.table('becas').update({'tipo_beca': new_type}).eq('id', atleta['id']).execute()
                updated_count += 1
            else:
                print(f"Saltando {atleta['nombre']} (Ya tiene tipo válido: {old_type})")

        print(f"\nMigración completada. {updated_count} registros actualizados.")

    except Exception as e:
        print(f"Error durante la migración: {e}")

if __name__ == "__main__":
    migrar_becas()
