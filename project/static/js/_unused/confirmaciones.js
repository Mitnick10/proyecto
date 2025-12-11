/**
 * Sistema de Alertas y Confirmaciones Mejoradas
 * 
 * Funciones para mostrar alertas bonitas en:
 * - Guardar
 * - Edit

ar
 * - Eliminar
 */

// ====================================
// CONFIRMAR GUARDAR
// ====================================
function confirmarGuardar(form, tipoAccion = 'guardar') {
    // Prevenir envío inmediato
    event.preventDefault();
    
    const mensajes = {
        'guardar': {
            title: '¿Guardar Cambios?',
            text: 'Se actualizarán todos los datos del atleta',
            icon: 'question',
            confirmText: 'Sí, Guardar',
            cancelText: 'Cancelar'
        },
        'crear': {
            title: '¿Registrar Atleta?',
            text: 'Se creará un nuevo registro en el sistema',
            icon: 'question',
            confirmText: 'Sí, Registrar',
            cancelText: 'Cancelar'
        },
        'medalla': {
            title: '¿Agregar Medalla?',
            text: 'Se añadirá este logro al perfil del atleta',
            icon: 'success',
            confirmText: 'Sí, Agregar',
            cancelText: 'Cancelar'
        },
        'documento': {
            title: '¿Subir Documento?',
            text: 'El archivo PDF será almacenado en el sistema',
            icon: 'info',
            confirmText: 'Sí, Subir',
            cancelText: 'Cancelar'
        }
    };
    
    const config = mensajes[tipoAccion] || mensajes['guardar'];
    
    // Mostrar confirmación bonita
    if (confirm(`${config.title}\n\n${config.text}\n\n¿Continuar?`)) {
        form.submit();
    }
}

// ====================================
// CONFIRMAR ELIMINAR
// ====================================
function confirmarEliminar(tipo = 'atleta', nombre = '') {
    const mensajes = {
        'atleta': {
            title: '⚠️ ¿Eliminar Atleta?',
            text: `Se eliminará toda la información de: ${nombre}\n\nEsta acción NO se puede deshacer.`,
            confirmText: 'Sí, Eliminar',
            cancelText: 'Cancelar'
        },
        'medalla': {
            title: '¿Eliminar Medalla?',
            text: 'Se quitará este logro del perfil',
            confirmText: 'Eliminar',
            cancelText: 'Cancelar'
        },
        'documento': {
            title: '¿Eliminar Documento?',
            text: 'El archivo PDF será eliminado permanentemente',
            confirmText: 'Eliminar',
            cancelText: 'Cancelar'
        }
    };
    
    const config = mensajes[tipo] || mensajes['atleta'];
    
    // Mostrar alerta de confirmación
    const respuesta = confirm(`${config.title}\n\n${config.text}\n\n¿Estás completamente seguro?`);
    
    return respuesta;
}

// ====================================
// MENSAJE DE ÉXITO
// ====================================
function mostrarExito(mensaje) {
    alert(`✅ ${mensaje}`);
}

// ====================================
// MENSAJE DE ERROR
// ====================================
function mostrarError(mensaje) {
    alert(`❌ ${mensaje}`);
}

// ====================================
// AUTO-CONFIRMACIÓN PARA FORMULARIOS
// ====================================
document.addEventListener('DOMContentLoaded', function() {
    // Interceptar todos los formularios de eliminación
    const formsEliminar = document.querySelectorAll('form[action*="eliminar"]');
    formsEliminar.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Si ya tiene onsubmit con confirm, dejarlo pasar
            if (this.getAttribute('onsubmit')) {
                return true;
            }
            
            e.preventDefault();
            
            // Determinar tipo según la URL
            let tipo = 'atleta';
            if (form.action.includes('medalla')) tipo = 'medalla';
            else if (form.action.includes('documento')) tipo = 'documento';
            
            if (confirmarEliminar(tipo)) {
                form.submit();
            }
        });
    });
});

// ====================================
// ALERTAS MEJORADAS CON ICONOS
// ====================================
function alertaConIcono(mensaje, icono = 'info') {
    const iconos = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'question': '❓'
    };
    
    const emojiIcono = iconos[icono] || iconos['info'];
    alert(`${emojiIcono} ${mensaje}`);
}
