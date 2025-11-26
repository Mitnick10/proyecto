import base64
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from supabase_client import supabase
from decorators import login_required, superadmin_required

# Definimos el Blueprint
dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='templates')

# --- HELPER PARA FOTOS (IMÁGENES) ---
def procesar_imagen(file):
    """Convierte la imagen subida a Base64 para guardarla en la BD."""
    if not file or not file.filename:
        return None
    try:
        # Leemos los bytes de la imagen
        file_data = file.read()
        # Convertimos a base64
        encoded_image = base64.b64encode(file_data).decode('utf-8')
        # Creamos el string completo (Data URI)
        mime_type = file.content_type or 'image/jpeg'
        return f"data:{mime_type};base64,{encoded_image}"
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return None

# --- HELPER PARA PDFS (DOCUMENTOS) ---
def procesar_pdf(file):
    """Convierte el PDF a Base64 para guardarlo en la BD."""
    if not file or not file.filename:
        return None
    try:
        file_data = file.read()
        encoded_pdf = base64.b64encode(file_data).decode('utf-8')
        # Forzamos el tipo application/pdf
        return f"data:application/pdf;base64,{encoded_pdf}"
    except Exception as e:
        print(f"Error procesando PDF: {e}")
        return None

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

# --- CONTEXT PROCESSOR ---
@dashboard_blueprint.context_processor
def inject_role():
    """Inyecta el rol del usuario en todas las plantillas."""
    return dict(user_role=session.get('role', 'usuario'))

# --- RUTA HOME (INICIO) ---
@dashboard_blueprint.route('/')
@login_required
def index():
    """Página de INICIO (Home) con contadores."""
    try:
        user = supabase.auth.get_user().user
        first_name = user.user_metadata.get('first_name', 'Usuario')

        # 1. Contar atletas ACTIVOS
        atletas = supabase.table('becas').select('id', count='exact').eq('estatus', 'Activo').execute().count or 0
        
        # 2. Contar atletas EN REVISIÓN
        revision = supabase.table('becas').select('id', count='exact').eq('estatus', 'En Revisión').execute().count or 0
        
        # 3. Contar TOTAL DE MEDALLAS
        try:
            medallas = supabase.table('medallas').select('id', count='exact').execute().count or 0
        except: 
            medallas = 0 # Si la tabla no existe aún
        
        return render_template('dashboard_home.html', 
                               first_name=first_name, 
                               atletas_count=atletas, 
                               revision_count=revision, 
                               medallas_count=medallas)
    except Exception as e:
        print(f"Error cargando dashboard: {e}")
        session.clear()
        return redirect(url_for('login'))

# --- RUTA LISTADO DE ATLETAS ---
@dashboard_blueprint.route('/becas')
@login_required
def lista_becas():
    """Lista de becas con filtro por disciplina."""
    filtro = request.args.get('disciplina')
    try:
        query = supabase.table('becas').select('*')
        if filtro and filtro != 'Todas':
            query = query.eq('disciplina', filtro)
        
        becas = query.execute().data
        
        # Obtener lista única de disciplinas para el dropdown de filtro
        all_d = supabase.table('becas').select('disciplina').execute()
        lista_d = sorted(list(set(i['disciplina'] for i in all_d.data if i.get('disciplina'))))
        
        return render_template('dashboard_becas.html', becas=becas, disciplinas=lista_d, current_filter=filtro)
    except Exception as e:
        flash(f'Error al cargar listado: {e}', 'error')
        return render_template('dashboard_becas.html', becas=[], disciplinas=[])

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
            # 1. Recolectar todos los datos del formulario usando el helper
            datos = obtener_datos_formulario(request)
            
            # 2. Procesar Foto
            foto_b64 = procesar_imagen(request.files.get('foto'))
            if foto_b64:
                datos['foto'] = foto_b64
            
            # 3. Insertar en BD
            supabase.table('becas').insert(datos).execute()
            flash('Atleta registrado exitosamente.', 'success')
            return redirect(url_for('dashboard.lista_becas'))
        except Exception as e: 
            print(f"Error crear_beca: {e}")
            flash(f'Error al registrar: {e}', 'error')
    return render_template('crear_beca.html')

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
        except: documentos = []

        return render_template('ver_beca.html', beca=beca, medallas=medallas, documentos=documentos)
    except Exception as e: 
        flash(f'Error al cargar ficha: {e}', 'error')
        return redirect(url_for('dashboard.lista_becas'))

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
            foto_b64 = procesar_imagen(request.files.get('foto'))
            if foto_b64:
                datos['foto'] = foto_b64
            
            supabase.table('becas').update(datos).eq('id', beca_id).execute()
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
        except: documentos = []
        
        return render_template('editar_beca.html', beca=beca, medallas=medallas, documentos=documentos)
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
            pdf_b64 = procesar_pdf(archivo)
            if pdf_b64:
                supabase.table('documentos').insert({
                    'atleta_id': beca_id,
                    'nombre': nombre_doc,
                    'archivo': pdf_b64
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
        usuarios = supabase.table('profiles').select('*').order('email').execute().data
        return render_template('dashboard_usuarios.html', usuarios=usuarios)
    except: return redirect(url_for('dashboard.index'))

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
            flash('Rol actualizado.', 'success')
    except: flash('Error al cambiar rol.', 'error')
    return redirect(url_for('dashboard.lista_usuarios'))