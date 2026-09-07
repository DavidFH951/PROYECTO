/* ==============================================================================
   INTERACTIVIDAD PLANILLA DE NOTAS - ACADEMIA GALENO
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const btnToggle = document.getElementById('btnToggleEdicion');
    const inputsNotas = document.querySelectorAll('.input-nota');
    let enEdicion = true;

    if (btnToggle) {
        btnToggle.addEventListener('click', () => {
            enEdicion = !enEdicion;

            inputsNotas.forEach(input => {
                input.readOnly = !enEdicion;
                if (!enEdicion) {
                    input.classList.add('locked');
                } else {
                    input.classList.remove('locked');
                }
            });

            btnToggle.innerHTML = enEdicion 
                ? '🔒 Bloquear Casillas' 
                : '✏️ Habilitar Edición de Notas';
        });
    }
});