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
from utils.pdf_generator import generar_listado_pdf
from utils.cache_helpers import get_cached_or_compute, invalidate_cache, create_cache
from utils.form_helpers import extract_athlete_data

logger = logging.getLogger(__name__)

# Caché simple para contadores (TTL: 60 segundos)
cache_contadores = create_cache(ttl=60)

# Caché para disciplinas (TTL más largo porque cambian menos frecuentemente)
cache_disciplinas = create_cache(ttl=300)  # 5 minutos

# Definimos el Blueprint
dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='templates')

# --- HELPER PARA OBTENER DISCIPLINAS CON CACHÉ ---
def obtener_disciplinas_disponibles():
    """Obtiene la lista de disciplinas con caché para mejor rendimiento."""
    
    def compute_disciplinas():
        """Función auxiliar que calcula las disciplinas."""
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
            return sorted(disciplinas_base) + disciplinas_bd
        except Exception as e:
            logger.error(f"Error obteniendo disciplinas: {e}")
            # Fallback a lista básica
            return ['Atletismo', 'Baloncesto', 'Béisbol', 'Boxeo', 'Ciclismo', 'Fútbol', 'Gimnasia', 'Natación', 'Taekwondo', 'Tenis de Campo', 'Tenis de Mesa', 'Voleibol']
    
    return get_cached_or_compute(cache_disciplinas, compute_disciplinas)


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

        # Usar helper de caché para obtener contadores
        def compute_contadores():
            atletas = supabase.table('becas').select('id', count='exact').eq('estatus', 'Activo').execute().count or 0
            revision = supabase.table('becas').select('id', count='exact').eq('estatus', 'En Revisión').execute().count or 0
            try:
                medallas = supabase.table('medallas').select('id', count='exact').execute().count or 0
            except: 
                medallas = 0
            
            return {'atletas': atletas, 'revision': revision, 'medallas': medallas}
        
        contadores = get_cached_or_compute(cache_contadores, compute_contadores)
        
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
        
        # Mezclar ambos grupos independientemente
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
    filtro_tipo = request.args.get('tipo_beca')
    busqueda = request.args.get('buscar', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        query = supabase.table('becas').select('*', count='exact').eq('estatus', 'Activo')
        
        # Filtrar por disciplina
        if filtro and filtro != 'Todas':
            query = query.eq('disciplina', filtro)
            
        # Filtrar por Tipo de Beca
        if filtro_tipo and filtro_tipo != 'Todas':
            query = query.eq('tipo_beca', filtro_tipo)
        
        # Búsqueda por nombre o apellido (case-insensitive)
        if busqueda:
            query = query.or_(f"nombre.ilike.%{busqueda}%,apellido.ilike.%{busqueda}%,cedula.ilike.%{busqueda}%")
        
        result = query.order('id', desc=True).range(start, end).execute()
        becas = result.data
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # Usar disciplinas cacheadas en lugar de consulta directa
        lista_d = obtener_disciplinas_disponibles()
        
        # Obtener lista de Tipos de Beca (Distinct)
        # Nota: Supabase no tiene un 'distinct' directo fácil en el cliente, traemos todos y filtramos en python
        # o usamos una RPC si fuera muy grande. Por ahora, fetch ligero de columna.
        try:
             tipos_raw = supabase.table('becas').select('tipo_beca').execute()
             tipos_beca = sorted(list(set(t['tipo_beca'] for t in tipos_raw.data if t.get('tipo_beca'))))
        except:
             tipos_beca = []

        
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
                             tipos_beca=tipos_beca,
                             current_filter=filtro,
                             current_tipo_beca=filtro_tipo,
                             current_search=busqueda,
                             gallery_images=gallery_images,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    except Exception as e:
        logger.error(f"Error al cargar listado: {e}", exc_info=True)
        flash(f'Error al cargar listado: {e}', 'error')
        return render_template('dashboard_becas.html', becas=[], disciplinas=[], page=1, total_pages=1, total=0, current_search='', gallery_images={})

@dashboard_blueprint.route('/becas/exportar_pdf')
@login_required
def exportar_pdf_becas():
    """Genera y descarga un PDF con el listado de atletas filtrado."""
    filtro = request.args.get('disciplina')
    filtro_tipo = request.args.get('tipo_beca')
    busqueda = request.args.get('buscar', '').strip()
    
    try:
        query = supabase.table('becas').select('*').eq('estatus', 'Activo')
        
        # Aplicar mismos filtros que en el listado
        if filtro and filtro != 'Todas':
            query = query.eq('disciplina', filtro)
            
        if filtro_tipo and filtro_tipo != 'Todas':
            query = query.eq('tipo_beca', filtro_tipo)
        
        if busqueda:
            query = query.or_(f"nombre.ilike.%{busqueda}%,apellido.ilike.%{busqueda}%,cedula.ilike.%{busqueda}%")
            
        # Ejecutar consulta (sin paginación para exportar todo)
        result = query.order('apellido', desc=False).execute()
        becas = result.data
        
        # Generar PDF
        pdf_buffer = generar_listado_pdf(becas)
        
        filename = f"Listado_Atletas_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exportando PDF: {e}", exc_info=True)
        flash(f'Error al generar PDF: {e}', 'error')
        return redirect(url_for('dashboard.lista_becas'))

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
    if request.method == 'POST':
        try:
            logger.debug(f"Procesando POST en crear_beca, method: {request.method}")
            
            # 1. Recolectar todos los datos del formulario usando el helper
            datos = extract_athlete_data(request)
            logger.debug(f"Datos extraídos: {list(datos.keys())}")
            
            # 2. Procesar Foto
            file = request.files.get('foto')
            if file and file.filename:
                logger.debug(f"Procesando archivo: {file.filename}, tipo: {file.content_type}")
                foto_url = procesar_imagen(file)
                if foto_url:
                    datos['foto'] = foto_url
                    logger.debug(f"Foto procesada exitosamente")
            
            # 3. Insertar en BD
            logger.debug("Insertando datos en BD...")
            result = supabase.table('becas').insert(datos).execute()
            logger.info(f"Atleta creado exitosamente, ID: {result.data[0].get('id') if result.data else 'N/A'}")
            
            # Invalidar caché de disciplinas si se agregó una nueva
            invalidate_cache(cache_disciplinas)
            
            flash('Atleta registrado exitosamente.', 'success')
            return redirect(url_for('dashboard.lista_becas'))
        except Exception as e:
            logger.error(f"Error en crear_beca: {e}", exc_info=True)
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
            datos = extract_athlete_data(request)
            
            # Procesar Foto Nueva (si se subió una)
            file = request.files.get('foto')
            if file and file.filename:
                logger.debug(f"Procesando nueva foto: {file.filename}")
                foto_url = procesar_imagen(file)
                if foto_url:
                    datos['foto'] = foto_url
                    logger.debug(f"Foto actualizada exitosamente")
            
            supabase.table('becas').update(datos).eq('id', beca_id).execute()
            logger.info(f"Ficha actualizada para atleta ID: {beca_id}")
            
            # Invalidar caché de disciplinas si se pudo haber cambiado
            invalidate_cache(cache_disciplinas)
            
            flash('Ficha actualizada correctamente.', 'success')
            return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))
        except Exception as e:
            logger.error(f"Error al guardar cambios en atleta {beca_id}: {e}", exc_info=True)
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