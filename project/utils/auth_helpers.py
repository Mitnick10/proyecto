"""
Funciones helper para autenticación.
Consolida lógica repetida de autenticación, gestión de sesiones y perfiles.
"""

import logging
from flask import session
from config.supabase_client import supabase

logger = logging.getLogger(__name__)


def get_user_role(user_id: str) -> str:
    """
    Obtiene el rol de un usuario desde la tabla profiles.
    
    Args:
        user_id: ID del usuario en Supabase Auth
        
    Returns:
        str: Rol del usuario ('admin', 'superadmin', 'usuario'). 
             Retorna 'usuario' por defecto si no se encuentra.
    """
    try:
        profile_response = supabase.table('profiles').select('role').eq('id', user_id).single().execute()
        
        if profile_response.data:
            user_role = profile_response.data.get('role', 'usuario')
            logger.info(f"✅ Rol encontrado: {user_role} para user_id: {user_id}")
            return user_role
        else:
            logger.warning(f"⚠️ No se encontró rol para user_id: {user_id}, asignando 'usuario' por defecto")
            return 'usuario'
            
    except Exception as e:
        logger.error(f"Error al obtener rol para user_id {user_id}: {e}", exc_info=True)
        return 'usuario'


def create_user_session(auth_response, user_role: str, email: str = None):
    """
    Crea la sesión de Flask con todos los datos del usuario.
    
    Args:
        auth_response: Respuesta de autenticación de Supabase con session y user
        user_role: Rol del usuario
        email: Email del usuario (opcional, se extrae de auth_response si no se provee)
    """
    from flask import request
    from datetime import datetime
    
    user_id = auth_response.user.id
    email = email or auth_response.user.email
    
    # Habilitar session permanente para que aplique el timeout
    session.permanent = True
    
    session['user_id'] = user_id
    session['access_token'] = auth_response.session.access_token
    session['refresh_token'] = auth_response.session.refresh_token
    session['role'] = user_role
    session['email'] = email
    
    # Metadata de seguridad
    session['login_time'] = datetime.utcnow().isoformat()
    session['ip'] = request.remote_addr
    
    logger.info(f"💾 Sesión creada - user_id: {user_id}, role: {user_role}, email: {email}")


def get_or_create_profile(user_id: str, email: str, user_metadata: dict = None) -> str:
    """
    Obtiene el perfil existente o crea uno nuevo para usuarios OAuth.
    
    Args:
        user_id: ID del usuario en Supabase Auth
        email: Email del usuario
        user_metadata: Metadata del usuario (para OAuth, contiene nombre completo, etc.)
        
    Returns:
        str: Rol del usuario
    """
    try:
        # Intentar obtener perfil existente
        profile_response = supabase.table('profiles').select('role').eq('id', user_id).single().execute()
        
        if profile_response.data:
            # Usuario existente
            user_role = profile_response.data.get('role', 'usuario')
            logger.info(f"👤 Usuario existente encontrado con rol: {user_role}")
            return user_role
        else:
            # Nuevo usuario - crear perfil
            user_role = 'usuario'
            user_metadata = user_metadata or {}
            
            # Extraer nombre del metadata (para OAuth providers como Google)
            full_name = user_metadata.get('full_name', '')
            first_name = user_metadata.get('given_name', '')
            last_name = user_metadata.get('family_name', '')
            
            profile_data = {
                'id': user_id,
                'email': email,
                'role': user_role,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': full_name or f"{first_name} {last_name}".strip()
            }
            
            try:
                supabase.table('profiles').insert(profile_data).execute()
                logger.info(f"✨ Nuevo perfil creado para {email} con rol {user_role}")
            except Exception as profile_error:
                logger.warning(f"Error al crear perfil (puede que ya exista): {profile_error}")
            
            return user_role
            
    except Exception as e:
        logger.error(f"Error al obtener/crear perfil para {email}: {e}", exc_info=True)
        return 'usuario'
