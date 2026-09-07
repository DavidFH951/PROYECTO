// ==============================================================================
// MODAL DE DETALLE DE EVALUACIONES Y NOTAS (ESTUDIANTE)
// ==============================================================================

function abrirModalNotas(nombreCurso) {
    const titulo = document.getElementById('modalCursoTitulo');
    const modal = document.getElementById('modalNotas');

    if (titulo) {
        titulo.innerText = 'Evaluaciones: ' + (nombreCurso || 'Curso');
    }
    if (modal) {
        modal.style.display = 'flex';
    }
}

function cerrarModalNotas() {
    const modal = document.getElementById('modalNotas');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Cerrar modal automáticamente si se hace clic fuera del recuadro blanco
window.addEventListener('click', function (e) {
    const modal = document.getElementById('modalNotas');
    if (modal && e.target === modal) {
        modal.style.display = 'none';
    }
});