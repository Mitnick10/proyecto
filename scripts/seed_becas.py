import os
import sys
import random
from faker import Faker
from dotenv import load_dotenv

# Añadir el directorio raíz al path para poder importar config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project.config.supabase_client import supabase

# Cargar variables de entorno
load_dotenv()

fake = Faker('es_ES')  # Usar locale en español

DISCIPLINAS = [
    'Futbol', 'Baloncesto', 'Voleibol', 'Beisbol', 'Natacion', 
    'Atletismo', 'Karate', 'Judo', 'Taekwondo', 'Ajedrez', 
    'Tenis', 'Ciclismo', 'Boxeo', 'Pesas'
]

ESTATUS = ['Activo', 'Inactivo', 'En Revisión']

def generar_atleta():
    sexo = random.choice(['M', 'F'])
    nombre = fake.first_name_male() if sexo == 'M' else fake.first_name_female()
    apellido = fake.last_name()
    
    return {
        'nombre': nombre,
        'apellido': apellido,
        'cedula': str(fake.unique.random_number(digits=8)),
        'edad': random.randint(12, 25),
        'sexo': sexo,
        'email': fake.email(),
        'telefono': fake.phone_number(),
        'estatus': random.choice(ESTATUS),
        'cuenta_bancaria': str(fake.random_number(digits=20, fix_len=True)),
        'es_menor': random.choice([True, False]),
        'municipio': fake.city(),
        'direccion': fake.address(),
        'fecha_nacimiento': fake.date_of_birth(minimum_age=12, maximum_age=25).isoformat(),
        'disciplina': random.choice(DISCIPLINAS),
        'especialidad': 'General',
        'categoria': random.choice(['Juvenil', 'Infantil', 'Adulto']),
        'tipo_beca': random.choice(['Excelencia', 'Talento', 'Desarrollo']),
        'sangre': random.choice(['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']),
        'peso': f"{random.randint(45, 90)} kg",
        'estatura': f"{random.randint(150, 195)} cm",
        # Tallas
        'talla_zapato': str(random.randint(35, 45)),
        'talla_franela': random.choice(['S', 'M', 'L', 'XL']),
        'talla_short': random.choice(['S', 'M', 'L', 'XL']),
        'talla_chemise': random.choice(['S', 'M', 'L', 'XL']),
        'talla_mono': random.choice(['S', 'M', 'L', 'XL']),
        'talla_competencia': random.choice(['S', 'M', 'L', 'XL']),
        # Info Médica
        'usa_lentes': random.choice(['Si', 'No']),
        'usa_bucal': random.choice(['Si', 'No']),
        'usa_munequera': random.choice(['Si', 'No']),
        'usa_rodilleras': random.choice(['Si', 'No']),
        'dieta_deportiva': random.choice(['Si', 'No']),
        'control_medico': random.choice(['Si', 'No']),
        'estudio_social': random.choice(['Si', 'No']),
    }

def seed_becas(cantidad=100):
    print(f"Generando {cantidad} atletas...")
    
    lote = []
    for i in range(cantidad):
        atleta = generar_atleta()
        lote.append(atleta)
        
        # Insertar en lotes de 10 para no saturar
        if len(lote) >= 10:
            try:
                supabase.table('becas').insert(lote).execute()
                print(f"Insertados {i+1}/{cantidad}")
                lote = []
            except Exception as e:
                print(f"Error insertando lote: {e}")
                lote = [] # Limpiar para intentar seguir
    
    # Insertar el resto
    if lote:
        try:
            supabase.table('becas').insert(lote).execute()
            print(f"Insertados {cantidad}/{cantidad}")
        except Exception as e:
            print(f"Error insertando lote final: {e}")

    print("¡Proceso finalizado!")

if __name__ == '__main__':
    seed_becas()
