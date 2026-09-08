/* ==============================================================================
   DINAMISMO DE FILAS DE HORARIO - ACADEMIA GALENO
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const btnAdd = document.getElementById('btnAddHorario');
    const container = document.getElementById('horariosContainer');

    if (!btnAdd || !container) return;

    btnAdd.addEventListener('click', () => {
        const row = document.createElement('div');
        row.className = 'horario-row';
        row.innerHTML = `
            <select name="horario_dia[]" required>
                <option value="1">Lunes</option>
                <option value="2">Martes</option>
                <option value="3">Miércoles</option>
                <option value="4">Jueves</option>
                <option value="5">Viernes</option>
                <option value="6">Sábado</option>
            </select>
            <input type="time" name="horario_inicio[]" required>
            <input type="time" name="horario_fin[]" required>
            <input type="text" name="horario_aula[]" placeholder="Aula (ej: Lab 02, Virtual)">
            <button type="button" class="btn-remove-horario" title="Eliminar">&times;</button>
        `;

        row.querySelector('.btn-remove-horario').addEventListener('click', () => {
            row.remove();
        });

        container.appendChild(row);
    });

    // Delegación para filas ya existentes
    container.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-remove-horario')) {
            e.target.closest('.horario-row').remove();
        }
    });
});