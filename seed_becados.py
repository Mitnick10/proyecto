import os
import sys
import random
import time

# Add project directory to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'project'))

from config.supabase_client import supabase

def generate_cedula():
    return f"V-{random.randint(10000000, 35000000)}"

def generate_phone():
    prefixes = ['0412', '0414', '0424', '0416', '0426']
    return f"{random.choice(prefixes)}-{random.randint(1000000, 9999999)}"

nombres = ["Juan", "Pedro", "Maria", "Ana", "Luis", "Carlos", "Jose", "Laura", "Sofia", "Miguel", "Andrea", "Elena", "Diego", "David", "Gabriel", "Lucia", "Carmen", "Rosa", "Pablo", "Jesus"]
apellidos = ["Perez", "Garcia", "Rodriguez", "Gonzalez", "Hernandez", "Lopez", "Martinez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes", "Morales", "Castillo", "Jimenez", "Chavez", "Mendoza"]

disciplinas = ['Atletismo', 'Baloncesto', 'Béisbol', 'Boxeo', 'Ciclismo', 'Fútbol', 
               'Gimnasia', 'Natación', 'Taekwondo', 'Tenis de Campo', 'Tenis de Mesa', 'Voleibol']

tipos_beca = [
    "Esperanza Olímpica Guariqueña",
    "Elite Internacional",
    "Proyección a Selección Nacional",
    "Elite Nacional",
    "Talento Deportivo Guariqueño"
]

municipios = ["Juan Germán Roscio", "Francisco de Miranda", "Leonardo Infante", "José Tadeo Monagas", "Mellado"]

def seed_data(total_records=500):
    print(f"Iniciando generación de {total_records} becados...")
    
    batch_size = 50
    records = []
    
    for i in range(total_records):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        
        record = {
            'nombre': nombre,
            'apellido': apellido,
            'cedula': generate_cedula(),
            'edad': random.randint(12, 30),
            'sexo': random.choice(['M', 'F']),
            'email': f"{nombre.lower()}.{apellido.lower()}.{random.randint(1,999)}@example.com",
            'telefono': generate_phone(),
            'estatus': 'Activo',
            'cuenta_bancaria': '0102' + str(random.randint(1000000000000000, 9999999999999999)),
            # Datos Deportivos
            'disciplina': random.choice(disciplinas),
            'tipo_beca': random.choice(tipos_beca),
            'categoria': random.choice(['Juvenil', 'Adulto', 'Infantil']),
            'especialidad': 'General',
            # Ubicación
            'municipio': random.choice(municipios),
            'direccion': 'Dirección de prueba generada automáticamente',
            # Otros
            'es_menor': random.choice([True, False]),
            'created_at': 'now()' # Let Supabase handle timestamp or send string
        }
        records.append(record)
        
        if len(records) >= batch_size:
            try:
                # Insertar lote
                supabase.table('becas').insert(records).execute()
                print(f"Insertados {i+1}/{total_records} registros.")
            except Exception as e:
                print(f"Error insertando lote: {e}")
            finally:
                records = []
                time.sleep(0.5) # Breve pausa para no saturar

    # Insertar remanente
    if records:
        try:
            supabase.table('becas').insert(records).execute()
            print(f"Insertados registros finales. Total: {total_records}")
        except Exception as e:
            print(f"Error insertando lote final: {e}")

if __name__ == "__main__":
    seed_data(500)
