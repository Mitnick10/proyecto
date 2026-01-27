
function confirmarGuardar(form, tipoAccion = 'guardar') {
    // Prevenir envío inmediato
    event.preventDefault();

    const mensajes = {
        'guardar': {
            title: '¿Guardar Cambios?',
            text: 'Se actualizarán todos los datos del atleta',
            icon: 'question',
            confirmText: 'Sí, Guardar',
            cancelText: 'Cancelar',
            successTitle: '¡Guardado!',
            successText: 'Los cambios han sido guardados correctamente'
        },
        'crear': {
            title: '¿Registrar Atleta?',
            text: 'Se creará un nuevo registro en el sistema',
            icon: 'question',
            confirmText: 'Sí, Registrar',
            cancelText: 'Cancelar',
            successTitle: '¡Registrado!',
            successText: 'El atleta ha sido registrado exitosamente'
        },
        'medalla': {
            title: '¿Agregar Medalla?',
            text: 'Se añadirá este logro al perfil del atleta',
            icon: 'success',
            confirmText: 'Sí, Agregar',
            cancelText: 'Cancelar',
            successTitle: '¡Agregada!',
            successText: 'La medalla ha sido agregada'
        },
        'documento': {
            title: '¿Subir Documento?',
            text: 'El archivo PDF será almacenado en el sistema',
            icon: 'info',
            confirmText: 'Sí, Subir',
            cancelText: 'Cancelar',
            successTitle: '¡Subido!',
            successText: 'El documento ha sido almacenado'
        }
    };

    const config = mensajes[tipoAccion] || mensajes['guardar'];

    // Mostrar confirmación con SweetAlert2
    Swal.fire({
        title: config.title,
        text: config.text,
        icon: config.icon,
        showCancelButton: true,
        confirmButtonColor: '#3b82f6',
        cancelButtonColor: '#6b7280',
        confirmButtonText: config.confirmText,
        cancelButtonText: config.cancelText,
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Enviar el formulario
            form.submit();
        }
    });
}

// ====================================
// CONFIRMAR ELIMINAR
// ====================================
function confirmarEliminar(event, tipo = 'atleta', nombre = '') {
    // Prevenir envío inmediato del formulario
    event.preventDefault();

    const mensajes = {
        'atleta': {
            title: '⚠️ ¿Eliminar Atleta?',
            text: nombre ? `Se eliminará toda la información de: ${nombre}` : 'Se eliminará toda la información del atleta',
            warning: 'Esta acción NO se puede deshacer.',
            confirmText: 'Sí, Eliminar',
            cancelText: 'Cancelar',
            successTitle: '¡Eliminado!',
            successText: 'El atleta ha sido eliminado'
        },
        'medalla': {
            title: '¿Eliminar Medalla?',
            text: 'Se quitará este logro del perfil',
            warning: 'Esta acción es permanente.',
            confirmText: 'Sí, Eliminar',
            cancelText: 'Cancelar',
            successTitle: '¡Eliminada!',
            successText: 'La medalla ha sido eliminada'
        },
        'documento': {
            title: '¿Eliminar Documento?',
            text: 'El archivo PDF será eliminado permanentemente',
            warning: 'No podrás recuperar este archivo.',
            confirmText: 'Sí, Eliminar',
            cancelText: 'Cancelar',
            successTitle: '¡Eliminado!',
            successText: 'El documento ha sido eliminado'
        },
        'foto': {
            title: '¿Eliminar Foto?',
            text: 'La foto será eliminada de la galería',
            warning: 'Esta acción es permanente.',
            confirmText: 'Sí, Eliminar',
            cancelText: 'Cancelar',
            successTitle: '¡Eliminada!',
            successText: 'La foto ha sido eliminada'
        }
    };

    const config = mensajes[tipo] || mensajes['atleta'];

    // Guardar referencia al formulario
    const form = event.target;

    // Mostrar alerta de confirmación
    Swal.fire({
        title: config.title,
        html: `<p class="mb-2">${config.text}</p><p class="text-sm text-red-600 font-semibold">${config.warning}</p>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: config.confirmText,
        cancelButtonText: config.cancelText,
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Enviar el formulario después de confirmar
            form.submit();
        }
    });

    // Prevenir envío por defecto
    return false;
}

// ====================================
// MENSAJE DE ÉXITO (después de acción)
// ====================================
function mostrarExito(mensaje, titulo = '¡Éxito!') {
    Swal.fire({
        icon: 'success',
        title: titulo,
        text: mensaje,
        confirmButtonColor: '#3b82f6',
        timer: 2000,
        showConfirmButton: false
    });
}

// ====================================
// MENSAJE DE ERROR
// ====================================
function mostrarError(mensaje, titulo = 'Error') {
    Swal.fire({
        icon: 'error',
        title: titulo,
        text: mensaje,
        confirmButtonColor: '#3b82f6'
    });
}

// ====================================
// AUTO-DETECCIÓN DE FLASH MESSAGES
// ====================================
document.addEventListener('DOMContentLoaded', function () {
    // Interceptar mensajes flash de Flask y mostrarlos con SweetAlert
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        const message = alert.textContent.trim();
        if (alert.classList.contains('alert-success')) {
            mostrarExito(message);
        } else if (alert.classList.contains('alert-error') || alert.classList.contains('alert-danger')) {
            mostrarError(message);
        }
        alert.remove(); // Eliminar el elemento del DOM
    });
});
