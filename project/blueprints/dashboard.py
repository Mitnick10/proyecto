import base64
import os
import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from urllib.parse import urlparse, unquote
import re
from config.supabase_client import supabase, supabase_admin
from utils.decorators import login_required, superadmin_required
from utils.file_handler import procesar_imagen, procesar_pdf
from utils.excel_generator import generar_ficha_excel

logger = logging.getLogger(__name__)

# Caché simple para contadores
cache_contadores = {
    'data': None,
    'timestamp': None,
    'ttl': 60
}

# Caché para disciplinas (TTL más largo porque cambian menos frecuentemente)
cache_disciplinas = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutos
}

# Definimos el Blueprint
dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='templates')

# --- HELPER PARA OBTENER DISCIPLINAS CON CACHÉ ---
def obtener_disciplinas_disponibles():
    """Obtiene la lista de disciplinas con caché para mejor rendimiento."""
    now = datetime.now()
    cache_valido = (
        cache_disciplinas['data'] is not None and 
        cache_disciplinas['timestamp'] is not None and
        (now - cache_disciplinas['timestamp']).total_seconds() < cache_disciplinas['ttl']
    )
    
    if cache_valido:
        return cache_disciplinas['data']
    
    try:
        # Disciplinas predeterminadas
        disciplinas_base = ['Atletismo', 'Baloncesto', 'Béisbol', 'Boxeo', 'Ciclismo', 'Fútbol',
                           'Gimnasia', 'Natación', 'Taekwondo', 'Tenis de Campo', 'Tenis de Mesa', 'Voleibol']
        
        # Obtener disciplinas personalizadas de la BD (las que no están en la lista base)
        try:
            all_disciplinas = supabase.table('becas').select('disciplina').limit(500).execute()
            disciplinas_bd = sorted(list(set(d['disciplina'] for d in all_disciplinas.data if d.get('disciplina') and d['disciplina'] not in disciplinas_base)))
        except:
            disciplinas_bd = []
        
        # Combinar: base + personalizadas
        disciplinas_completas = sorted(disciplinas_base) + disciplinas_bd
        
        # Actualizar caché
        cache_disciplinas['data'] = disciplinas_completas
        cache_disciplinas['timestamp'] = now
        
        return disciplinas_completas
    except Exception as e:
        logger.error(f"Error obteniendo disciplinas: {e}")
        # Fallback a lista básica
        return ['Atletismo', 'Baloncesto', 'Béisbol', 'Boxeo', 'Ciclismo', 'Fútbol', 'Gimnasia', 'Natación', 'Taekwondo', 'Tenis de Campo', 'Tenis de Mesa', 'Voleibol']

# --- HELPER PARA RECOLECTAR DATOS DEL FORMULARIO ---
def obtener_datos_formulario(req):
    """Extrae todos los campos del formulario para crear o editar."""
    # Usamos .get() para evitar errores si el campo no existe en el form
    datos = {
        # Datos Básicos
        'nombre': req.form.get('nombre'),
        'apellido': req.form.get('apellido'),
        'cedula': req.form.get('cedula'),
        'edad': req.form.get('edad') or None, # Convertir vacíos a None para enteros
        'sexo': req.form.get('sexo'),
        'email': req.form.get('email'),
        'telefono': req.form.get('telefono'),
        'estatus': req.form.get('estatus'),
        'cuenta_bancaria': req.form.get('cuenta_bancaria'),
        
        # Datos del Representante
        'es_menor': True if req.form.get('es_menor') == 'on' else False,
        'representante_nombre': req.form.get('representante_nombre'),
        'representante_cedula': req.form.get('representante_cedula'),
        'representante_telefono': req.form.get('representante_telefono'),
        'representante_parentesco': req.form.get('representante_parentesco'),
        
        # Ubicación
        'municipio': req.form.get('municipio'),
        'lugar_nacimiento': req.form.get('lugar_nacimiento'),
        'direccion': req.form.get('direccion'),
        'fecha_nacimiento': req.form.get('fecha_nacimiento') or None,

        # Datos Deportivos
        'disciplina': req.form.get('disciplina'),
        'especialidad': req.form.get('especialidad'),
        'categoria': req.form.get('categoria'),
        'tipo_beca': req.form.get('tipo_beca'),

        # Antropometría
        'sangre': req.form.get('sangre'),
        'peso': req.form.get('peso'),
        'estatura': req.form.get('estatura'),

        # Tallas
        'talla_zapato': req.form.get('talla_zapato'),
        'talla_franela': req.form.get('talla_franela'),
        'talla_short': req.form.get('talla_short'),
        'talla_chemise': req.form.get('talla_chemise'),
        'talla_mono': req.form.get('talla_mono'),
        'talla_competencia': req.form.get('talla_competencia'),

        # Información Médica y Otros (Selects Si/No)
        'usa_lentes': req.form.get('usa_lentes'),
        'usa_bucal': req.form.get('usa_bucal'),
        'usa_munequera': req.form.get('usa_munequera'),
        'usa_rodilleras': req.form.get('usa_rodilleras'),
        'dieta_deportiva': req.form.get('dieta_deportiva'),
        'control_medico': req.form.get('control_medico'),
        'estudio_social': req.form.get('estudio_social'),
    }
    return datos

def get_signed_url_for_doc(doc_url):
    """Genera una URL firmada válida por 1 hora para un documento."""
    try:
        if not doc_url: return doc_url
        
        # Normalizar URL y quitar query params si existen
        decoded_url = unquote(doc_url).split('?')[0]
        
        # Regex para extraer bucket y path
        # Soporta: .../object/public/<bucket>/<filepath>
        match = re.search(r'/object/public/([^/]+)/(.*)', decoded_url)
        
        if match:
            bucket_name = match.group(1)
            file_path = match.group(2)

            print(f"DEBUG SIGN: Bucket detected: '{bucket_name}', Path: '{file_path}'")
            
            # Generar Signed URL
            res = supabase_admin.storage.from_(bucket_name).create_signed_url(file_path, 3600)
            
            signed_url = None
            if isinstance(res, dict):
                 signed_url = res.get('signedURL')
            elif hasattr(res, 'signedURL'):
                 signed_url = res.signedURL
            elif isinstance(res, str):
                 signed_url = res
            
            if signed_url:
                return signed_url
            else:
                 logger.error(f"Error signing URL: {res}")
                 return doc_url
        else:
            # Fallback para URLs que no siguen el patrón standard de Supabase
            # o si es un bucket privado con otra estructura
            return doc_url
            
    except Exception as e:
        logger.warning(f"Error generanda signed URL para {doc_url}: {e}")
        return doc_url

# --- CONTEXT PROCESSOR ---
@dashboard_blueprint.context_processor
def inject_role():
    """Inyecta el rol del usuario en todas las plantillas."""
    return dict(user_role=session.get('role', 'usuario'))

# --- RUTA HOME (INICIO) CON CACHÉ ---
@dashboard_blueprint.route('/')
@login_required
def index():
    """Página de INICIO (Home) con contadores optimizados."""
    try:
        user = supabase.auth.get_user().user
        first_name = user.user_metadata.get('first_name', 'Usuario')

        # Verificar si el caché es válido
        now = datetime.now()
        cache_valido = (
            cache_contadores['data'] is not None and 
            cache_contadores['timestamp'] is not None and
            (now - cache_contadores['timestamp']).total_seconds() < cache_contadores['ttl']
        )
        
        if cache_valido:
            contadores = cache_contadores['data']
        else:
            atletas = supabase.table('becas').select('id', count='exact').eq('estatus', 'Activo').execute().count or 0
            revision = supabase.table('becas').select('id', count='exact').eq('estatus', 'En Revisión').execute().count or 0
            try:
                medallas = supabase.table('medallas').select('id', count='exact').execute().count or 0
            except: 
                medallas = 0
            
            contadores = {'atletas': atletas, 'revision': revision, 'medallas': medallas}
            cache_contadores['data'] = contadores
            cache_contadores['timestamp'] = now
        
        # Cargar imágenes independientes para el carrusel (Slots: home_1 a home_6)
        carousel_photos = []
        try:
            gallery_data = supabase.table('gallery_images').select('*').execute()
            # Crear un mapa para acceso rápido
            slots_map = {img['slot']: img['image_data'] for img in gallery_data.data if img['slot'].startswith('home_')}
            
            for i in range(1, 13):
                slot_id = f'home_{i}'
                url = slots_map.get(slot_id)
                carousel_photos.append({
                    'slot': slot_id,
                    'url': url,
                    'nombre': f'Imagen {i}'
                })
        except Exception as e:
            logger.warning(f"Error cargando fotos de galería: {e}")

        # Separar slots con imagen de los vacíos
        con_imagen = [p for p in carousel_photos if p.get('url')]
        sin_imagen = [p for p in carousel_photos if not p.get('url')]
        
        # Mezclar ambos grupos independientementes
        random.shuffle(con_imagen)
        random.shuffle(sin_imagen)
        
        # Priorizar los que tienen imagen y completar hasta llegar a 6
        final_photos = (con_imagen + sin_imagen)[:6]

        return render_template('dashboard_home.html', 
                               first_name=first_name, 
                               atletas_count=contadores['atletas'], 
                               revision_count=contadores['revision'], 
                               medallas_count=contadores['medallas'],
                               carousel_photos=final_photos)
    except Exception as e:
        logger.error(f"Error cargando dashboard: {e}", exc_info=True)
        session.clear()
        return redirect(url_for('auth.login'))

# --- RUTA LISTADO DE ATLETAS ---
@dashboard_blueprint.route('/becas')
@login_required
def lista_becas():
    """Lista de becas con filtro por disciplina, búsqueda por nombre y paginación."""
    filtro = request.args.get('disciplina')
    busqueda = request.args.get('buscar', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        query = supabase.table('becas').select('*', count='exact')
        
        # Filtrar por disciplina
        if filtro and filtro != 'Todas':
            query = query.eq('disciplina', filtro)
        
        # Búsqueda por nombre o apellido (case-insensitive)
        if busqueda:
            query = query.or_(f"nombre.ilike.%{busqueda}%,apellido.ilike.%{busqueda}%")
        
        result = query.order('id', desc=True).range(start, end).execute()
        becas = result.data
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # Usar disciplinas cacheadas en lugar de consulta directa
        lista_d = obtener_disciplinas_disponibles()
        
        # Cargar imágenes de galería para los laterales (hasta 6 slots por lado)
        gallery_images = {'left': [], 'right': []}
        try:
            gallery_data = supabase.table('gallery_images').select('*').execute()
            slots_map = {img['slot']: img['image_data'] for img in gallery_data.data}
            
            # Preparar pools de hasta 6 slots
            left_pool = []
            right_pool = []
            for i in range(1, 7):
                l_slot = f'left_{i}'
                r_slot = f'right_{i}'
                left_pool.append({'slot': l_slot, 'url': slots_map.get(l_slot)})
                right_pool.append({'slot': r_slot, 'url': slots_map.get(r_slot)})
            
            # Separar con imagen de vacíos para priorizar
            con_img_l = [p for p in left_pool if p['url']]
            sin_img_l = [p for p in left_pool if not p['url']]
            con_img_r = [p for p in right_pool if p['url']]
            sin_img_r = [p for p in right_pool if not p['url']]
            
            random.shuffle(con_img_l)
            random.shuffle(sin_img_l)
            random.shuffle(con_img_r)
            random.shuffle(sin_img_r)
            
            # Tomar los primeros 3 de cada lado
            gallery_images['left'] = (con_img_l + sin_img_l)[:3]
            gallery_images['right'] = (con_img_r + sin_img_r)[:3]
            
        except Exception as e:
            logger.warning(f"Error cargando fotos laterales: {e}")
            gallery_images = {'left': [{'slot': f'left_{i}', 'url': None} for i in range(1, 4)], 
                              'right': [{'slot': f'right_{i}', 'url': None} for i in range(1, 4)]}
        
        return render_template('dashboard_becas.html', 
                             becas=becas, 
                             disciplinas=lista_d, 
                             current_filter=filtro,
                             current_search=busqueda,
                             gallery_images=gallery_images,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    except Exception as e:
        logger.error(f"Error al cargar listado: {e}", exc_info=True)
        flash(f'Error al cargar listado: {e}', 'error')
        return render_template('dashboard_becas.html', becas=[], disciplinas=[], page=1, total_pages=1, total=0, current_search='', gallery_images={})

# --- RUTA MI CUENTA ---
@dashboard_blueprint.route('/cuenta', methods=['GET', 'POST'])
@login_required
def mi_cuenta():
    """Gestionar perfil y contraseña."""
    try:
        user = supabase.auth.get_user().user
        if request.method == 'POST':
            # Actualizar Datos Personales
            if 'update_info' in request.form:
                fname = request.form.get('first_name')
                lname = request.form.get('last_name')
                supabase.auth.update_user({"data": {"first_name": fname, "last_name": lname, "full_name": f"{fname} {lname}"}})
                flash('Datos actualizados.', 'success')
            
            # Cambiar Contraseña
            elif 'update_password' in request.form:
                pwd = request.form.get('password')
                if len(pwd) < 6:
                    flash('La contraseña es muy corta.', 'error')
                else:
                    supabase.auth.update_user({"password": pwd})
                    flash('Contraseña actualizada.', 'success')
            return redirect(url_for('dashboard.mi_cuenta'))

        return render_template('dashboard_cuenta.html', first_name=user.user_metadata.get('first_name'), last_name=user.user_metadata.get('last_name'), email=user.email)
    except: return redirect(url_for('dashboard.index'))


# --- GESTIÓN DE ATLETAS (CRUD) ---

@dashboard_blueprint.route('/becas/nueva', methods=['GET', 'POST'])
@login_required
def crear_beca():
    print("="*50)
    print("DEBUG: CREAR_BECA INICIADO")
    print(f"DEBUG: Método: {request.method}")
    
    if request.method == 'POST':
        try:
            print("DEBUG: Procesando POST")
            print(f"DEBUG: request.files: {request.files}")
            print(f"DEBUG: request.form keys: {request.form.keys()}")
            
            # 1. Recolectar todos los datos del formulario usando el helper
            datos = obtener_datos_formulario(request)
            print(f"DEBUG: Datos recolectados: {list(datos.keys())}")
            
            # 2. Procesar Foto
            file = request.files.get('foto')
            print(f"DEBUG CREAR: Archivo recibido: {file}")
            if file:
                print(f"DEBUG CREAR: Filename: {file.filename}")
                print(f"DEBUG CREAR: Content-Type: {file.content_type}")
            
            foto_url = procesar_imagen(file)
            print(f"DEBUG CREAR: Resultado procesar_imagen: {foto_url[:100] if foto_url else 'None'}...")
            
            if foto_url:
                datos['foto'] = foto_url
                print(f"DEBUG: Foto URL: {foto_url}")
            
            # 3. Insertar en BD
            print("DEBUG: Intentando insertar en BD...")
            result = supabase.table('becas').insert(datos).execute()
            print(f"DEBUG: Insert exitoso, data: {result.data}")
            
            # Invalidar caché de disciplinas si se agregó una nueva
            cache_disciplinas['data'] = None
            cache_disciplinas['timestamp'] = None
            
            flash('Atleta registrado exitosamente.', 'success')
            return redirect(url_for('dashboard.lista_becas'))
        except Exception as e: 
            print(f"ERROR en crear_beca: {e}")
            import traceback
            traceback.print_exc()
            flash(f'Error al registrar: {e}', 'error')
    
    # GET - Cargar disciplinas disponibles usando caché
    disciplinas_completas = obtener_disciplinas_disponibles()
    return render_template('crear_beca.html', disciplinas_list=disciplinas_completas)

@dashboard_blueprint.route('/becas/ver/<int:beca_id>')
@login_required
def ver_beca(beca_id):
    """Ver ficha técnica y medallas (Solo lectura)."""
    try:
        # Cargar Atleta
        beca = supabase.table('becas').select('*').eq('id', beca_id).single().execute().data
        
        if not beca:
            flash('Atleta no encontrado.', 'error')
            return redirect(url_for('dashboard.lista_becas'))

        # Cargar Medallas
        try:
            medallas = supabase.table('medallas').select('*').eq('atleta_id', beca_id).order('created_at', desc=True).execute().data
        except: medallas = [] # Si falla (ej. tabla no existe), lista vacía

        # Cargar Documentos (opcional para ver ficha)
        try:
            documentos = supabase.table('documentos').select('*').eq('atleta_id', beca_id).execute().data
            # Firmar URLs
            for doc in documentos:
                doc['archivo'] = get_signed_url_for_doc(doc['archivo'])
        except: documentos = []

        return render_template('ver_beca.html', beca=beca, medallas=medallas, documentos=documentos)
    except Exception as e: 
        flash(f'Error al cargar ficha: {e}', 'error')
        return redirect(url_for('dashboard.lista_becas'))

@dashboard_blueprint.route('/becas/descargar/<int:beca_id>')
@login_required
def descargar_ficha(beca_id):
    try:
        # 1. Obtener datos del atleta
        beca = supabase.table('becas').select('*').eq('id', beca_id).single().execute().data
        if not beca:
            flash('Atleta no encontrado.', 'error')
            return redirect(url_for('dashboard.lista_becas'))

        # 2. Generar Excel usando el utility
        output = generar_ficha_excel(beca)

        filename = f"Ficha_{beca.get('nombre','').replace(' ','_')}_{beca.get('apellido','').replace(' ','_')}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error al generar ficha: {e}', 'error')
        return redirect(url_for('dashboard.ver_beca', beca_id=beca_id))

@dashboard_blueprint.route('/becas/editar/<int:beca_id>', methods=['GET', 'POST'])
@login_required
def editar_beca(beca_id):
    """Editar datos y gestionar medallas."""
    
    # 1. Guardar cambios del atleta (POST)
    if request.method == 'POST':
        try:
            # Recolectar datos actualizados
            datos = obtener_datos_formulario(request)
            
            # Procesar Foto Nueva (si se subió una)
            file = request.files.get('foto')
            print(f"DEBUG EDITAR: Archivo recibido: {file}")
            if file:
                print(f"DEBUG EDITAR: Filename: {file.filename}")
                print(f"DEBUG EDITAR: Content-Type: {file.content_type if hasattr(file, 'content_type') else 'N/A'}")
            
            foto_url = procesar_imagen(file)
            print(f"DEBUG EDITAR: Resultado procesar_imagen: {foto_url[:100] if foto_url else 'None'}")
            
            if foto_url:
                datos['foto'] = foto_url
                print(f"DEBUG EDITAR: Foto agregada a datos para update. URL: {foto_url}")
            else:
                print("DEBUG EDITAR: No se procesó ninguna foto nueva")
            
            supabase.table('becas').update(datos).eq('id', beca_id).execute()
            
            # Invalidar caché de disciplinas si se pudo haber cambiado
            cache_disciplinas['data'] = None
            cache_disciplinas['timestamp'] = None
            
            flash('Ficha actualizada correctamente.', 'success')
            return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))
        except Exception as e: 
            flash(f'Error al guardar cambios: {e}', 'error')

    # 2. MOSTRAR (GET)
    try:
        beca = supabase.table('becas').select('*').eq('id', beca_id).single().execute().data
        
        # Cargar medallas
        try:
            medallas = supabase.table('medallas').select('*').eq('atleta_id', beca_id).order('created_at', desc=True).execute().data
        except: medallas = []

        # Cargar documentos
        try:
            documentos = supabase.table('documentos').select('*').eq('atleta_id', beca_id).order('created_at', desc=True).execute().data
            # Firmar URLs
            for doc in documentos:
                doc['archivo'] = get_signed_url_for_doc(doc['archivo'])
        except: documentos = []
        
        # Galería: usar la foto principal del atleta
        galeria_fotos = []
        if beca.get('foto'):
            galeria_fotos = [{'id': 0, 'url': beca['foto'], 'atleta_id': beca_id}]
        
        # Cargar disciplinas disponibles usando caché
        disciplinas_completas = obtener_disciplinas_disponibles()
        
        return render_template('editar_beca.html', beca=beca, medallas=medallas, documentos=documentos, galeria_fotos=galeria_fotos, disciplinas_list=disciplinas_completas)
    except: return redirect(url_for('dashboard.lista_becas'))

@dashboard_blueprint.route('/becas/eliminar/<int:beca_id>', methods=['POST'])
@login_required
def eliminar_beca(beca_id):
    try:
        supabase.table('becas').delete().eq('id', beca_id).execute()
        flash('Atleta eliminado.', 'success')
    except Exception as e: flash(f'Error: {e}', 'error')
    return redirect(url_for('dashboard.lista_becas'))

# --- GESTIÓN DE MEDALLAS (Rutas Auxiliares) ---

@dashboard_blueprint.route('/becas/<int:beca_id>/agregar_medalla', methods=['POST'])
@login_required
def agregar_medalla(beca_id):
    try:
        supabase.table('medallas').insert({
            'atleta_id': beca_id,
            'tipo_medalla': request.form.get('tipo_medalla'),
            'competicion': request.form.get('competicion'),
            'fecha': request.form.get('fecha') or None
        }).execute()
        flash('Medalla agregada.', 'success')
    except Exception as e: flash(f'Error al agregar medalla: {e}', 'error')
    # Volver a la misma página de edición
    return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))

@dashboard_blueprint.route('/medallas/eliminar/<int:medalla_id>', methods=['POST'])
@login_required
def eliminar_medalla(medalla_id):
    atleta_id = request.form.get('atleta_id') # Necesario para saber a dónde volver
    try:
        supabase.table('medallas').delete().eq('id', medalla_id).execute()
        flash('Medalla eliminada.', 'success')
    except: flash('Error al eliminar.', 'error')
    return redirect(url_for('dashboard.editar_beca', beca_id=atleta_id))

# --- GESTIÓN DE DOCUMENTOS (Rutas Auxiliares) ---

@dashboard_blueprint.route('/becas/<int:beca_id>/subir_documento', methods=['POST'])
@login_required
def subir_documento(beca_id):
    try:
        archivo = request.files.get('archivo_pdf')
        nombre_doc = request.form.get('nombre_doc')
        
        if not archivo or not nombre_doc:
            flash('Debes seleccionar un archivo y un nombre.', 'error')
        else:
            doc_url = procesar_pdf(archivo)
            if doc_url:
                supabase.table('documentos').insert({
                    'atleta_id': beca_id,
                    'nombre': nombre_doc,
                    'archivo': doc_url
                }).execute()
                flash('Documento subido correctamente.', 'success')
            else:
                flash('Error al procesar el archivo PDF.', 'error')
    except Exception as e: 
        flash(f'Error al subir: {e}', 'error')
    
    return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))

@dashboard_blueprint.route('/documentos/eliminar/<int:doc_id>', methods=['POST'])
@login_required
def eliminar_documento(doc_id):
    atleta_id = request.form.get('atleta_id')
    try:
        supabase.table('documentos').delete().eq('id', doc_id).execute()
        flash('Documento eliminado.', 'success')
    except: flash('Error al eliminar.', 'error')
    return redirect(url_for('dashboard.editar_beca', beca_id=atleta_id))


# --- GESTIÓN DE USUARIOS (SOLO SUPERADMIN) ---

@dashboard_blueprint.route('/usuarios')
@login_required
@superadmin_required
def lista_usuarios():
    try:
        if not supabase_admin:
            flash('Error de configuración: Admin client no disponible.', 'error')
            return redirect(url_for('dashboard.index'))
            
        usuarios = supabase_admin.table('profiles').select('*').order('email').execute().data
        return render_template('dashboard_usuarios.html', usuarios=usuarios)
    except Exception as e:
        logger.error(f"Error cargando usuarios: {e}", exc_info=True)
        flash(f'Error al cargar usuarios: {e}', 'error')
        return redirect(url_for('dashboard.index'))

@dashboard_blueprint.route('/usuarios/cambiar_rol', methods=['POST'])
@login_required
@superadmin_required
def cambiar_rol():
    uid = request.form.get('user_id')
    role = request.form.get('new_role')
    try:
        if uid == session.get('user_id') and role != 'superadmin':
            flash('No puedes quitarte el rol de Superadmin a ti mismo.', 'error')
        else:
            if supabase_admin:
                supabase_admin.table('profiles').update({'role': role}).eq('id', uid).execute()
                flash('Rol actualizado.', 'success')
            else:
                flash('Error: Admin client no disponible.', 'error')
    except Exception as e:
        logger.error(f"Error cambiando rol: {e}")
        flash('Error al cambiar rol.', 'error')
    return redirect(url_for('dashboard.lista_usuarios'))

@dashboard_blueprint.route('/usuarios/eliminar', methods=['POST'])
@login_required
@superadmin_required
def eliminar_usuario():
    uid = request.form.get('user_id')
    try:
        if uid == session.get('user_id'):
            flash('No puedes eliminar tu propia cuenta.', 'error')
        else:
            # Nota: Esto solo elimina el perfil. Para eliminar el usuario de Auth se requiere Service Key y:
            # supabase.auth.admin.delete_user(uid)
            if supabase_admin:
                # Nota: Esto solo elimina el perfil. Para eliminar el usuario de Auth se requiere Service Key y:
                supabase_admin.auth.admin.delete_user(uid)
                supabase_admin.table('profiles').delete().eq('id', uid).execute()
                flash('Usuario eliminado permanentemente.', 'success')
            else:
                flash('Error: Admin client no disponible.', 'error')
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        flash(f'Error al eliminar usuario: {e}', 'error')
    return redirect(url_for('dashboard.lista_usuarios'))


# --- GESTIÓN DE GALERÍA DE IMÁGENES ---

@dashboard_blueprint.route('/gallery/upload', methods=['POST'])
@login_required
def upload_gallery_image():
    """Subir imagen para la galería del dashboard (Solo admins)."""
    from flask import jsonify
    
    # Verificar permisos
    role = session.get('role', 'usuario')
    if role not in ['admin', 'superadmin']:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        file = request.files.get('image')
        slot = request.form.get('slot')
        
        if not file or not slot:
            return jsonify({'error': 'Faltan datos'}), 400
        
        # Validar slot válido (becas laterales ilimitados, home dinámico)
        import re
        if not (slot.startswith('home_') or re.match(r'^(left|right)_\d+$', slot)):
            return jsonify({'error': 'Slot inválido'}), 400
        
        try:
            from io import BytesIO
            from PIL import Image
            from utils.file_handler import upload_file_to_supabase
            
            # 1. Procesar imagen (Opcional: Resizing/Format)
            file.seek(0)
            img = Image.open(file)
            
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Redimensionar para la web (800px max)
            img.thumbnail((800, 1000))
            
            # Guardar en buffer temporal
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # Crear un objeto "file-like" para el helper
            class FileLike:
                def __init__(self, content, filename, content_type):
                    self.content = content
                    self.filename = filename
                    self.content_type = content_type
                def read(self): return self.content
                def seek(self, pos): pass
            
            temp_file = FileLike(buffer.read(), file.filename, 'image/jpeg')
            
            # 2. Subir a Supabase Storage
            # Usamos el bucket 'becas-public' y folder 'gallery'
            public_url = upload_file_to_supabase(temp_file, 'becas-public', 'gallery')
            
            if not public_url:
                return jsonify({'error': 'Error al subir al storage'}), 500
            
            # 3. Upsert en la tabla gallery_images (usar slot como clave única)
            data = {
                'slot': slot,
                'image_data': public_url
            }
            
            # Upsert
            supabase.table('gallery_images').upsert(data, on_conflict='slot').execute()
            
            logger.info(f"Imagen de galería actualizada en Storage y DB: {slot} -> {public_url}")
            return jsonify({'success': True, 'message': 'Imagen actualizada', 'url': public_url}), 200
            
        except Exception as save_error:
            logger.error(f"Error procesando/guardando imagen de galería: {save_error}", exc_info=True)
            return jsonify({'error': f'Error procesando imagen: {str(save_error)}'}), 500
        
    except Exception as e:
        logger.error(f"Error subiendo imagen galería: {e}")
        return jsonify({'error': str(e)}), 500