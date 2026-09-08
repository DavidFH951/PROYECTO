// ==============================================================================
// GESTIÓN DINÁMICA DE CRITERIOS DE EVALUACIÓN (EDITAR CURSO)
// ==============================================================================

function actualizarIndicesCriterios() {
    const filas = document.querySelectorAll('#contenedor-criterios .criterio-fila');
    filas.forEach((fila, index) => {
        const span = fila.querySelector('.badge-codigo');
        if (span) {
            span.textContent = `N${index + 1}`;
        }
    });
}

function agregarCriterio() {
    const contenedor = document.getElementById('contenedor-criterios');
    if (!contenedor) return;

    const total = contenedor.querySelectorAll('.criterio-fila').length + 1;

    const div = document.createElement('div');
    div.className = 'criterio-fila';
    div.style = 'display: flex; gap: 10px; align-items: center;';
    div.innerHTML = `
        <span class="badge-codigo" style="background: #e2e8f0; font-weight: 700; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #334155; min-width: 32px; text-align: center;">N${total}</span>
        <input type="text" name="criterio_nombre" required class="input-form" placeholder="Nombre de la evaluación (ej: Pasito N${total})">
        <button type="button" onclick="eliminarCriterio(this)" style="background: #fee2e2; border: none; color: #dc2626; border-radius: 6px; padding: 10px 14px; cursor: pointer; font-size: 14px;" title="Eliminar criterio">🗑️</button>
    `;
    contenedor.appendChild(div);
}

function eliminarCriterio(btn) {
    const contenedor = document.getElementById('contenedor-criterios');
    if (!contenedor) return;

    const filas = contenedor.querySelectorAll('.criterio-fila');
    if (filas.length <= 1) {
        alert("El curso debe tener al menos un criterio de evaluación.");
        return;
    }
    btn.closest('.criterio-fila').remove();
    actualizarIndicesCriterios();
}