// ============================================
// SISTEMA DE CONFIRMACIONES ELEGANTES
// ============================================

// Crear el HTML del modal de confirmación
function crearModalConfirmacion() {
    if (document.getElementById('modalConfirmacion')) return;

    const modal = document.createElement('div');
    modal.id = 'modalConfirmacion';
    modal.className = 'fixed inset-0 z-[9999] hidden';
    modal.innerHTML = `
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"></div>
        <div class="fixed inset-0 flex items-center justify-center p-4">
            <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full transform transition-all scale-95 modal-content">
                <div class="p-6">
                    <div class="flex items-center justify-center w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-red-100 to-red-200">
                        <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 text-center mb-2" id="modalTitulo">Confirmar acción</h3>
                    <p class="text-gray-600 text-center mb-6" id="modalMensaje"></p>
                    <div class="flex gap-3">
                        <button id="btnCancelar" class="flex-1 px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors">
                            Cancelar
                        </button>
                        <button id="btnConfirmar" class="flex-1 px-4 py-2.5 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-medium rounded-lg shadow-lg shadow-red-500/30 transition-all">
                            Confirmar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Mostrar modal de confirmación
function mostrarModal(mensaje, titulo = 'Confirmar acción') {
    return new Promise((resolve) => {
        crearModalConfirmacion();
        const modal = document.getElementById('modalConfirmacion');
        const modalMensaje = document.getElementById('modalMensaje');
        const modalTitulo = document.getElementById('modalTitulo');
        const btnConfirmar = document.getElementById('btnConfirmar');
        const btnCancelar = document.getElementById('btnCancelar');

        modalTitulo.textContent = titulo;
        modalMensaje.textContent = mensaje;

        modal.classList.remove('hidden');
        setTimeout(() => {
            modal.querySelector('.modal-content').classList.remove('scale-95');
            modal.querySelector('.modal-content').classList.add('scale-100');
        }, 10);

        function cerrarModal(resultado) {
            modal.querySelector('.modal-content').classList.add('scale-95');
            setTimeout(() => {
                modal.classList.add('hidden');
                resolve(resultado);
            }, 200);
        }

        btnConfirmar.onclick = () => cerrarModal(true);
        btnCancelar.onclick = () => cerrarModal(false);
        modal.querySelector('.fixed.inset-0.bg-black').onclick = () => cerrarModal(false);
    });
}

// Funciones globales de confirmación
async function confirmarEliminar(tipo, nombre) {
    let mensaje = nombre
        ? `¿Estás seguro de que deseas eliminar ${tipo}: ${nombre}?`
        : `¿Estás seguro de que deseas eliminar este ${tipo}?`;

    return await mostrarModal(mensaje, '⚠️ Confirmar eliminación');
}

async function confirmarGuardar(tipo) {
    let mensaje = tipo === 'crear'
        ? '¿Confirmas que deseas crear este nuevo registro?'
        : '¿Confirmas que deseas guardar los cambios?';

    return await mostrarModal(mensaje, '💾 Confirmar guardado');
}

// Auto-dismiss de notificaciones
document.addEventListener('DOMContentLoaded', function () {
    const notifications = document.querySelectorAll('div[style*="slideInRight"]');
    notifications.forEach((notif, index) => {
        setTimeout(() => {
            notif.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notif.remove(), 300);
        }, 5000 + (index * 500));
    });
});

// Interceptar formularios con confirmación
document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('form[onsubmit*="confirmar"]');
    forms.forEach(form => {
        const originalOnsubmit = form.getAttribute('onsubmit');
        form.removeAttribute('onsubmit');

        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            // Extraer parámetros
            let confirmResult = false;
            if (originalOnsubmit.includes('confirmarEliminar')) {
                const match = originalOnsubmit.match(/confirmarEliminar\('([^']+)'(?:,\s*'([^']+)')?\)/);
                if (match) {
                    confirmResult = await confirmarEliminar(match[1], match[2]);
                }
            } else if (originalOnsubmit.includes('confirmarGuardar')) {
                const match = originalOnsubmit.match(/confirmarGuardar\('([^']+)'\)/);
                if (match) {
                    confirmResult = await confirmarGuardar(match[1]);
                }
            }

            if (confirmResult) {
                form.submit();
            }
        });
    });
});
