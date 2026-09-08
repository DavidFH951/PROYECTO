// ==============================================================================
// GESTIÓN DE MATRICULACIÓN DE ALUMNOS (SELECCIÓN Y BÚSQUEDA REACTIVA)
// ==============================================================================

document.addEventListener('DOMContentLoaded', function () {
    // Seleccionar/Deseleccionar todos los checkboxes visibles
    const checkTodos = document.getElementById('checkTodos');
    if (checkTodos) {
        checkTodos.addEventListener('change', function () {
            const checkboxes = document.querySelectorAll('.alumno-checkbox');
            checkboxes.forEach(function (cb) {
                const fila = cb.closest('tr');
                if (fila && fila.style.display !== 'none') {
                    cb.checked = checkTodos.checked;
                }
            });
        });
    }

    // Buscador reactivo en vivo sobre la tabla de alumnos
    const inputFiltro = document.getElementById('filtroAlumno');
    if (inputFiltro) {
        inputFiltro.addEventListener('input', function () {
            const texto = this.value.toLowerCase();
            const filas = document.querySelectorAll('.alumno-fila');

            filas.forEach(function (fila) {
                const contenido = fila.textContent.toLowerCase();
                fila.style.display = contenido.includes(texto) ? '' : 'none';
            });
        });
    }
});