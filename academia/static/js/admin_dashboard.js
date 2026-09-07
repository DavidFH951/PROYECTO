// ==============================================================================
// GESTIÓN DEL PANEL DE ADMINISTRACIÓN (USUARIOS, MODALES Y CHECKBOXES)
// ==============================================================================

// Seleccionar/Deseleccionar todos los checkboxes de la tabla
function toggleAll(source) {
    const checkboxes = document.querySelectorAll('.user-check');
    checkboxes.forEach(function (cb) {
        cb.checked = source.checked;
    });
}

// Control del modal de Temporadas / Ciclos
function abrirModalTemporadas() {
    const modal = document.getElementById('modalTemporadas');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function cerrarModalTemporadas() {
    const modal = document.getElementById('modalTemporadas');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Cerrar modal automáticamente si se hace clic en el fondo oscuro
window.addEventListener('click', function (event) {
    const modal = document.getElementById('modalTemporadas');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }
});