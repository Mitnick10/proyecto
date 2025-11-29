import base64
import logging
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config.supabase_client import supabase
from utils.decorators import login_required, superadmin_required
from utils.validaciones import validar_datos_atleta, sanitizar_input

# Configurar logger
logger = logging.getLogger(__name__)

# Caché simple para contadores (evita consultas repetidas)
cache_contadores = {
    'data': None,
    'timestamp': None,
    'ttl': 60  # 60 segundos de vida
}

# Definimos el Blueprint
dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='templates')

# --- HELPER PARA SUBIR ARCHIVOS A SUPABASE STORAGE ---
def upload_file(file, bucket, folder=""):
    """Sube un archivo a Supabase Storage y retorna la URL pública."""
    if not file or not file.filename:
        return None
    try:
        # Leer el contenido del archivo
        file_content = file.read()
        
        # Generar un nombre único para evitar colisiones
        ext = file.filename.split('.')[-1]
        filename = f"{folder}/{uuid.uuid4()}.{ext}" if folder else f"{uuid.uuid4()}.{ext}"
        
        # Subir el archivo
        mime_type = file.content_type or 'application/octet-stream'
        supabase.storage.from_(bucket).upload(
            path=filename,
            file=file_content,
            file_options={"content-type": mime_type}
        )
        
        # Obtener la URL pública
        public_url = supabase.storage.from_(bucket).get_public_url(filename)
        return public_url
    except Exception as e:
        logger.error(f"Error subiendo archivo a {bucket}: {e}")
        return None

def procesar_imagen(file):
    """Wrapper para subir imágenes al bucket 'avatars'."""
    return upload_file(file, 'avatars')

def procesar_pdf(file):
    """Wrapper para subir documentos al bucket 'documentos'."""
    return upload_file(file, 'documentos')

# --- HELPER PARA RECOLECTAR DATOS DEL FORMULARIO ---
def obtener_datos_formulario(req):
    """Extrae todos los campos del formulario para crear o editar."""
    datos = {
        'nombre': sanitizar_input(req.form.get('nombre')),
        'apellido': sanitizar_input(req.form.get('apellido')),
        'cedula': req.form.get('cedula'),
        'edad': req.form.get('edad') or None,
        'sexo': req.form.get('sexo'),
        'email': req.form.get('email'),
        'telefono': req.form.get('telefono'),
        'estatus': req.form.get('estatus'),
        'cuenta_bancaria': req.form.get('cuenta_bancaria'),
        'es_menor': True if req.form.get('es_menor') == 'on' else False,
        'representante_nombre': sanitizar_input(req.form.get('representante_nombre')),
        'representante_cedula': req.form.get('representante_cedula'),
        'representante_parentesco': sanitizar_input(req.form.get('representante_parentesco')),
        'municipio': sanitizar_input(req.form.get('municipio')),
        'lugar_nacimiento': sanitizar_input(req.form.get('lugar_nacimiento')),
        'direccion': sanitizar_input(req.form.get('direccion')),
        'fecha_nacimiento': req.form.get('fecha_nacimiento') or None,
        'disciplina': req.form.get('disciplina'),
        'especialidad': sanitizar_input(req.form.get('especialidad')),
        'categoria': req.form.get('categoria'),
        'tipo_beca': req.form.get('tipo_beca'),
        'sangre': req.form.get('sangre'),
        'peso': req.form.get('peso'),
        'estatura': req.form.get('estatura'),
        'talla_zapato': req.form.get('talla_zapato'),
        'talla_franela': req.form.get('talla_franela'),
        'talla_short': req.form.get('talla_short'),
        'talla_chemise': req.form.get('talla_chemise'),
        'talla_mono': req.form.get('talla_mono'),
        'talla_competencia': req.form.get('talla_competencia'),
        'usa_lentes': req.form.get('usa_lentes'),
        'usa_bucal': req.form.get('usa_bucal'),
        'usa_munequera': req.form.get('usa_munequera'),
        'usa_rodilleras': req.form.get('usa_rodilleras'),
        'dieta_deportiva': req.form.get('dieta_deportiva'),
        'control_medico': req.form.get('control_medico'),
        'estudio_social': req.form.get('estudio_social'),
    }
    return datos

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
        
        return render_template('dashboard_home.html', 
                               first_name=first_name, 
                               atletas_count=contadores['atletas'], 
                               revision_count=contadores['revision'], 
                               medallas_count=contadores['medallas'])
    except Exception as e:
        logger.error(f"Error cargando dashboard: {e}", exc_info=True)
        session.clear()
        return redirect(url_for('auth.login'))

# --- RUTA LISTADO DE ATLETAS CON PAGINACIÓN ---
@dashboard_blueprint.route('/becas')
@login_required
def lista_becas():
    """Lista de becas con filtro por disciplina y paginación."""
    filtro = request.args.get('disciplina')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    try:
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        query = supabase.table('becas').select('*', count='exact')
        if filtro and filtro != 'Todas':
            query = query.eq('disciplina', filtro)
        
        result = query.order('id', desc=True).range(start, end).execute()
        becas = result.data
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        all_d = supabase.table('becas').select('disciplina').limit(1000).execute()
        lista_d = sorted(list(set(i['disciplina'] for i in all_d.data if i.get('disciplina'))))
        
        return render_template('dashboard_becas.html', 
                             becas=becas, 
                             disciplinas=lista_d, 
                             current_filter=filtro,
                             page=page,
                             total_pages=total_pages,
                             total=total)
    except Exception as e:
        logger.error(f"Error al cargar listado: {e}", exc_info=True)
        flash(f'Error al cargar listado: {e}', 'error')
        return render_template('dashboard_becas.html', becas=[], disciplinas=[], page=1, total_pages=1, total=0)

# --- RUTA MI CUENTA ---
@dashboard_blueprint.route('/cuenta', methods=['GET', 'POST'])
@login_required
def mi_cuenta():
    """Gestionar perfil y contraseña."""
    try:
        user = supabase.auth.get_user().user
        if request.method == 'POST':
            if 'update_info' in request.form:
                fname = sanitizar_input(request.form.get('first_name'))
                lname = sanitizar_input(request.form.get('last_name'))
                supabase.auth.update_user({"data": {"first_name": fname, "last_name": lname, "full_name": f"{fname} {lname}"}})
                flash('Datos actualizados.', 'success')
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
            datos = obtener_datos_formulario(request)
            es_valido, errores = validar_datos_atleta(datos)
            if not es_valido:
                for error in errores:
                    flash(error, 'error')
                return render_template('crear_beca.html')
            
            foto_b64 = procesar_imagen(request.files.get('foto'))
            if foto_b64:
                datos['foto'] = foto_b64
            
            supabase.table('becas').insert(datos).execute()
            cache_contadores['data'] = None  # Invalidar caché
            logger.info(f"Atleta registrado: {datos['nombre']} {datos['apellido']}")
            flash('Atleta registrado exitosamente.', 'success')
            return redirect(url_for('dashboard.lista_becas'))
        except Exception as e: 
            logger.error(f"Error crear_beca: {e}", exc_info=True)
            flash(f'Error al registrar: {e}', 'error')
    return render_template('crear_beca.html')

@dashboard_blueprint.route('/becas/ver/<int:beca_id>')
@login_required
def ver_beca(beca_id):
    try:
        beca = supabase.table('becas').select('*').eq('id', beca_id).single().execute().data
        if not beca:
            flash('Atleta no encontrado.', 'error')
            return redirect(url_for('dashboard.lista_becas'))
        try:
            medallas = supabase.table('medallas').select('*').eq('atleta_id', beca_id).order('created_at', desc=True).execute().data
        except: medallas = []
        try:
            documentos = supabase.table('documentos').select('*').eq('atleta_id', beca_id).execute().data
        except: documentos = []
        return render_template('ver_beca.html', beca=beca, medallas=medallas, documentos=documentos)
    except Exception as e: 
        logger.error(f"Error al cargar ficha: {e}", exc_info=True)
        flash(f'Error al cargar ficha: {e}', 'error')
        return redirect(url_for('dashboard.lista_becas'))

@dashboard_blueprint.route('/becas/editar/<int:beca_id>', methods=['GET', 'POST'])
@login_required
def editar_beca(beca_id):
    if request.method == 'POST':
        try:
            datos = obtener_datos_formulario(request)
            es_valido, errores = validar_datos_atleta(datos)
            if not es_valido:
                for error in errores:
                    flash(error, 'error')
                return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))
            
            foto_b64 = procesar_imagen(request.files.get('foto'))
            if foto_b64:
                datos['foto'] = foto_b64
            
            supabase.table('becas').update(datos).eq('id', beca_id).execute()
            cache_contadores['data'] = None  # Invalidar caché
            logger.info(f"Ficha actualizada: ID {beca_id}")
            flash('Ficha actualizada correctamente.', 'success')
            return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))
        except Exception as e: 
            logger.error(f"Error al guardar cambios: {e}", exc_info=True)
            flash(f'Error al guardar cambios: {e}', 'error')
    try:
        beca = supabase.table('becas').select('*').eq('id', beca_id).single().execute().data
        if not beca:
            flash('Atleta no encontrado.', 'error')
            return redirect(url_for('dashboard.lista_becas'))
        try:
            medallas = supabase.table('medallas').select('*').eq('atleta_id', beca_id).order('created_at', desc=True).execute().data
        except: medallas = []
        try:
            documentos = supabase.table('documentos').select('*').eq('atleta_id', beca_id).order('created_at', desc=True).execute().data
        except: documentos = []
        return render_template('editar_beca.html', beca=beca, medallas=medallas, documentos=documentos)
    except Exception as e:
        logger.error(f"Error al cargar ficha para editar: {e}", exc_info=True)
        flash(f'Error al cargar ficha: {e}', 'error')
        return redirect(url_for('dashboard.lista_becas'))

@dashboard_blueprint.route('/becas/eliminar/<int:beca_id>', methods=['POST'])
@login_required
def eliminar_beca(beca_id):
    try:
        supabase.table('becas').delete().eq('id', beca_id).execute()
        cache_contadores['data'] = None  # Invalidar caché
        logger.info(f"Atleta eliminado: ID {beca_id}")
        flash('Atleta eliminado.', 'success')
    except Exception as e: 
        logger.error(f"Error al eliminar: {e}", exc_info=True)
        flash(f'Error: {e}', 'error')
    return redirect(url_for('dashboard.lista_becas'))

# --- GESTIÓN DE MEDALLAS ---
@dashboard_blueprint.route('/becas/<int:beca_id>/agregar_medalla', methods=['POST'])
@login_required
def agregar_medalla(beca_id):
    try:
        supabase.table('medallas').insert({
            'atleta_id': beca_id,
            'tipo_medalla': request.form.get('tipo_medalla'),
            'competicion': sanitizar_input(request.form.get('competicion')),
            'fecha': request.form.get('fecha') or None
        }).execute()
        cache_contadores['data'] = None  # Invalidar caché
        logger.info(f"Medalla agregada al atleta ID {beca_id}")
        flash('Medalla agregada.', 'success')
    except Exception as e: 
        logger.error(f"Error al agregar medalla: {e}", exc_info=True)
        flash(f'Error al agregar medalla: {e}', 'error')
    return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))

@dashboard_blueprint.route('/medallas/eliminar/<int:medalla_id>', methods=['POST'])
@login_required
def eliminar_medalla(medalla_id):
    atleta_id = request.form.get('atleta_id')
    try:
        supabase.table('medallas').delete().eq('id', medalla_id).execute()
        cache_contadores['data'] = None  # Invalidar caché
        logger.info(f"Medalla eliminada: ID {medalla_id}")
        flash('Medalla eliminada.', 'success')
    except Exception as e:
        logger.error(f"Error al eliminar medalla: {e}", exc_info=True)
        flash('Error al eliminar.', 'error')
    return redirect(url_for('dashboard.editar_beca', beca_id=atleta_id))

# --- GESTIÓN DE DOCUMENTOS ---
@dashboard_blueprint.route('/becas/<int:beca_id>/subir_documento', methods=['POST'])
@login_required
def subir_documento(beca_id):
    try:
        archivo = request.files.get('archivo_pdf')
        nombre_doc = sanitizar_input(request.form.get('nombre_doc'))
        if not archivo or not nombre_doc:
            flash('Debes seleccionar un archivo y un nombre.', 'error')
        else:
            pdf_b64 = procesar_pdf(archivo)
            if pdf_b64:
                supabase.table('documentos').insert({
                    'atleta_id': beca_id,
                    'nombre': nombre_doc,
                    'archivo': pdf_b64
                }).execute()
                logger.info(f"Documento subido al atleta ID {beca_id}: {nombre_doc}")
                flash('Documento subido correctamente.', 'success')
            else:
                flash('Error al procesar el archivo PDF.', 'error')
    except Exception as e: 
        logger.error(f"Error al subir documento: {e}", exc_info=True)
        flash(f'Error al subir: {e}', 'error')
    return redirect(url_for('dashboard.editar_beca', beca_id=beca_id))

@dashboard_blueprint.route('/documentos/eliminar/<int:doc_id>', methods=['POST'])
@login_required
def eliminar_documento(doc_id):
    atleta_id = request.form.get('atleta_id')
    try:
        supabase.table('documentos').delete().eq('id', doc_id).execute()
        logger.info(f"Documento eliminado: ID {doc_id}")
        flash('Documento eliminado.', 'success')
    except Exception as e:
        logger.error(f"Error al eliminar documento: {e}", exc_info=True)
        flash('Error al eliminar.', 'error')
    return redirect(url_for('dashboard.editar_beca', beca_id=atleta_id))

# --- GESTIÓN DE USUARIOS (SOLO SUPERADMIN) ---
@dashboard_blueprint.route('/usuarios')
@login_required
@superadmin_required
def lista_usuarios():
    try:
        usuarios = supabase.table('profiles').select('*').order('email').execute().data
        return render_template('dashboard_usuarios.html', usuarios=usuarios)
    except Exception as e:
        logger.error(f"Error al cargar usuarios: {e}", exc_info=True)
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
            supabase.table('profiles').update({'role': role}).eq('id', uid).execute()
            flash('Rol actualizado correctamente.', 'success')
    except Exception as e:
        logger.error(f"Error al cambiar rol: {e}", exc_info=True)
        flash('Error al actualizar rol.', 'error')
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
            try:
                supabase.auth.admin.delete_user(uid)
                logger.info(f"Usuario {uid} eliminado de Auth.")
                flash('Usuario eliminado del sistema correctamente.', 'success')
            except Exception as auth_error:
                logger.error(f"Error al eliminar de Auth (posible falta de permisos): {auth_error}")
                supabase.table('profiles').delete().eq('id', uid).execute()
                flash('Usuario eliminado de la base de datos (posiblemente siga en Auth).', 'warning')

    except Exception as e:
        logger.error(f"Error al eliminar usuario: {e}", exc_info=True)
        flash('Error al eliminar usuario.', 'error')
    return redirect(url_for('dashboard.lista_usuarios'))