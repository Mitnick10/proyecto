/**
 * Sistema de Alertas Modernas y Elegantes
 * Reemplaza alert() y confirm() nativos
 */

// Iconos para cada tipo de alerta
const ALERT_ICONS = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
    question: '?'
};

/**
 * Muestra una alerta moderna
 * @param {Object} options - Configuración de la alerta
 * @returns {Promise} Resuelve con true/false según la acción del usuario
 */
function showCustomAlert(options) {
    return new Promise((resolve) => {
        const {
            title = '¡Atención!',
            message = '',
            type = 'info', // success, error, warning, info, question
            confirmText = 'Aceptar',
            cancelText = 'Cancelar',
            showCancel = false
        } = options;

        // Crear overlay
        const overlay = document.createElement('div');
        overlay.className = 'custom-alert-overlay';

        // Crear modal
        const modal = document.createElement('div');
        modal.className = 'custom-alert-modal';

        // Header con icono
        const header = document.createElement('div');
        header.className = `custom-alert-header ${type}`;
        header.innerHTML = `
            <div class="custom-alert-icon pulse">
                ${ALERT_ICONS[type] || ALERT_ICONS.info}
            </div>
            <h2 class="custom-alert-title">${title}</h2>
        `;

        // Body con mensaje
        const body = document.createElement('div');
        body.className = 'custom-alert-body';
        body.innerHTML = `
            <p class="custom-alert-message">${message}</p>
        `;

        // Footer con botones
        const footer = document.createElement('div');
        footer.className = 'custom-alert-footer';

        // Botón principal (Aceptar/OK)
        const btnPrimary = document.createElement('button');
        btnPrimary.className = `custom-alert-btn custom-alert-btn-primary ${type}`;
        btnPrimary.textContent = confirmText;
        btnPrimary.onclick = () => closeAlert(overlay, modal, true, resolve);

        footer.appendChild(btnPrimary);

        // Botón secundario (Cancelar) - solo si showCancel es true
        if (showCancel) {
            const btnSecondary = document.createElement('button');
            btnSecondary.className = 'custom-alert-btn custom-alert-btn-secondary';
            btnSecondary.textContent = cancelText;
            btnSecondary.onclick = () => closeAlert(overlay, modal, false, resolve);
            footer.appendChild(btnSecondary);
        }

        // Ensamblar modal
        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);
        overlay.appendChild(modal);

        // Agregar al DOM
        document.body.appendChild(overlay);

        // Focus en botón principal
        setTimeout(() => btnPrimary.focus(), 100);

        // Cerrar con ESC
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closeAlert(overlay, modal, false, resolve);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // Cerrar al hacer click fuera del modal
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeAlert(overlay, modal, false, resolve);
            }
        });
    });
}

/**
 * Cierra la alerta con animación
 */
function closeAlert(overlay, modal, result, resolve) {
    overlay.classList.add('hiding');
    modal.classList.add('hiding');

    setTimeout(() => {
        overlay.remove();
        resolve(result);
    }, 200);
}

/**
 * FUNCIONES HELPER - Usan showCustomAlert internamente
 */

// Confirmación (pregunta con Sí/No)
async function confirmAlert(message, title = '¿Confirmas esta acción?') {
    return await showCustomAlert({
        title: title,
        message: message,
        type: 'question',
        confirmText: 'Sí, Continuar',
        cancelText: 'Cancelar',
        showCancel: true
    });
}

// Alerta de éxito
async function successAlert(message, title = '¡Éxito!') {
    return await showCustomAlert({
        title: title,
        message: message,
        type: 'success',
        confirmText: 'Entendido',
        showCancel: false
    });
}

// Alerta de error
async function errorAlert(message, title = 'Error') {
    return await showCustomAlert({
        title: title,
        message: message,
        type: 'error',
        confirmText: 'Entendido',
        showCancel: false
    });
}

// Alerta de advertencia
async function warningAlert(message, title = '¡Advertencia!') {
    return await showCustomAlert({
        title: title,
        message: message,
        type: 'warning',
        confirmText: 'Entendido',
        showCancel: false
    });
}

// Alerta informativa
async function infoAlert(message, title = 'Información') {
    return await showCustomAlert({
        title: title,
        message: message,
        type: 'info',
        confirmText: 'Entendido',
        showCancel: false
    });
}

/**
 * FUNCIONES ESPECÍFICAS PARA EL PROYECTO
 */

// Confirmar guardar
async function confirmarGuardar(tipoAccion = 'guardar') {
    event.preventDefault();

    const mensajes = {
        'guardar': {
            title: '¿Guardar Cambios?',
            message: 'Se actualizarán todos los datos del atleta.\n\n¿Deseas continuar?'
        },
        'crear': {
            title: '¿Registrar Nuevo Atleta?',
            message: 'Se creará un nuevo registro en el sistema.\n\n¿Deseas continuar?'
        },
        'medalla': {
            title: '¿Agregar Medalla?',
            message: 'Se añadirá este logro al perfil del atleta.\n\n¿Continuar?'
        },
        'documento': {
            title: '¿Subir Documento?',
            message: 'El archivo PDF será almacenado en el sistema.\n\n¿Continuar?'
        }
    };

    const config = mensajes[tipoAccion] || mensajes['guardar'];

    const resultado = await showCustomAlert({
        title: config.title,
        message: config.message,
        type: 'question',
        confirmText: '✓ Sí, Continuar',
        cancelText: '✕ Cancelar',
        showCancel: true
    });

    if (resultado) {
        event.target.closest('form').submit();
    }
}

// Confirmar eliminar
async function confirmarEliminar(tipo = 'atleta', nombre = '') {
    event.preventDefault();

    const mensajes = {
        'atleta': {
            title: '⚠️ ¿Eliminar Atleta?',
            message: nombre ?
                `Se eliminará toda la información de:\n${nombre}\n\nEsta acción NO se puede deshacer.\n\n¿Estás completamente seguro?` :
                'Se eliminará toda la información de este atleta.\n\nEsta acción NO se puede deshacer.\n\n¿Estás completamente seguro?'
        },
        'medalla': {
            title: '¿Eliminar Medalla?',
            message: 'Se quitará este logro del perfil del atleta.\n\n¿Continuar?'
        },
        'documento': {
            title: '¿Eliminar Documento?',
            message: 'El archivo PDF será eliminado permanentemente.\n\n¿Continuar?'
        },
        'usuario': {
            title: '¿Eliminar Usuario?',
            message: nombre ?
                `Se eliminará el acceso al sistema para:\n${nombre}\n\n¿Estás seguro?` :
                'Se eliminará este usuario permanentemente.\n\n¿Estás seguro?'
        }
    };

    const config = mensajes[tipo] || mensajes['atleta'];

    const resultado = await showCustomAlert({
        title: config.title,
        message: config.message,
        type: 'error',
        confirmText: '🗑️ Sí, Eliminar',
        cancelText: 'Cancelar',
        showCancel: true
    });

    if (resultado) {
        event.target.closest('form').submit();
    }
}

// Mensaje de éxito después de guardar
function mostrarExito(mensaje = 'Operación completada con éxito') {
    successAlert(mensaje, '¡Perfecto!');
}

// Mensaje de error
function mostrarError(mensaje = 'Ha ocurrido un error') {
    errorAlert(mensaje, 'Error');
}

/**
 * REEMPLAZO GLOBAL DE confirm()
 * Descomenta si quieres que TODOS los confirm() usen el diseño nuevo
 */
/*
window.confirm = async function(message) {
    return await confirmAlert(message);
};
*/
